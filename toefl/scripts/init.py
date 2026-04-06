#!/usr/bin/env python3
"""
TOEFL 備考系統 — 初始化模組 (init.py)
首次使用時的引導精靈：問卷、診斷、個人化計畫產生。

Usage:
    python init.py --target ./my-study-folder
    python init.py --target . --non-interactive --target-score 5.0 --exam-date 2026-07-15 --daily-minutes 30 --weeks 12

此模組會：
1. 詢問使用者的基本資訊（目標分數、考試日期、每日可用時間、英語程度自評）
2. 產生個人化的 config.json
3. 呼叫 scaffold.py 產生完整資料夾結構
4. 產生一份簡易診斷測驗（diagnostic quiz）供使用者完成
5. 輸出「接下來怎麼做」的引導說明
"""

import argparse
import json
import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path


def interactive_onboarding() -> dict:
    """Interactive questionnaire for first-time setup."""
    print("=" * 55)
    print("🎯 TOEFL iBT 2026 備考系統 — 初始化精靈")
    print("=" * 55)
    print()

    # Target score
    print("📊 你的目標分數是多少？（新制 1.0–6.0）")
    print("   參考：5.0+ 頂尖大學 / 4.0–4.5 一般大學 / 3.5 基本門檻")
    while True:
        try:
            target_score = float(input("   目標分數 [5.0]: ").strip() or "5.0")
            if 1.0 <= target_score <= 6.0:
                break
            print("   ❌ 請輸入 1.0 到 6.0 之間的數字")
        except ValueError:
            print("   ❌ 請輸入數字")

    # Exam date
    print("\n📅 你的考試日期是？（格式：YYYY-MM-DD，不確定可跳過）")
    exam_date = input("   考試日期 [留空]: ").strip()
    if exam_date:
        try:
            exam_dt = datetime.strptime(exam_date, "%Y-%m-%d").date()
            days_left = (exam_dt - date.today()).days
            if days_left <= 0:
                print("   ⚠️ 這個日期已過，將設為未定")
                exam_date = ""
            else:
                weeks_available = days_left // 7
                print(f"   ✅ 距離考試 {days_left} 天（約 {weeks_available} 週）")
        except ValueError:
            print("   ⚠️ 日期格式不正確，將設為未定")
            exam_date = ""

    # Daily time
    print("\n⏱️ 你每天可以花多少時間準備？")
    print("   1) 15 分鐘（零碎時間）")
    print("   2) 30 分鐘（推薦最低）")
    print("   3) 45 分鐘")
    print("   4) 60 分鐘（密集備考）")
    print("   5) 自訂")
    choice = input("   選擇 [2]: ").strip() or "2"
    time_map = {"1": 15, "2": 30, "3": 45, "4": 60}
    if choice in time_map:
        daily_minutes = time_map[choice]
    else:
        try:
            daily_minutes = int(input("   請輸入分鐘數: ").strip())
        except ValueError:
            daily_minutes = 30

    # Self-assessment
    print("\n📝 你目前的英語程度自評：")
    print("   1) 初級 — 日常對話有困難")
    print("   2) 中級 — 能進行基本對話，閱讀簡單文章")
    print("   3) 中高級 — 能閱讀學術文章，聽懂大部分演講")
    print("   4) 高級 — 接近流利，偶有文法或詞彙不足")
    print("   5) 不確定（建議做診斷測驗）")
    level_choice = input("   選擇 [5]: ").strip() or "5"
    level_map = {"1": "beginner", "2": "intermediate", "3": "upper-intermediate", "4": "advanced", "5": "unknown"}
    self_level = level_map.get(level_choice, "unknown")

    # Weak areas
    print("\n🔍 你覺得自己最弱的是哪一科？（可多選，用逗號分隔）")
    print("   R=閱讀  L=聽力  S=口說  W=寫作  ?=不確定")
    weak_input = input("   最弱科目 [?]: ").strip().upper() or "?"
    weak_map = {"R": "reading", "L": "listening", "S": "speaking", "W": "writing", "?": "unknown"}
    weak_areas = [weak_map.get(w.strip(), "unknown") for w in weak_input.split(",")]

    # Study weeks
    if exam_date:
        weeks = min(max(weeks_available, 4), 16)
        print(f"\n📅 根據考試日期，建議 {weeks} 週計畫")
    else:
        print("\n📅 你想要幾週的計畫？")
        print("   建議：8 週（短期衝刺）/ 12 週（標準）/ 16 週（充裕）")
        try:
            weeks = int(input("   週數 [12]: ").strip() or "12")
            weeks = min(max(weeks, 4), 24)
        except ValueError:
            weeks = 12

    # TTS preference
    print("\n🔊 聽力練習的 TTS 引擎：")
    print("   1) edge-tts（需網路，品質好，免費）← 推薦")
    print("   2) Kokoro（離線，需下載模型約 200MB）")
    tts_choice = input("   選擇 [1]: ").strip() or "1"
    tts_engine = "edge-tts" if tts_choice == "1" else "kokoro"

    return {
        "target_score": target_score,
        "exam_date": exam_date,
        "daily_minutes": daily_minutes,
        "weeks": weeks,
        "self_level": self_level,
        "weak_areas": weak_areas,
        "tts_engine": tts_engine,
    }


