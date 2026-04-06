#!/usr/bin/env python3
"""
TOEFL 備考系統 — 口說教練模組 (speaking_coach.py)
產生口說題目、Listen & Repeat 跟讀句、Interview 練習題，
並提供 Claude 評估框架。

Usage:
    python speaking_coach.py --type repeat --output ./speaking/ --count 7
    python speaking_coach.py --type interview --output ./speaking/ --topic daily_life
    python speaking_coach.py --type full --output ./speaking/   # 完整一回（7 repeat + 4 interview）
    python speaking_coach.py --type evaluate --input ./speaking/recordings/my-answer.txt

Dependencies:
    pip install edge-tts  (for audio generation)
"""

import argparse
import asyncio
import json
import os
import sys
import random
from datetime import datetime
from pathlib import Path

# ── Listen & Repeat 句庫 ──────────────────────────────────

REPEAT_SENTENCE_BANKS = {
    "campus_tour": {
        "context": "Campus Tour Guide",
        "image_hint": "A map of a university campus",
        "sentences": [
            {"text": "Welcome to the main campus.", "difficulty": 1, "seconds": 8},
            {"text": "The bookstore is on your left.", "difficulty": 1, "seconds": 8},
            {"text": "You can pick up your student ID at the front desk.", "difficulty": 2, "seconds": 10},
            {"text": "The dining hall serves breakfast from seven to nine thirty.", "difficulty": 2, "seconds": 10},
            {"text": "Students with meal plans can eat at any of the three cafeterias on campus.", "difficulty": 3, "seconds": 10},
            {"text": "If you need to print documents, the computer lab on the second floor has color printers available.", "difficulty": 3, "seconds": 12},
            {"text": "The recreation center offers free fitness classes for all registered students throughout the semester.", "difficulty": 4, "seconds": 12},
        ],
    },
    "library": {
        "context": "Library Orientation",
        "image_hint": "Interior of a university library",
        "sentences": [
            {"text": "Please keep your voice down.", "difficulty": 1, "seconds": 8},
            {"text": "Books can be borrowed for two weeks.", "difficulty": 1, "seconds": 8},
            {"text": "The quiet study area is on the fourth floor.", "difficulty": 2, "seconds": 10},
            {"text": "You'll need your student card to reserve a group study room.", "difficulty": 2, "seconds": 10},
            {"text": "Late fees are fifty cents per day for each overdue item.", "difficulty": 3, "seconds": 10},
            {"text": "The library database can be accessed remotely using your university login credentials.", "difficulty": 3, "seconds": 12},
            {"text": "During finals week, the library extends its hours and remains open until two in the morning.", "difficulty": 4, "seconds": 12},
        ],
    },
    "dormitory": {
        "context": "Dormitory Move-in Day",
        "image_hint": "A university dormitory hallway",
        "sentences": [
            {"text": "Your room is on the third floor.", "difficulty": 1, "seconds": 8},
            {"text": "Laundry machines are in the basement.", "difficulty": 1, "seconds": 8},
            {"text": "Please return your key to the front desk when you check out.", "difficulty": 2, "seconds": 10},
            {"text": "Quiet hours begin at ten PM on weeknights and midnight on weekends.", "difficulty": 2, "seconds": 10},
            {"text": "Each floor has a shared kitchen with a microwave, stove, and refrigerator.", "difficulty": 3, "seconds": 10},
            {"text": "Residents are responsible for keeping common areas clean and reporting any maintenance issues.", "difficulty": 3, "seconds": 12},
            {"text": "If your roommate's schedule conflicts with yours, the housing office can help arrange a room transfer.", "difficulty": 4, "seconds": 12},
        ],
    },
    "registration": {
        "context": "Course Registration Office",
        "image_hint": "A student services desk",
        "sentences": [
            {"text": "Registration opens next Monday.", "difficulty": 1, "seconds": 8},
            {"text": "You need at least twelve credits per semester.", "difficulty": 1, "seconds": 8},
            {"text": "Talk to your advisor before dropping any required courses.", "difficulty": 2, "seconds": 10},
            {"text": "The deadline for adding or dropping courses without penalty is September fifteenth.", "difficulty": 2, "seconds": 10},
            {"text": "Students who want to take more than eighteen credits must get approval from their department.", "difficulty": 3, "seconds": 10},
            {"text": "If a course you need is full, you can add yourself to the waitlist and check back regularly.", "difficulty": 3, "seconds": 12},
            {"text": "Prerequisites listed in the course catalog must be completed before you can enroll in advanced level classes.", "difficulty": 4, "seconds": 12},
        ],
    },
}

# ── Interview 題庫 ──────────────────────────────────────

