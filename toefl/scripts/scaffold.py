#!/usr/bin/env python3
"""
TOEFL iBT 2026 Study Environment Scaffold
Generates the complete folder structure and initial files for a 12-week study plan.

Usage:
    python scaffold.py --target ./my-toefl-prep
    python scaffold.py --target . --weeks 8 --daily-minutes 60 --target-score 5.0 --exam-date 2026-07-15
"""

import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path


def create_config(target: Path, args):
    """Create the configuration file."""
    config = {
        "created": datetime.now().isoformat(),
        "target_score": args.target_score,
        "exam_date": args.exam_date or "",
        "daily_minutes": args.daily_minutes,
        "total_weeks": args.weeks,
        "current_week": 1,
        "current_day": 1,
        "language": "zh-TW",
        "tts_voice": "en-US-AriaNeural",
        "tts_engine": "edge-tts",
        "anki_new_cards_per_day": 20,
    }
    with open(target / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def create_progress(target: Path, weeks: int):
    """Create the progress tracking file."""
    progress = {
        "last_updated": datetime.now().isoformat(),
        "total_study_minutes": 0,
        "streak_days": 0,
        "longest_streak": 0,
        "baseline_scores": {
            "reading": None,
            "listening": None,
            "speaking": None,
            "writing": None,
            "total": None,
        },
        "latest_scores": {
            "reading": None,
            "listening": None,
            "speaking": None,
            "writing": None,
            "total": None,
        },
        "mock_tests": [],
        "weekly_completion": {f"week-{i:02d}": {"completed": 0, "total": 6} for i in range(1, weeks + 1)},
        "vocabulary": {
            "total_learned": 0,
            "total_reviewed": 0,
            "words_due_today": 0,
        },
        "daily_log": [],
    }
    with open(target / "progress.json", "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2, ensure_ascii=False)


# ── Phase definitions ──────────────────────────────────────────────

PHASES = {
    "foundation": {
        "name": "基礎期",
        "weeks": (1, 4),
        "focus": "熟悉題型、建立每日習慣、累積基礎字彙",
    },
    "intensive": {
        "name": "強化期",
        "weeks": (5, 8),
        "focus": "弱項加強、計時練習、提升準確度",
    },
    "sprint": {
        "name": "衝刺期",
        "weeks": (9, 12),
        "focus": "模擬考、穩定輸出、考前調整",
    },
}


DAILY_TEMPLATES = {
    "reading": "## 閱讀練習\n\n- [ ] Complete the Words：5 題\n- [ ] Read in Daily Life：2 篇\n- [ ] Academic Passage：1 篇\n\n### 筆記區\n\n",
    "listening": "## 聽力練習\n\n- [ ] Choose a Response：5 題\n- [ ] Conversation：1 段\n- [ ] Announcement：1 段\n- [ ] 筆記練習：記錄關鍵詞\n\n### 筆記區\n\n",
    "speaking": "## 口說練習\n\n- [ ] Listen & Repeat：跟讀 7 句（shadowing 15 分鐘）\n- [ ] Interview：即興回答 2 題（各 45 秒）\n- [ ] 錄音並回聽\n\n### 自我評估\n\n| 維度 | 自評 (1-5) | 備註 |\n|------|-----------|------|\n| Fluency | | |\n| Intelligibility | | |\n| Language Use | | |\n| Organization | | |\n\n",
    "writing": "## 寫作練習\n\n- [ ] Build a Sentence：10 題\n- [ ] Write an Email 或 Academic Discussion（擇一）\n\n### 草稿區\n\n\n### Claude 批改結果\n\n（完成後請 Claude 批改）\n",
    "vocabulary": "## 單字複習\n\n- [ ] Anki 複習（舊卡）\n- [ ] 學習 20 個新單字\n- [ ] 用新單字造句 5 句\n\n### 今日新單字\n\n| 單字 | 詞性 | 定義 | 例句 |\n|------|------|------|------|\n| | | | |\n\n",
    "review": "## 週末複習\n\n- [ ] Anki 全部複習\n- [ ] 重做本週錯題\n- [ ] 更新進度追蹤\n- [ ] 檢查本週目標完成度\n\n### 本週反思\n\n**做得好的：**\n\n**需要改進的：**\n\n**下週重點：**\n\n",
}


# Each day maps to focus areas (R=reading, L=listening, S=speaking, W=writing, V=vocab)
WEEKLY_ROTATION = [
    ["vocabulary", "reading"],       # Day 1
    ["vocabulary", "listening"],     # Day 2
    ["vocabulary", "speaking"],      # Day 3
    ["vocabulary", "writing"],       # Day 4
    ["vocabulary", "reading", "listening"],  # Day 5
    ["vocabulary", "speaking", "writing"],   # Day 6
]


def get_phase(week: int, total_weeks: int) -> str:
    """Determine which phase a week belongs to."""
    third = total_weeks / 3
    if week <= third:
        return "foundation"
    elif week <= 2 * third:
        return "intensive"
    else:
        return "sprint"


def create_weekly_goals(week: int, total_weeks: int) -> str:
    """Generate goals markdown for a specific week."""
    phase = get_phase(week, total_weeks)
    phase_info = PHASES[phase]

    goals = f"# 第 {week} 週 — {phase_info['name']}\n\n"
    goals += f"**階段重點：** {phase_info['focus']}\n\n"
    goals += "## 本週目標\n\n"

    if phase == "foundation":
        if week == 1:
            goals += "- [ ] 完成診斷模擬考，記錄基線分數\n"
            goals += "- [ ] 熟悉所有新制題型\n"
            goals += "- [ ] 建立每日 Anki 習慣\n"
            goals += "- [ ] 累積 30 個新單字\n"
        elif week == 2:
            goals += "- [ ] 閱讀三種題型各練習 10 題以上\n"
            goals += "- [ ] 累積 100 個新單字（含拼寫）\n"
            goals += "- [ ] Complete the Words 正確率 ≥ 60%\n"
        elif week == 3:
            goals += "- [ ] 聽力四種題型各練習 5 題以上\n"
            goals += "- [ ] Listen & Repeat 嘗試完整複述 7 句\n"
            goals += "- [ ] 聽懂 2 分鐘學術短文的主旨\n"
        else:
            goals += "- [ ] Build a Sentence 正確率 ≥ 70%\n"
            goals += "- [ ] 完成一篇 Email + 一篇 Discussion\n"
            goals += "- [ ] 完成第二次模擬考\n"

    elif phase == "intensive":
        if week == 5:
            goals += "- [ ] Module 1 模擬正確率 ≥ 70%\n"
            goals += "- [ ] 限時練習閱讀和聽力\n"
        elif week == 6:
            goals += "- [ ] 每天 shadowing 15 分鐘\n"
            goals += "- [ ] Interview 能穩定說滿 40 秒\n"
        elif week == 7:
            goals += "- [ ] Email 和 Discussion 計時完成\n"
            goals += "- [ ] Build a Sentence 正確率 ≥ 90%\n"
        else:
            goals += "- [ ] 完成第三次模擬考\n"
            goals += "- [ ] 分數達到目標 -0.5 以內\n"

    else:  # sprint
        if week == 9:
            goals += "- [ ] 完成 2 次完整模擬考\n"
            goals += "- [ ] 嚴格計時\n"
        elif week == 10:
            goals += "- [ ] 分析所有模擬考的錯誤模式\n"
            goals += "- [ ] 針對弱項專項練習\n"
        elif week == 11:
            goals += "- [ ] 最後一次完整模擬考\n"
            goals += "- [ ] 分數穩定在目標範圍\n"
        else:
            goals += "- [ ] 輕量練習，保持手感\n"
            goals += "- [ ] 確認考試流程和文件\n"
            goals += "- [ ] 調整作息\n"

    goals += "\n## 本週完成度\n\n"
    goals += "| 日 | 完成 | 備註 |\n|---|------|------|\n"
    for d in range(1, 7):
        goals += f"| Day {d} | [ ] | |\n"
    goals += "| Review | [ ] | |\n"

    return goals


def create_daily_task(week: int, day: int, total_weeks: int, daily_minutes: int) -> str:
    """Generate a daily task markdown file."""
    phase = get_phase(week, total_weeks)
    focus_areas = WEEKLY_ROTATION[day - 1] if day <= 6 else ["review"]

    content = f"# 第 {week} 週・Day {day}\n\n"
    content += f"**日期：** ____年____月____日\n"
    content += f"**預計時間：** {daily_minutes} 分鐘\n"
    content += f"**今日重點：** {' + '.join(a.capitalize() for a in focus_areas)}\n\n"
    content += "---\n\n"

    if day == 7:
        content += DAILY_TEMPLATES["review"]
    else:
        for area in focus_areas:
            content += DAILY_TEMPLATES.get(area, "")
            content += "\n---\n\n"

    content += "## 今日完成度\n\n"
    content += "- [ ] 完成所有練習\n"
    content += f"- [ ] 實際花費時間：____ 分鐘\n"
    content += "- [ ] 更新 progress.json\n"

    return content


def create_readme(target: Path, args):
    """Create the main README."""
    readme = """# 🎯 TOEFL iBT 2026 備考計畫

## Quick Start

1. 每天打開這個資料夾
2. 啟動 Claude Code
3. 告訴 Claude：「今天練什麼？」

## 常用指令

| 指令 | 說明 |
|------|------|
| `今天練什麼？` | 查看今日任務 |
| `幫我做口說練習` | 產生口說題目 + 評估 |
| `批改我的寫作` | 提交寫作草稿讓 Claude 批改 |
| `產生聽力練習` | 用 TTS 產生聽力音檔 |
| `產生 Anki 單字卡` | 產生本週的 Anki deck |
| `模擬考` | 開始一次完整模擬考 |
| `看進度` | 顯示學習進度和統計 |
| `弱項分析` | 分析各科弱項並給建議 |

## 目標

| 項目 | 設定 |
|------|------|
| 目標分數 | {target_score} |
| 考試日期 | {exam_date} |
| 每日時間 | {daily_minutes} 分鐘 |
| 總週數 | {weeks} 週 |

## 資料夾說明

- `plan/` — 每週計畫和每日任務
- `vocabulary/` — 單字表和 Anki deck
- `reading/` — 閱讀練習
- `listening/` — 聽力練習（含 TTS 音檔）
- `speaking/` — 口說練習和回饋
- `writing/` — 寫作練習和批改
- `mock-tests/` — 模擬考

## 工具安裝

```bash
pip install edge-tts genanki
```
""".format(
        target_score=args.target_score,
        exam_date=args.exam_date or "未設定",
        daily_minutes=args.daily_minutes,
        weeks=args.weeks,
    )
    with open(target / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)


def scaffold(args):
    """Main scaffold function."""
    target = Path(args.target).resolve()
    prep_dir = target / "toefl-prep"
    prep_dir.mkdir(parents=True, exist_ok=True)

    # Create top-level files
    create_config(prep_dir, args)
    create_progress(prep_dir, args.weeks)
    create_readme(prep_dir, args)

    # Create directory structure
    dirs = [
        "plan",
        "vocabulary/word-lists",
        "vocabulary/anki-decks",
        "reading/passages",
        "reading/exercises",
        "listening/audio",
        "listening/transcripts",
        "listening/exercises",
        "speaking/prompts",
        "speaking/recordings",
        "speaking/feedback",
        "writing/prompts",
        "writing/drafts",
        "writing/feedback",
        "mock-tests",
    ]
    for d in dirs:
        (prep_dir / d).mkdir(parents=True, exist_ok=True)

    # Create plan overview
    overview = "# 12 週備考計畫總覽\n\n"
    for phase_key, phase in PHASES.items():
        w1, w2 = phase["weeks"]
        overview += f"## {phase['name']}（第 {w1}–{w2} 週）\n"
        overview += f"**重點：** {phase['focus']}\n\n"
    with open(prep_dir / "plan" / "overview.md", "w", encoding="utf-8") as f:
        f.write(overview)

    # Create weekly plans
    for week in range(1, args.weeks + 1):
        week_dir = prep_dir / "plan" / f"week-{week:02d}"
        daily_dir = week_dir / "daily"
        daily_dir.mkdir(parents=True, exist_ok=True)

        # Weekly goals
        goals = create_weekly_goals(week, args.weeks)
        with open(week_dir / "goals.md", "w", encoding="utf-8") as f:
            f.write(goals)

        # Daily tasks
        for day in range(1, 7):
            task = create_daily_task(week, day, args.weeks, args.daily_minutes)
            with open(daily_dir / f"day-{day}.md", "w", encoding="utf-8") as f:
                f.write(task)

        # Review day
        review = create_daily_task(week, 7, args.weeks, args.daily_minutes)
        with open(daily_dir / "review-day.md", "w", encoding="utf-8") as f:
            f.write(review)

    print(f"✅ TOEFL 備考環境已建立：{prep_dir}")
    print(f"   📅 {args.weeks} 週計畫")
    print(f"   ⏱️ 每日 {args.daily_minutes} 分鐘")
    print(f"   🎯 目標分數 {args.target_score}")
    print(f"\n下一步：進入 {prep_dir} 資料夾，告訴 Claude「今天練什麼？」")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TOEFL iBT 2026 Study Environment Scaffold")
    parser.add_argument("--target", default=".", help="Target directory (default: current)")
    parser.add_argument("--weeks", type=int, default=12, help="Total study weeks (default: 12)")
    parser.add_argument("--daily-minutes", type=int, default=30, help="Daily study minutes (default: 30)")
    parser.add_argument("--target-score", type=float, default=5.0, help="Target score 1.0-6.0 (default: 5.0)")
    parser.add_argument("--exam-date", type=str, default="", help="Exam date YYYY-MM-DD")
    args = parser.parse_args()
    scaffold(args)