def generate_config(target: Path, params: dict):
    """Generate personalized config.json."""
    config = {
        "version": "1.0.0",
        "created": datetime.now().isoformat(),
        "target_score": params["target_score"],
        "exam_date": params.get("exam_date", ""),
        "daily_minutes": params["daily_minutes"],
        "total_weeks": params["weeks"],
        "current_week": 1,
        "current_day": 1,
        "self_level": params.get("self_level", "unknown"),
        "weak_areas": params.get("weak_areas", ["unknown"]),
        "language": "zh-TW",
        "tts_engine": params.get("tts_engine", "edge-tts"),
        "tts_voice": "en-US-AriaNeural",
        "anki_new_cards_per_day": 20,
        "initialized": True,
        "diagnostic_completed": False,
        "phase_schedule": {
            "foundation": {"start": 1, "end": max(1, params["weeks"] // 3)},
            "intensive": {"start": max(2, params["weeks"] // 3 + 1), "end": max(3, params["weeks"] * 2 // 3)},
            "sprint": {"start": max(4, params["weeks"] * 2 // 3 + 1), "end": params["weeks"]},
        },
    }
    with open(target / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    return config


def generate_diagnostic(target: Path):
    """Generate a diagnostic quiz for baseline assessment."""
    diagnostic = {
        "title": "TOEFL 2026 診斷測驗",
        "instructions": "這不是正式模擬考，而是快速評估你的起始程度。每科 5 題，約 15-20 分鐘。",
        "sections": {
            "reading": {
                "description": "閱讀理解（5 題）",
                "questions": [
                    {
                        "type": "complete_words",
                        "prompt": "The researcher's hyp_th_sis was supported by the experimental data.",
                        "answer": "hypothesis",
                        "explanation": "hypothesis = 假說。注意 y 和 e 的位置。"
                    },
                    {
                        "type": "complete_words",
                        "prompt": "Environmental sust__n_bility requires both individual and collective action.",
                        "answer": "sustainability",
                        "explanation": "sustainability = 永續性。注意 ai 和 a 的位置。"
                    },
                    {
                        "type": "daily_life",
                        "prompt": "Email: 'Hi Alex, The study group for Biology 101 will meet this Thursday at 3 PM in Room 204 instead of our usual time on Wednesday. Please bring your lab notes. — Sarah'",
                        "question": "What change is Sarah informing Alex about?",
                        "options": ["A. The room number", "B. The meeting day and time", "C. The subject being studied", "D. Who will attend"],
                        "answer": "B",
                    },
                    {
                        "type": "academic",
                        "passage": "Coral reefs, often called the rainforests of the sea, support approximately 25 percent of all marine species despite covering less than one percent of the ocean floor. Rising ocean temperatures cause coral bleaching, a process in which corals expel the algae living in their tissues. Without these algae, corals lose their color and their primary food source.",
                        "question": "What is the main cause of coral bleaching according to the passage?",
                        "options": ["A. Ocean pollution", "B. Overfishing", "C. Rising water temperatures", "D. Reduced sunlight"],
                        "answer": "C",
                    },
                    {
                        "type": "academic",
                        "passage": "Coral reefs, often called the rainforests of the sea, support approximately 25 percent of all marine species despite covering less than one percent of the ocean floor. Rising ocean temperatures cause coral bleaching, a process in which corals expel the algae living in their tissues. Without these algae, corals lose their color and their primary food source.",
                        "question": "The phrase 'rainforests of the sea' is used to emphasize:",
                        "options": ["A. Coral reefs are located near tropical forests", "B. Coral reefs have high biodiversity", "C. Coral reefs are endangered", "D. Coral reefs are very large"],
                        "answer": "B",
                    },
                ],
            },
            "writing": {
                "description": "寫作能力（2 題）",
                "questions": [
                    {
                        "type": "build_a_sentence",
                        "prompt": "Arrange these words into a correct sentence: [wanted / she / which / to / know / I'm / colleges / considering]",
                        "answer": "She wanted to know which colleges I'm considering.",
                    },
                    {
                        "type": "email",
                        "prompt": "You ordered a laptop online, but it arrived with a cracked screen. Write an email to customer service to: (1) Describe the problem, (2) Explain how it affects you, (3) Request a solution.",
                        "time_limit": "7 minutes",
                        "rubric": "See scoring-rubrics.md — Email section",
                    },
                ],
            },
            "speaking": {
                "description": "口說能力（2 題）— 請錄音或打字回答",
                "questions": [
                    {
                        "type": "interview",
                        "prompt": "Think about a teacher who had a significant impact on you. Who was this teacher, and why did they influence you?",
                        "time_limit": "45 seconds",
                    },
                    {
                        "type": "interview",
                        "prompt": "Some people prefer to study alone, while others prefer to study in groups. Which do you prefer, and why?",
                        "time_limit": "45 seconds",
                    },
                ],
            },
        },
    }

    diag_dir = target / "mock-tests" / "diagnostic"
    diag_dir.mkdir(parents=True, exist_ok=True)
    with open(diag_dir / "diagnostic-quiz.json", "w", encoding="utf-8") as f:
        json.dump(diagnostic, f, indent=2, ensure_ascii=False)

    # Also create a human-readable version
    md = "# 🏥 TOEFL 2026 診斷測驗\n\n"
    md += "> 約 15–20 分鐘，用來評估你的起始程度\n\n"
    md += "---\n\n"

    for section_key, section in diagnostic["sections"].items():
        md += f"## {section['description']}\n\n"
        for i, q in enumerate(section["questions"], 1):
            md += f"### 題 {i} ({q['type']})\n\n"
            if q["type"] == "complete_words":
                md += f"填入缺漏的字母：\n\n`{q['prompt']}`\n\n"
                md += f"<details><summary>答案</summary>\n\n{q['answer']}\n\n{q.get('explanation', '')}\n\n</details>\n\n"
            elif q["type"] == "daily_life":
                md += f"{q['prompt']}\n\n**{q['question']}**\n\n"
                for opt in q["options"]:
                    md += f"- {opt}\n"
                md += f"\n<details><summary>答案</summary>{q['answer']}</details>\n\n"
            elif q["type"] == "academic":
                md += f"> {q['passage']}\n\n**{q['question']}**\n\n"
                for opt in q["options"]:
                    md += f"- {opt}\n"
                md += f"\n<details><summary>答案</summary>{q['answer']}</details>\n\n"
            elif q["type"] == "build_a_sentence":
                md += f"{q['prompt']}\n\n"
                md += f"<details><summary>答案</summary>\n\n{q['answer']}\n\n</details>\n\n"
            elif q["type"] == "email":
                md += f"**情境：** {q['prompt']}\n\n"
                md += f"**時間限制：** {q['time_limit']}\n\n"
                md += "（請在下方或 `writing/drafts/diagnostic-email.md` 中作答）\n\n"
            elif q["type"] == "interview":
                md += f"**題目：** {q['prompt']}\n\n"
                md += f"**時間限制：** {q['time_limit']}\n\n"
                md += "（請錄音或在 `speaking/feedback/diagnostic.md` 中打字回答）\n\n"
            md += "---\n\n"

    with open(diag_dir / "diagnostic-quiz.md", "w", encoding="utf-8") as f:
        f.write(md)

    print(f"   📋 診斷測驗已產生：{diag_dir}")


def print_next_steps(target: Path, config: dict):
    """Print onboarding complete message with next steps."""
    print()
    print("=" * 55)
    print("✅ 初始化完成！")
    print("=" * 55)
    print()
    print(f"📂 備考資料夾：{target}")
    print(f"🎯 目標分數：{config['target_score']}")
    print(f"📅 考試日期：{config.get('exam_date') or '未設定'}")
    print(f"⏱️ 每日時間：{config['daily_minutes']} 分鐘")
    print(f"📅 計畫週數：{config['total_weeks']} 週")
    print(f"🔊 TTS 引擎：{config['tts_engine']}")
    print()
    print("📋 接下來的步驟：")
    print()
    print("  1️⃣  完成診斷測驗")
    print(f"     打開 mock-tests/diagnostic/diagnostic-quiz.md")
    print(f"     告訴 Claude：「我完成診斷測驗了，幫我評估」")
    print()
    print("  2️⃣  安裝必要工具")
    print(f"     pip install edge-tts genanki")
    print()
    print("  3️⃣  開始每日練習")
    print(f"     告訴 Claude：「今天練什麼？」")
    print()
    print("  💡 隨時可以說：")
    print("     「幫我做口說練習」")
    print("     「批改我的寫作」")
    print("     「產生本週 Anki 單字卡」")
    print("     「看我的進度」")
    print("     「做模擬考」")
    print()


def main():
    parser = argparse.ArgumentParser(description="TOEFL 備考系統初始化")
    parser.add_argument("--target", default=".", help="Target directory")
    parser.add_argument("--non-interactive", action="store_true", help="Skip interactive prompts")
    parser.add_argument("--target-score", type=float, default=5.0)
    parser.add_argument("--exam-date", type=str, default="")
    parser.add_argument("--daily-minutes", type=int, default=30)
    parser.add_argument("--weeks", type=int, default=12)
    args = parser.parse_args()

    target = Path(args.target).resolve()

    # Check if already initialized
    config_path = target / "toefl-prep" / "config.json"
    if config_path.exists():
        with open(config_path, "r") as f:
            existing = json.load(f)
        if existing.get("initialized"):
            print("⚠️ 此資料夾已經初始化過了。")
            print(f"   config.json 建立於 {existing.get('created', '?')}")
            choice = input("   要重新初始化嗎？(y/N): ").strip().lower()
            if choice != "y":
                print("   取消。")
                return

    # Gather parameters
    if args.non_interactive:
        params = {
            "target_score": args.target_score,
            "exam_date": args.exam_date,
            "daily_minutes": args.daily_minutes,
            "weeks": args.weeks,
            "self_level": "unknown",
            "weak_areas": ["unknown"],
            "tts_engine": "edge-tts",
        }
    else:
        params = interactive_onboarding()

    # Run scaffold
    print("\n🔧 正在建立備考環境...")
    from scaffold import scaffold as run_scaffold

    class ScaffoldArgs:
        pass

    sa = ScaffoldArgs()
    sa.target = str(target)
    sa.weeks = params["weeks"]
    sa.daily_minutes = params["daily_minutes"]
    sa.target_score = params["target_score"]
    sa.exam_date = params.get("exam_date", "")
    run_scaffold(sa)

    prep_dir = target / "toefl-prep"

    # Overwrite config with enriched version
    config = generate_config(prep_dir, params)

    # Generate diagnostic
    print("   📋 正在產生診斷測驗...")
    generate_diagnostic(prep_dir)

    # Print next steps
    print_next_steps(prep_dir, config)


if __name__ == "__main__":
    main()
