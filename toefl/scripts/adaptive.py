#!/usr/bin/env python3
"""
TOEFL 備考系統 — 自適應引擎 (adaptive.py)

根據 progress.json 中的表現數據，動態調整：
1. 每日時間分配（弱科多練、強科維持）
2. 題目難度等級
3. 本週重點科目
4. 里程碑檢查與計畫修正建議
5. 單字複習排程（遺忘曲線加權）

Usage:
    python adaptive.py --target ./toefl-prep/ --action analyze     # 分析現況，輸出調整建議
    python adaptive.py --target ./toefl-prep/ --action rebalance   # 重新分配時間並更新每日計畫
    python adaptive.py --target ./toefl-prep/ --action difficulty  # 輸出各科建議難度等級
    python adaptive.py --target ./toefl-prep/ --action checkpoint  # 里程碑檢查
"""

import argparse
import json
import math
import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import defaultdict

# ── Constants ──────────────────────────────────────────

SECTIONS = ["reading", "listening", "speaking", "writing"]

# 每科最低時間佔比（不會低於此比例）
MIN_TIME_RATIO = 0.10  # 10%
# 弱科加權上限
MAX_TIME_RATIO = 0.45  # 45%

# 難度等級定義
DIFFICULTY_LEVELS = {
    1: {"label": "基礎", "description": "短句、常見詞、慢速", "target_score_range": (1.0, 2.5)},
    2: {"label": "初中級", "description": "中等句長、學術基礎詞", "target_score_range": (2.5, 3.5)},
    3: {"label": "中級", "description": "複雜句、學術進階詞、正常語速", "target_score_range": (3.5, 4.5)},
    4: {"label": "中高級", "description": "長複雜句、低頻詞、快語速", "target_score_range": (4.5, 5.0)},
    5: {"label": "高級", "description": "接近真實考試最高難度", "target_score_range": (5.0, 6.0)},
}

# 里程碑定義（按週數比例）
MILESTONES = {
    0.25: {  # 25% 進度（第3週）
        "name": "基礎檢查點",
        "expected": {
            "diagnostic_completed": True,
            "vocab_learned": 60,
            "mock_tests": 1,
        },
        "checks": ["是否完成診斷測驗", "是否累積 60+ 單字", "是否完成第一次模擬考"],
    },
    0.50: {  # 50% 進度（第6週）
        "name": "中期檢查點",
        "expected": {
            "vocab_learned": 150,
            "mock_tests": 2,
            "min_score_improvement": 0.5,
        },
        "checks": ["模擬考分數是否提升 ≥ 0.5", "弱項是否有改善", "是否維持每日練習"],
    },
    0.75: {  # 75% 進度（第9週）
        "name": "衝刺前檢查點",
        "expected": {
            "vocab_learned": 250,
            "mock_tests": 3,
            "target_gap": 0.5,
        },
        "checks": ["模擬考分數是否在目標 -0.5 以內", "各科是否平衡", "是否需要延長計畫"],
    },
    1.0: {  # 100% 進度（最後一週）
        "name": "考前最終檢查",
        "expected": {
            "mock_tests": 4,
            "target_reached": True,
        },
        "checks": ["是否達到目標分數", "是否有信心穩定發揮", "考試流程是否熟悉"],
    },
}


def load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Core Analysis ──────────────────────────────────────

def compute_section_scores(progress: dict) -> dict:
    """Extract latest score per section, with fallback to mock test data."""
    latest = progress.get("latest_scores", {})
    scores = {}
    for sec in SECTIONS:
        s = latest.get(sec)
        if s is not None:
            scores[sec] = float(s)
    
    # Fallback: average from daily logs
    if len(scores) < 4:
        log_scores = defaultdict(list)
        for entry in progress.get("daily_log", []):
            if entry.get("section") and entry.get("score"):
                log_scores[entry["section"]].append(entry["score"])
        for sec in SECTIONS:
            if sec not in scores and log_scores[sec]:
                scores[sec] = sum(log_scores[sec]) / len(log_scores[sec])

    return scores


