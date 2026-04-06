#!/usr/bin/env python3
"""
TOEFL Study Progress Tracker
Reads and updates progress.json, displays stats and charts.

Usage:
    python progress.py --action show --target ./toefl-prep/
    python progress.py --action log --target ./toefl-prep/ --minutes 30 --section reading --score 4.0
    python progress.py --action today --target ./toefl-prep/
    python progress.py --action weekly --target ./toefl-prep/
    python progress.py --action mock --target ./toefl-prep/ --reading 4.5 --listening 5.0 --speaking 4.0 --writing 4.5
"""

import argparse
import json
import os
import sys
from datetime import datetime, date
from pathlib import Path


def load_progress(target: str) -> dict:
    path = os.path.join(target, "progress.json")
    if not os.path.exists(path):
        print(f"❌ 找不到 progress.json：{path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_progress(target: str, data: dict):
    path = os.path.join(target, "progress.json")
    data["last_updated"] = datetime.now().isoformat()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_config(target: str) -> dict:
    path = os.path.join(target, "config.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def show_progress(target: str):
    """Display overall progress summary."""
    prog = load_progress(target)
    config = load_config(target)

    print("=" * 50)
    print("📊 TOEFL 備考進度總覽")
    print("=" * 50)
    print(f"🎯 目標分數：{config.get('target_score', '未設定')}")
    print(f"📅 考試日期：{config.get('exam_date', '未設定')}")
    print(f"🔥 連續天數：{prog.get('streak_days', 0)} 天")
    print(f"⏱️ 累計學習：{prog.get('total_study_minutes', 0)} 分鐘")
    print()

    if config.get("exam_date"):
        try:
            exam = datetime.strptime(config["exam_date"], "%Y-%m-%d").date()
            days_left = (exam - date.today()).days
            print(f"⏳ 距離考試：{days_left} 天")
        except ValueError:
            pass

    # Scores
    print("\n📈 分數追蹤")
    print("-" * 40)
    baseline = prog.get("baseline_scores", {})
    latest = prog.get("latest_scores", {})

    sections = ["reading", "listening", "speaking", "writing"]
    print(f"{'科目':<12} {'基線':<8} {'最新':<8} {'變化':<8}")
    for sec in sections:
        b = baseline.get(sec)
        l = latest.get(sec)
        b_str = f"{b:.1f}" if b else "—"
        l_str = f"{l:.1f}" if l else "—"
        if b and l:
            diff = l - b
            d_str = f"{diff:+.1f}"
        else:
            d_str = "—"
        print(f"{sec.capitalize():<12} {b_str:<8} {l_str:<8} {d_str:<8}")

    b_total = baseline.get("total")
    l_total = latest.get("total")
    print(f"{'Total':<12} {f'{b_total:.1f}' if b_total else '—':<8} {f'{l_total:.1f}' if l_total else '—':<8}")

    # Mock tests
    mocks = prog.get("mock_tests", [])
    if mocks:
        print(f"\n📝 模擬考次數：{len(mocks)}")
        for i, m in enumerate(mocks[-3:], 1):  # Show last 3
            print(f"  #{len(mocks) - 3 + i}: {m.get('date', '?')} — 總分 {m.get('total', '?')}")

    # Weekly completion
    print("\n📅 每週完成度")
    print("-" * 40)
    weekly = prog.get("weekly_completion", {})
    for week_key in sorted(weekly.keys()):
        w = weekly[week_key]
        completed = w.get("completed", 0)
        total = w.get("total", 6)
        bar = "█" * completed + "░" * (total - completed)
        print(f"  {week_key}: [{bar}] {completed}/{total}")

    # Vocabulary
    vocab = prog.get("vocabulary", {})
    if vocab.get("total_learned", 0) > 0:
        print(f"\n📚 單字：已學 {vocab['total_learned']} / 已複習 {vocab.get('total_reviewed', 0)}")


def log_daily(target: str, minutes: int, section: str = None, score: float = None):
    """Log a daily study session."""
    prog = load_progress(target)
    config = load_config(target)

    today_str = date.today().isoformat()
    log_entry = {
        "date": today_str,
        "minutes": minutes,
        "section": section,
        "score": score,
    }

    prog["daily_log"].append(log_entry)
    prog["total_study_minutes"] = prog.get("total_study_minutes", 0) + minutes

    # Update streak
    logs = prog.get("daily_log", [])
    dates = sorted(set(l["date"] for l in logs))
    if dates:
        streak = 1
        for i in range(len(dates) - 1, 0, -1):
            d1 = datetime.strptime(dates[i], "%Y-%m-%d").date()
            d2 = datetime.strptime(dates[i - 1], "%Y-%m-%d").date()
            if (d1 - d2).days == 1:
                streak += 1
            else:
                break
        prog["streak_days"] = streak
        prog["longest_streak"] = max(prog.get("longest_streak", 0), streak)

    # Update latest score if provided
    if section and score:
        prog["latest_scores"][section] = score
        scores = [v for v in prog["latest_scores"].values() if v and isinstance(v, (int, float)) and v != prog["latest_scores"].get("total")]
        if len(scores) == 4:
            prog["latest_scores"]["total"] = round(sum(scores) / 4 * 2) / 2  # Round to nearest 0.5

    # Update weekly completion
    current_week = config.get("current_week", 1)
    week_key = f"week-{current_week:02d}"
    if week_key in prog.get("weekly_completion", {}):
        # Count unique days this week
        week_dates = set()
        for l in logs:
            week_dates.add(l["date"])
        prog["weekly_completion"][week_key]["completed"] = min(len(week_dates), 6)

    save_progress(target, prog)
    print(f"✅ 已記錄：{minutes} 分鐘" + (f"（{section}: {score}）" if section and score else ""))


def log_mock_test(target: str, reading: float, listening: float, speaking: float, writing: float):
    """Log a mock test result."""
    prog = load_progress(target)

    total = round((reading + listening + speaking + writing) / 4 * 2) / 2
    mock_entry = {
        "date": date.today().isoformat(),
        "reading": reading,
        "listening": listening,
        "speaking": speaking,
        "writing": writing,
        "total": total,
    }
    prog["mock_tests"].append(mock_entry)

    # Update latest scores
    prog["latest_scores"] = {
        "reading": reading,
        "listening": listening,
        "speaking": speaking,
        "writing": writing,
        "total": total,
    }

    # Set baseline if first mock
    if len(prog["mock_tests"]) == 1:
        prog["baseline_scores"] = prog["latest_scores"].copy()

    save_progress(target, prog)
    print(f"✅ 模擬考已記錄：R={reading} L={listening} S={speaking} W={writing} → 總分 {total}")


def show_today(target: str):
    """Show what to practice today."""
    config = load_config(target)
    prog = load_progress(target)

    week = config.get("current_week", 1)
    day = config.get("current_day", 1)
    minutes = config.get("daily_minutes", 30)

    print(f"📅 今天：第 {week} 週 Day {day}")
    print(f"⏱️ 預計時間：{minutes} 分鐘")
    print()

    task_path = os.path.join(target, "plan", f"week-{week:02d}", "daily", f"day-{day}.md")
    if os.path.exists(task_path):
        with open(task_path, "r", encoding="utf-8") as f:
            print(f.read())
    else:
        print(f"找不到任務檔案：{task_path}")
        print("請執行 scaffold.py 重新產生計畫")


def main():
    parser = argparse.ArgumentParser(description="TOEFL Study Progress Tracker")
    parser.add_argument("--action", choices=["show", "log", "today", "mock"], default="show")
    parser.add_argument("--target", default="./toefl-prep/", help="Path to toefl-prep directory")
    parser.add_argument("--minutes", type=int, default=30, help="Minutes studied")
    parser.add_argument("--section", choices=["reading", "listening", "speaking", "writing"])
    parser.add_argument("--score", type=float, help="Score for the section (1.0-6.0)")
    parser.add_argument("--reading", type=float)
    parser.add_argument("--listening", type=float)
    parser.add_argument("--speaking", type=float)
    parser.add_argument("--writing", type=float)
    args = parser.parse_args()

    if args.action == "show":
        show_progress(args.target)
    elif args.action == "log":
        log_daily(args.target, args.minutes, args.section, args.score)
    elif args.action == "today":
        show_today(args.target)
    elif args.action == "mock":
        if all([args.reading, args.listening, args.speaking, args.writing]):
            log_mock_test(args.target, args.reading, args.listening, args.speaking, args.writing)
        else:
            print("❌ 模擬考需提供四科分數：--reading --listening --speaking --writing")


if __name__ == "__main__":
    main()