INTERVIEW_TOPICS = {
    "daily_life": {
        "theme": "Daily Routines and Habits",
        "intro": "You have volunteered for a research study about daily life. You will have a short online interview with a researcher.",
        "questions": [
            "What does a typical weekday look like for you? Walk me through your routine.",
            "Is there a habit you've been trying to build or break recently? How's it going?",
            "Do you prefer having a structured schedule or keeping things flexible? Why?",
            "If you could add one extra hour to your day, how would you spend it?",
        ],
    },
    "education": {
        "theme": "Learning and Education",
        "intro": "You have volunteered for a research study about education. You will have a short online interview with a researcher.",
        "questions": [
            "Think about the most effective teacher you've had. What made them stand out?",
            "Do you learn better by reading, listening, or doing things hands-on? Give an example.",
            "Some people think online learning is just as effective as in-person classes. What's your view?",
            "If you could study any subject without worrying about career prospects, what would you choose and why?",
        ],
    },
    "technology": {
        "theme": "Technology in Daily Life",
        "intro": "You have volunteered for a research study about technology use. You will have a short online interview with a researcher.",
        "questions": [
            "How has technology changed the way you communicate with friends and family?",
            "What's one piece of technology you couldn't live without? Why is it so important to you?",
            "Do you think social media has more positive or negative effects on society? Explain your reasoning.",
            "Imagine a day without any electronic devices. How would you spend it?",
        ],
    },
    "environment": {
        "theme": "Environment and Sustainability",
        "intro": "You have volunteered for a research study about environmental awareness. You will have a short online interview with a researcher.",
        "questions": [
            "What's one thing you do in your daily life to help the environment?",
            "Do you think individuals or governments are more responsible for solving environmental problems? Why?",
            "How has your local environment changed over the past few years? Describe what you've noticed.",
            "If you could implement one environmental policy in your city, what would it be?",
        ],
    },
    "work": {
        "theme": "Work and Career",
        "intro": "You have volunteered for a research study about work experiences. You will have a short online interview with a researcher.",
        "questions": [
            "Describe a time when you had to work with someone whose approach was very different from yours.",
            "Do you prefer working independently or as part of a team? Why?",
            "What qualities do you think make a good leader?",
            "How do you think the workplace will change in the next ten years?",
        ],
    },
}

# ── Evaluation templates for Claude ──────────────────────

REPEAT_EVAL_TEMPLATE = """## Listen & Repeat 評估

**原句：** {original}
**學生回答：** {student_answer}

### 評分 (0–5)

| 維度 | 分數 | 說明 |
|------|------|------|
| Repeat Accuracy | /5 | 內容詞完整度、順序正確性 |
| Fluency | /5 | 節奏穩定、無明顯停頓 |
| Intelligibility | /5 | 發音清晰度 |

**總分：** /5

### 分析
- 遺漏的詞：
- 替換的詞：
- 發音需注意：

### 改進建議
1.
2.
"""

INTERVIEW_EVAL_TEMPLATE = """## Interview 回答評估

**題目：** {question}
**學生回答：** {student_answer}
**字數：** {word_count} 字（目標 100-120 字 ≈ 45 秒）

### 評分 (0–5)

| 維度 | 分數 | 說明 |
|------|------|------|
| Fluency | /5 | 語速自然、無明顯停頓 |
| Intelligibility | /5 | 發音清晰 |
| Language Use | /5 | 文法準確、詞彙多樣 |
| Organization | /5 | 邏輯清晰、結構完整 |

**總分：** /5

### 優點

### 需改進

### 文法錯誤
| 原文 | 修正 | 說明 |
|------|------|------|

### 模範回答參考
（提供一個 5 分級別的範例回答）
"""


def generate_repeat_set(output_dir: str, bank_key: str = None, count: int = 7):
    """Generate a Listen & Repeat exercise set."""
    if bank_key and bank_key in REPEAT_SENTENCE_BANKS:
        bank = REPEAT_SENTENCE_BANKS[bank_key]
    else:
        bank_key = random.choice(list(REPEAT_SENTENCE_BANKS.keys()))
        bank = REPEAT_SENTENCE_BANKS[bank_key]

    exercise_dir = os.path.join(output_dir, "prompts", f"repeat-{datetime.now().strftime('%Y%m%d-%H%M')}")
    os.makedirs(exercise_dir, exist_ok=True)

    sentences = bank["sentences"][:count]

    # Create exercise markdown
    md = f"# Listen & Repeat 練習\n\n"
    md += f"**情境：** {bank['context']}\n"
    md += f"**圖片提示：** {bank['image_hint']}\n\n"
    md += "## 練習方式\n\n"
    md += "1. 聽音檔（或請 Claude 唸出句子）\n"
    md += "2. 聽完後立刻複述\n"
    md += "3. 錄音或打字記錄你的回答\n"
    md += "4. 請 Claude 評估\n\n"
    md += "## 句子\n\n"

    for i, s in enumerate(sentences, 1):
        stars = "⭐" * s["difficulty"]
        md += f"### 第 {i} 句 {stars}（{s['seconds']}秒）\n\n"
        md += f"> 🔊 （聽完後在下方記錄你的回答）\n\n"
        md += f"我的回答：________________\n\n"
        md += f"<details><summary>原句（作答後再看）</summary>\n\n{s['text']}\n\n</details>\n\n"

    with open(os.path.join(exercise_dir, "exercise.md"), "w", encoding="utf-8") as f:
        f.write(md)

    # Save answer key as JSON (for programmatic access)
    answer_key = {
        "context": bank["context"],
        "sentences": [{"index": i+1, **s} for i, s in enumerate(sentences)],
    }
    with open(os.path.join(exercise_dir, "answer-key.json"), "w", encoding="utf-8") as f:
        json.dump(answer_key, f, indent=2, ensure_ascii=False)

    print(f"✅ Listen & Repeat 練習已產生：{exercise_dir}")
    print(f"   情境：{bank['context']}（{len(sentences)} 句）")
    return exercise_dir