def compute_score_trends(progress: dict) -> dict:
    """Compute score trend (improving/declining/stable) per section from mock tests."""
    mocks = progress.get("mock_tests", [])
    trends = {}
    for sec in SECTIONS:
        section_scores = [m.get(sec) for m in mocks if m.get(sec) is not None]
        if len(section_scores) >= 2:
            recent = section_scores[-1]
            previous = section_scores[-2]
            diff = recent - previous
            if diff > 0.3:
                trends[sec] = {"direction": "improving", "delta": diff, "emoji": "📈"}
            elif diff < -0.3:
                trends[sec] = {"direction": "declining", "delta": diff, "emoji": "📉"}
            else:
                trends[sec] = {"direction": "stable", "delta": diff, "emoji": "➡️"}
        else:
            trends[sec] = {"direction": "unknown", "delta": 0, "emoji": "❓"}
    return trends


def compute_weakness_weights(scores: dict, target_score: float) -> dict:
    """
    Calculate how much extra time each section needs.
    Sections further from target get more weight.
    Declining sections get an additional boost.
    """
    if not scores:
        return {sec: 0.25 for sec in SECTIONS}

    gaps = {}
    for sec in SECTIONS:
        current = scores.get(sec, target_score - 1.5)  # assume weak if no data
        gap = max(0, target_score - current)
        gaps[sec] = gap

    total_gap = sum(gaps.values())
    if total_gap == 0:
        return {sec: 0.25 for sec in SECTIONS}

    # Raw weights proportional to gap
    raw_weights = {sec: gaps[sec] / total_gap for sec in SECTIONS}

    # Clamp to [MIN_TIME_RATIO, MAX_TIME_RATIO]
    clamped = {}
    for sec in SECTIONS:
        clamped[sec] = max(MIN_TIME_RATIO, min(MAX_TIME_RATIO, raw_weights[sec]))

    # Normalize to sum to 1.0
    total = sum(clamped.values())
    return {sec: round(clamped[sec] / total, 3) for sec in SECTIONS}


def compute_difficulty_level(score: float) -> int:
    """Map a section score to a recommended difficulty level."""
    if score is None:
        return 2
    for level, info in sorted(DIFFICULTY_LEVELS.items()):
        low, high = info["target_score_range"]
        if score < high:
            return level
    return 5


def compute_daily_plan(weights: dict, daily_minutes: int) -> dict:
    """Convert weights to concrete minute allocation."""
    plan = {}
    remaining = daily_minutes
    allocated = {}

    for sec in SECTIONS:
        minutes = max(5, round(weights[sec] * daily_minutes))  # minimum 5 min
        allocated[sec] = minutes

    # Normalize to fit within daily_minutes
    total = sum(allocated.values())
    if total != daily_minutes:
        diff = daily_minutes - total
        # Add/subtract from the section with highest weight
        top_sec = max(weights, key=weights.get)
        allocated[top_sec] += diff

    return allocated


# ── Main Actions ──────────────────────────────────────

def analyze(target: str):
    """Full analysis: scores, trends, weights, difficulty, recommendations."""
    config = load_json(os.path.join(target, "config.json"))
    progress = load_json(os.path.join(target, "progress.json"))

    target_score = config.get("target_score", 5.0)
    daily_minutes = config.get("daily_minutes", 30)
    current_week = config.get("current_week", 1)
    total_weeks = config.get("total_weeks", 12)

    scores = compute_section_scores(progress)
    trends = compute_score_trends(progress)
    weights = compute_weakness_weights(scores, target_score)
    time_alloc = compute_daily_plan(weights, daily_minutes)

    print("\n🧠 自適應分析報告")
    print("=" * 55)
    print(f"🎯 目標：{target_score}  |  📅 進度：第 {current_week}/{total_weeks} 週 ({current_week/total_weeks*100:.0f}%)")
    print()

    # Section analysis
    print("📊 各科現況")
    print("-" * 55)
    print(f"{'科目':<12} {'分數':<8} {'差距':<8} {'趨勢':<8} {'難度':<10} {'時間分配'}")
    for sec in SECTIONS:
        s = scores.get(sec)
        s_str = f"{s:.1f}" if s else "—"
        gap = f"{target_score - s:+.1f}" if s else "—"
        trend = trends.get(sec, {})
        t_emoji = trend.get("emoji", "❓")
        diff_level = compute_difficulty_level(s)
        diff_label = DIFFICULTY_LEVELS[diff_level]["label"]
        mins = time_alloc[sec]
        pct = weights[sec] * 100

        print(f"{sec.capitalize():<12} {s_str:<8} {gap:<8} {t_emoji:<8} Lv{diff_level} {diff_label:<6} {mins}min ({pct:.0f}%)")

    print()

    # Recommendations
    print("💡 調整建議")
    print("-" * 55)

    if not scores:
        print("  ⚠️ 尚無分數數據。請先完成診斷測驗或模擬考。")
        return

    # Find weakest
    weakest = min(scores, key=scores.get)
    strongest = max(scores, key=scores.get)
    gap_worst = target_score - scores[weakest]
    gap_best = target_score - scores[strongest]

    if gap_worst > 1.5:
        print(f"  🔴 {weakest.capitalize()} 落後目標 {gap_worst:.1f} 分，建議每天至少 {time_alloc[weakest]} 分鐘專項練習")

    if gap_worst > 0.5 and gap_best <= 0:
        print(f"  🟡 {strongest.capitalize()} 已達標，可以減少時間，將資源移到 {weakest.capitalize()}")

    # Trend warnings
    for sec in SECTIONS:
        if trends.get(sec, {}).get("direction") == "declining":
            print(f"  ⚠️ {sec.capitalize()} 分數下降中！建議本週額外加練")

    # Balance check
    score_values = list(scores.values())
    if score_values:
        score_range = max(score_values) - min(score_values)
        if score_range > 1.5:
            print(f"  ⚠️ 各科差距 {score_range:.1f} 分，嚴重不平衡。集中補弱科。")
        elif score_range < 0.5:
            print(f"  ✅ 各科平衡（差距 {score_range:.1f}），可以均衡練習。")

    # Pace check
    progress_ratio = current_week / total_weeks
    avg_score = sum(score_values) / len(score_values) if score_values else 0
    expected_progress = target_score * (0.6 + 0.4 * progress_ratio)  # expect 60% at start, 100% at end
    if avg_score < expected_progress * 0.8:
        print(f"  🏃 進度偏慢。考慮增加每日練習時間或延長計畫。")

    # Output adaptive config
    adaptive_config = {
        "generated": datetime.now().isoformat(),
        "section_weights": weights,
        "time_allocation": time_alloc,
        "difficulty_levels": {sec: compute_difficulty_level(scores.get(sec)) for sec in SECTIONS},
        "trends": {sec: trends.get(sec, {}).get("direction", "unknown") for sec in SECTIONS},
        "weakest_section": weakest,
        "strongest_section": strongest,
    }
    adaptive_path = os.path.join(target, "adaptive.json")
    save_json(adaptive_path, adaptive_config)
    print(f"\n📁 自適應設定已儲存：{adaptive_path}")

    return adaptive_config