def generate_interview_set(output_dir: str, topic: str = None):
    """Generate an Interview exercise set."""
    if topic and topic in INTERVIEW_TOPICS:
        topic_data = INTERVIEW_TOPICS[topic]
    else:
        topic = random.choice(list(INTERVIEW_TOPICS.keys()))
        topic_data = INTERVIEW_TOPICS[topic]

    exercise_dir = os.path.join(output_dir, "prompts", f"interview-{datetime.now().strftime('%Y%m%d-%H%M')}")
    os.makedirs(exercise_dir, exist_ok=True)

    md = f"# Take an Interview 練習\n\n"
    md += f"**主題：** {topic_data['theme']}\n\n"
    md += f"**情境：** {topic_data['intro']}\n\n"
    md += "## 練習方式\n\n"
    md += "1. 讀完題目後立刻開始回答（不要準備！）\n"
    md += "2. 每題 45 秒（約 100–120 字）\n"
    md += "3. 用 Idea → Reason → Example 結構\n"
    md += "4. 錄音或打字記錄回答\n"
    md += "5. 請 Claude 評估\n\n"

    for i, q in enumerate(topic_data["questions"], 1):
        md += f"### Question {i}\n\n"
        md += f"🎤 *\"{q}\"*\n\n"
        md += f"⏱️ 45 秒\n\n"
        md += f"**我的回答：**\n\n\n\n---\n\n"

    with open(os.path.join(exercise_dir, "exercise.md"), "w", encoding="utf-8") as f:
        f.write(md)

    # Save questions JSON
    with open(os.path.join(exercise_dir, "questions.json"), "w", encoding="utf-8") as f:
        json.dump(topic_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Interview 練習已產生：{exercise_dir}")
    print(f"   主題：{topic_data['theme']}（4 題）")
    return exercise_dir


def generate_full_set(output_dir: str):
    """Generate a complete speaking practice set (7 repeat + 4 interview)."""
    print("🎤 產生完整口說練習（模擬真實考試）\n")
    r = generate_repeat_set(output_dir)
    print()
    i = generate_interview_set(output_dir)
    print(f"\n📝 完整口說練習已產生！")
    print(f"   先做 Listen & Repeat，再做 Interview")
    return r, i


def print_eval_framework(eval_type: str):
    """Print evaluation template for Claude to use."""
    if eval_type == "repeat":
        print(REPEAT_EVAL_TEMPLATE.format(
            original="[原句]",
            student_answer="[學生回答]"
        ))
    elif eval_type == "interview":
        print(INTERVIEW_EVAL_TEMPLATE.format(
            question="[題目]",
            student_answer="[學生回答]",
            word_count="[字數]"
        ))


def main():
    parser = argparse.ArgumentParser(description="TOEFL 口說教練模組")
    parser.add_argument("--type", choices=["repeat", "interview", "full", "evaluate"], default="full")
    parser.add_argument("--output", default="./speaking/")
    parser.add_argument("--topic", choices=list(INTERVIEW_TOPICS.keys()), help="Interview topic")
    parser.add_argument("--bank", choices=list(REPEAT_SENTENCE_BANKS.keys()), help="Repeat sentence bank")
    parser.add_argument("--count", type=int, default=7, help="Number of repeat sentences")
    parser.add_argument("--eval-type", choices=["repeat", "interview"], help="Print evaluation template")
    args = parser.parse_args()

    if args.type == "repeat":
        generate_repeat_set(args.output, args.bank, args.count)
    elif args.type == "interview":
        generate_interview_set(args.output, args.topic)
    elif args.type == "full":
        generate_full_set(args.output)
    elif args.type == "evaluate":
        print_eval_framework(args.eval_type or "interview")


if __name__ == "__main__":
    main()