def rebalance(target: str):
    """Rewrite upcoming daily plans based on adaptive analysis."""
    config = load_json(os.path.join(target, "config.json"))
    progress = load_json(os.path.join(target, "progress.json"))
    
    target_score = config.get("target_score", 5.0)
    daily_minutes = config.get("daily_minutes", 30)
    current_week = config.get("current_week", 1)
    current_day = config.get("current_day", 1)
    total_weeks = config.get("total_weeks", 12)

    scores = compute_section_scores(progress)
    weights = compute_weakness_weights(scores, target_score)
    time_alloc = compute_daily_plan(weights, daily_minutes)
    
    if not scores:
        print("⚠️ 尚無分數數據，無法重新平衡。請先完成模擬考。")
        return

    # Sort sections by priority (weakest first)
    priority_order = sorted(SECTIONS, key=lambda s: scores.get(s, 0))

    print("\n🔄 重新平衡每日計畫")
    print("=" * 50)
    print(f"基於最新數據，調整第 {current_week} 週 Day {current_day} 起的計畫\n")

    print("📊 新的時間分配：")
    for sec in priority_order:
        mins = time_alloc[sec]
        pct = weights[sec] * 100
        bar_len = int(pct / 5)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        score_str = f"{scores.get(sec, 0):.1f}" if scores.get(sec) else "?"
        print(f"  {sec.capitalize():<12} [{bar}] {mins:>2}min ({pct:.0f}%)  現分：{score_str}")

    # Generate adjusted daily template
    print("\n📋 調整後的每日模板：")
    print("-" * 50)
    
    # Vocabulary is always 5 min
    vocab_time = 5
    remaining = daily_minutes - vocab_time
    
    # Primary focus = weakest section
    # Secondary focus = second weakest
    primary = priority_order[0]
    secondary = priority_order[1]
    primary_time = max(10, round(remaining * weights[primary] / (weights[primary] + weights[secondary] + 0.001) * 1.2))
    secondary_time = remaining - primary_time

    print(f"  📚 單字複習：{vocab_time} 分鐘")
    print(f"  🔴 主練（{primary.capitalize()}）：{primary_time} 分鐘")
    print(f"  🟡 副練（{secondary.capitalize()}）：{secondary_time} 分鐘")
    print(f"  ─── 合計：{daily_minutes} 分鐘")

    # Difficulty recommendations
    print("\n📏 建議題目難度：")
    for sec in SECTIONS:
        level = compute_difficulty_level(scores.get(sec))
        info = DIFFICULTY_LEVELS[level]
        print(f"  {sec.capitalize():<12} → Lv{level} {info['label']}（{info['description']}）")

    # Save to adaptive.json
    adaptive = {
        "generated": datetime.now().isoformat(),
        "section_weights": weights,
        "time_allocation": time_alloc,
        "difficulty_levels": {sec: compute_difficulty_level(scores.get(sec)) for sec in SECTIONS},
        "priority_order": priority_order,
        "daily_template": {
            "vocabulary": vocab_time,
            "primary": {"section": primary, "minutes": primary_time},
            "secondary": {"section": secondary, "minutes": secondary_time},
        },
    }
    save_json(os.path.join(target, "adaptive.json"), adaptive)

    # Update config with adaptive flag
    config["adaptive_enabled"] = True
    config["last_rebalance"] = datetime.now().isoformat()
    save_json(os.path.join(target, "config.json"), config)

    print(f"\n✅ 計畫已重新平衡。下次 daily.py 會使用新設定。")


def show_difficulty(target: str):
    """Show recommended difficulty per section."""
    progress = load_json(os.path.join(target, "progress.json"))
    scores = compute_section_scores(progress)

    print("\n📏 各科建議難度")
    print("=" * 55)
    for sec in SECTIONS:
        s = scores.get(sec)
        level = compute_difficulty_level(s)
        info = DIFFICULTY_LEVELS[level]
        s_str = f"{s:.1f}" if s else "未知"
        print(f"\n  {sec.capitalize()} （現分：{s_str}）")
        print(f"    → Lv{level} {info['label']}")
        print(f"    {info['description']}")
        
        # Specific tips per section per level
        if sec == "reading":
            if level <= 2:
                print(f"    💡 先從 Daily Life 短文開始，再練 Complete the Words")
            elif level <= 3:
                print(f"    💡 加入 Academic Passage，練習推論題")
            else:
                print(f"    💡 限時練習，模擬 Module 1 壓力")
        elif sec == "listening":
            if level <= 2:
                print(f"    💡 先聽慢速（--rate=-20%），逐漸加速")
            elif level <= 3:
                print(f"    💡 正常語速，練習筆記技巧")
            else:
                print(f"    💡 Academic Talks + 推論題，只聽一次")
        elif sec == "speaking":
            if level <= 2:
                print(f"    💡 Repeat 練短句（5 詞以下），Interview 先打字再口說")
            elif level <= 3:
                print(f"    💡 Repeat 練中長句，Interview 計時 45 秒")
            else:
                print(f"    💡 全速跟讀，Interview 不打草稿直接說")
        elif sec == "writing":
            if level <= 2:
                print(f"    💡 Build a Sentence 先練簡單句型")
            elif level <= 3:
                print(f"    💡 Email 計時 7 分鐘，確保涵蓋所有要點")
            else:
                print(f"    💡 計時完成所有題型，追求零文法錯誤")


def checkpoint(target: str):
    """Run milestone checkpoint based on current progress."""
    config = load_json(os.path.join(target, "config.json"))
    progress = load_json(os.path.join(target, "progress.json"))

    current_week = config.get("current_week", 1)
    total_weeks = config.get("total_weeks", 12)
    target_score = config.get("target_score", 5.0)
    progress_ratio = current_week / total_weeks

    scores = compute_section_scores(progress)
    mocks = progress.get("mock_tests", [])
    vocab = progress.get("vocabulary", {})

    print("\n🏁 里程碑檢查")
    print("=" * 55)
    print(f"📅 進度：第 {current_week}/{total_weeks} 週（{progress_ratio*100:.0f}%）")
    print()

    # Find applicable milestone
    applicable = None
    for threshold, milestone in sorted(MILESTONES.items()):
        if progress_ratio >= threshold - 0.05:  # within 5% tolerance
            applicable = (threshold, milestone)

    if not applicable:
        print("  目前尚未到達任何里程碑。繼續加油！")
        return

    threshold, milestone = applicable
    print(f"📌 {milestone['name']}（{threshold*100:.0f}% 進度點）")
    print()

    passed = 0
    total = len(milestone["checks"])

    for check_desc in milestone["checks"]:
        # Evaluate each check
        if "診斷測驗" in check_desc:
            ok = config.get("diagnostic_completed", False)
        elif "單字" in check_desc:
            expected_vocab = milestone["expected"].get("vocab_learned", 0)
            actual_vocab = vocab.get("total_learned", 0)
            ok = actual_vocab >= expected_vocab
            check_desc += f"（{actual_vocab}/{expected_vocab}）"
        elif "模擬考" in check_desc:
            expected_mocks = milestone["expected"].get("mock_tests", 0)
            ok = len(mocks) >= expected_mocks
            check_desc += f"（{len(mocks)}/{expected_mocks}）"
        elif "提升" in check_desc:
            if len(mocks) >= 2:
                improvement = mocks[-1].get("total", 0) - mocks[0].get("total", 0)
                expected_improvement = milestone["expected"].get("min_score_improvement", 0)
                ok = improvement >= expected_improvement
                check_desc += f"（{improvement:+.1f}）"
            else:
                ok = False
        elif "目標" in check_desc and "0.5" in check_desc:
            if scores:
                avg = sum(scores.values()) / len(scores)
                gap = target_score - avg
                ok = gap <= 0.5
                check_desc += f"（差距 {gap:.1f}）"
            else:
                ok = False
        elif "達到目標" in check_desc:
            if scores:
                avg = sum(scores.values()) / len(scores)
                ok = avg >= target_score
            else:
                ok = False
        else:
            ok = None  # Cannot auto-check

        if ok is True:
            print(f"  ✅ {check_desc}")
            passed += 1
        elif ok is False:
            print(f"  ❌ {check_desc}")
        else:
            print(f"  ❓ {check_desc}（需手動確認）")

    print(f"\n  通過：{passed}/{total}")

    if passed < total:
        print("\n  💡 建議：")
        if not config.get("diagnostic_completed"):
            print("    → 儘快完成診斷測驗")
        if len(mocks) < milestone["expected"].get("mock_tests", 0):
            print("    → 安排一次模擬考")
        if scores:
            avg = sum(scores.values()) / len(scores)
            if target_score - avg > 1.0:
                print("    → 考慮增加每日練習時間或延長計畫週數")
    else:
        print("\n  🎉 所有里程碑都通過了！進度良好！")


def main():
    parser = argparse.ArgumentParser(description="TOEFL 自適應引擎")
    parser.add_argument("--target", default="./toefl-prep/")
    parser.add_argument("--action", choices=["analyze", "rebalance", "difficulty", "checkpoint"], default="analyze")
    args = parser.parse_args()

    if args.action == "analyze":
        analyze(args.target)
    elif args.action == "rebalance":
        rebalance(args.target)
    elif args.action == "difficulty":
        show_difficulty(args.target)
    elif args.action == "checkpoint":
        checkpoint(args.target)


if __name__ == "__main__":
    main()
