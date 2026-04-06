#!/usr/bin/env python3
"""
TOEFL 2026 Speaking Exercise Generator

Listen & Repeat audio structure (per sentence):
  [0.5s silence] → [sentence audio] → [0.3s silence] → [BEEP] → [recording silence 8-12s]

Interview audio structure (per question):
  [narrator: context intro] → [1s silence]
  [interviewer: question] → [0.5s silence] → [DOUBLE BEEP] → [45s recording silence] → [single beep = stop]

All timing calibrated to match the real 2026 TOEFL test experience.

Usage:
    uv run python scripts/generate_speaking.py --type repeat --output ./speaking/ --set 1
    uv run python scripts/generate_speaking.py --type interview --output ./speaking/ --topic daily-routines
    uv run python scripts/generate_speaking.py --type all --output ./speaking/
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from audio_utils import (
    generate_beep_file, generate_silence_file,
    generate_double_beep_file, concat_audio
)

try:
    import edge_tts
except ImportError:
    print("❌ edge-tts 未安裝。請執行：uv pip install edge-tts")
    sys.exit(1)

VOICES = {
    "narrator":      {"id": "en-US-AriaNeural",  "rate": "-3%"},
    "interviewer_f": {"id": "en-US-SaraNeural",  "rate": "-5%"},
    "interviewer_m": {"id": "en-US-GuyNeural",   "rate": "-5%"},
}

# ── Listen & Repeat Content ──────────────────────────────────
# Each set = 7 sentences, progressive difficulty, realistic campus scenario
# Recording times: items 1-2 = 8s, items 3-5 = 10s, items 6-7 = 12s

REPEAT_SETS = [
    {
        "set_id": 1,
        "scenario": "Campus Dining Hall Tour",
        "image_desc": "A map of a university dining hall showing different food stations.",
        "sentences": [
            {"text": "Welcome to the dining hall.",                                                               "record_ms": 8000,  "difficulty": 1},
            {"text": "The salad bar is on your left.",                                                            "record_ms": 8000,  "difficulty": 1},
            {"text": "Hot meals are served from eleven to two.",                                                  "record_ms": 10000, "difficulty": 2},
            {"text": "You can pay with your student card or cash.",                                               "record_ms": 10000, "difficulty": 2},
            {"text": "If you have any food allergies, please check the labels at each station.",                   "record_ms": 10000, "difficulty": 3},
            {"text": "The recycling bins are located near the exit, and we ask that you sort your waste properly.","record_ms": 12000, "difficulty": 3},
            {"text": "For students with special dietary requirements, a dedicated menu is available at the front counter upon request.", "record_ms": 12000, "difficulty": 4},
        ],
    },
    {
        "set_id": 2,
        "scenario": "Library Orientation",
        "image_desc": "A floor plan of a three-story university library.",
        "sentences": [
            {"text": "This is the main library.",                                                                  "record_ms": 8000,  "difficulty": 1},
            {"text": "The quiet study area is upstairs.",                                                           "record_ms": 8000,  "difficulty": 1},
            {"text": "Group study rooms can be reserved online.",                                                   "record_ms": 10000, "difficulty": 2},
            {"text": "Books may be borrowed for up to three weeks.",                                                "record_ms": 10000, "difficulty": 2},
            {"text": "If you need help finding a journal article, the reference desk is on the second floor.",      "record_ms": 10000, "difficulty": 3},
            {"text": "Laptops are available for checkout at the circulation desk, but they must be returned by closing time.", "record_ms": 12000, "difficulty": 3},
            {"text": "Students who accumulate more than ten dollars in overdue fines will be unable to register for courses until the balance is cleared.", "record_ms": 12000, "difficulty": 4},
        ],
    },
    {
        "set_id": 3,
        "scenario": "Campus Health Center Visit",
        "image_desc": "A diagram of a campus health center showing reception, exam rooms, and pharmacy.",
        "sentences": [
            {"text": "Please sign in at the front desk.",                                                          "record_ms": 8000,  "difficulty": 1},
            {"text": "Walk-in appointments are accepted daily.",                                                    "record_ms": 8000,  "difficulty": 1},
            {"text": "The pharmacy is located at the end of the hallway.",                                          "record_ms": 10000, "difficulty": 2},
            {"text": "Please bring your student ID and insurance card.",                                            "record_ms": 10000, "difficulty": 2},
            {"text": "If you're experiencing a medical emergency, go directly to the urgent care window on your right.", "record_ms": 10000, "difficulty": 3},
            {"text": "Annual flu vaccinations are offered free of charge to all enrolled students beginning in October.", "record_ms": 12000, "difficulty": 3},
            {"text": "For mental health services, you can schedule a confidential appointment through the student wellness portal, which is accessible from the university homepage.", "record_ms": 12000, "difficulty": 4},
        ],
    },
]

# ── Interview Content ─────────────────────────────────────────
# Each interview = 1 topic, 4 questions, progressive abstraction

INTERVIEW_SETS = [
    {
        "topic": "Daily Routines",
        "intro": "You have agreed to take part in a research study about daily routines. You will have a short online interview with a researcher.",
        "interviewer": "interviewer_f",
        "questions": [
            {"text": "Thank you for joining. Let's start with something simple. Can you describe what a typical morning looks like for you on a school day?", "type": "personal"},
            {"text": "Interesting. Now, think about a time when your regular routine was disrupted — maybe due to travel or an unexpected event. What happened, and how did you handle it?", "type": "experience"},
            {"text": "Some people prefer having a very structured daily schedule, while others like more flexibility. What's your personal preference, and why?", "type": "opinion"},
            {"text": "Looking ahead, if you could redesign your ideal daily routine with no constraints, what would it look like and why?", "type": "hypothetical"},
        ],
    },
    {
        "topic": "Technology in Education",
        "intro": "You have volunteered for a research study about the use of technology in education. You will have a short online interview with a researcher.",
        "interviewer": "interviewer_m",
        "questions": [
            {"text": "Thanks for participating. First, can you tell me about a piece of technology that you use regularly for your studies?", "type": "personal"},
            {"text": "Can you think of a time when technology helped you learn something more effectively than a traditional method would have?", "type": "experience"},
            {"text": "Some educators believe that students rely too heavily on technology and that it's actually harming their ability to think critically. Do you agree or disagree with this view?", "type": "opinion"},
            {"text": "Imagine that your university decided to eliminate all screens from classrooms for one full semester. How do you think that would affect the learning experience?", "type": "hypothetical"},
        ],
    },
    {
        "topic": "Urban Living",
        "intro": "You have agreed to participate in a study about urban life. You will have a short online interview with a researcher.",
        "interviewer": "interviewer_f",
        "questions": [
            {"text": "Thank you for speaking with me today. First, can you tell me about the city or town where you currently live? What do you like about it?", "type": "personal"},
            {"text": "Now, think about the last time you visited a city that you don't live in. What stood out to you about that city, either positively or negatively?", "type": "experience"},
            {"text": "Many cities are trying to limit car traffic in their downtown areas. Some people support this, while others say it hurts businesses. What's your take on this?", "type": "opinion"},
            {"text": "If you had the opportunity to design a brand-new city from scratch, what features would you prioritize, and why?", "type": "hypothetical"},
        ],
    },
]


async def tts(text: str, voice_key: str, path: str):
    v = VOICES[voice_key]
    await edge_tts.Communicate(text, v["id"], rate=v["rate"]).save(path)


async def build_repeat_set(rset: dict, output_dir: str):
    """Build a complete Listen & Repeat practice set with proper timing."""
    set_dir = os.path.join(output_dir, f"repeat-set-{rset['set_id']:02d}")
    os.makedirs(set_dir, exist_ok=True)
    tmp = os.path.join(set_dir, "_tmp")
    os.makedirs(tmp, exist_ok=True)

    all_segments = []  # For full combined audio
    answer_key = []

    for i, sent in enumerate(rset["sentences"]):
        item_segments = []

        # Pre-sentence silence (settle)
        pre = os.path.join(tmp, f"{i}-pre.wav")
        generate_silence_file(pre, 500)
        item_segments.append(pre)

        # The sentence itself
        audio = os.path.join(tmp, f"{i}-sentence.mp3")
        await tts(sent["text"], "narrator", audio)
        item_segments.append(audio)

        # Brief pause before beep
        gap = os.path.join(tmp, f"{i}-gap.wav")
        generate_silence_file(gap, 300)
        item_segments.append(gap)

        # BEEP = "your turn to speak"
        beep = os.path.join(tmp, f"{i}-beep.wav")
        generate_beep_file(beep, frequency=880, duration_ms=250, volume=0.35)
        item_segments.append(beep)

        # Recording silence (8s / 10s / 12s depending on sentence)
        rec = os.path.join(tmp, f"{i}-record.wav")
        generate_silence_file(rec, sent["record_ms"])
        item_segments.append(rec)

        # Build individual item audio
        item_path = os.path.join(set_dir, f"item-{i+1:02d}.mp3")
        concat_audio(item_segments, item_path)

        all_segments.extend(item_segments)
        answer_key.append({
            "item": i + 1,
            "sentence": sent["text"],
            "difficulty": sent["difficulty"],
            "record_seconds": sent["record_ms"] / 1000,
        })

    # Build combined full-set audio
    full_path = os.path.join(set_dir, "full-set.mp3")
    concat_audio(all_segments, full_path)

    # Write metadata
    meta = {
        "type": "listen-and-repeat",
        "set_id": rset["set_id"],
        "scenario": rset["scenario"],
        "image_description": rset["image_desc"],
        "item_count": len(rset["sentences"]),
        "items": answer_key,
    }
    with open(os.path.join(set_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    # Write answer key
    ak_md = f"# Listen & Repeat — Set {rset['set_id']}: {rset['scenario']}\n\n"
    ak_md += f"*{rset['image_desc']}*\n\n"
    ak_md += "| # | ⭐ | Record | Sentence |\n|---|---|--------|----------|\n"
    for item in answer_key:
        ak_md += f"| {item['item']} | {'⭐' * item['difficulty']} | {item['record_seconds']:.0f}s | {item['sentence']} |\n"
    ak_md += "\n## Scoring Reminder\n\n"
    ak_md += "- **5/5**: Exact repetition, clear pronunciation, natural rhythm\n"
    ak_md += "- **4/5**: One small error (article, preposition), still clear\n"
    ak_md += "- **3/5**: Most content words correct, some omissions\n"
    ak_md += "- Keep going even if you miss a word — stopping hurts more than the error\n"

    with open(os.path.join(set_dir, "answer-key.md"), "w", encoding="utf-8") as f:
        f.write(ak_md)

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"✅ Listen & Repeat Set {rset['set_id']}: {rset['scenario']}（{len(rset['sentences'])} 句）")


async def build_interview(interview: dict, output_dir: str, index: int):
    """Build an Interview exercise with proper timing."""
    int_dir = os.path.join(output_dir, f"interview-{index:02d}")
    os.makedirs(int_dir, exist_ok=True)
    tmp = os.path.join(int_dir, "_tmp")
    os.makedirs(tmp, exist_ok=True)

    all_segments = []

    # Intro narration
    intro_audio = os.path.join(tmp, "intro.mp3")
    await tts(interview["intro"], "narrator", intro_audio)
    all_segments.append(intro_audio)

    intro_gap = os.path.join(tmp, "intro-gap.wav")
    generate_silence_file(intro_gap, 2000)
    all_segments.append(intro_gap)

    for i, q in enumerate(interview["questions"]):
        q_segments = []

        # Question audio
        q_audio = os.path.join(tmp, f"q{i}.mp3")
        await tts(q["text"], interview["interviewer"], q_audio)
        q_segments.append(q_audio)

        # Brief pause
        q_gap = os.path.join(tmp, f"q{i}-gap.wav")
        generate_silence_file(q_gap, 500)
        q_segments.append(q_gap)

        # Double beep = "start speaking"
        start_beep = os.path.join(tmp, f"q{i}-start.wav")
        generate_double_beep_file(start_beep, freq=880, beep_ms=150, gap_ms=100, volume=0.35)
        q_segments.append(start_beep)

        # 45 seconds recording silence
        rec = os.path.join(tmp, f"q{i}-record.wav")
        generate_silence_file(rec, 45000)
        q_segments.append(rec)

        # Single beep = "time's up"
        stop_beep = os.path.join(tmp, f"q{i}-stop.wav")
        generate_beep_file(stop_beep, frequency=660, duration_ms=400, volume=0.3)
        q_segments.append(stop_beep)

        # Gap before next question
        next_gap = os.path.join(tmp, f"q{i}-next.wav")
        generate_silence_file(next_gap, 1500)
        q_segments.append(next_gap)

        # Build individual question audio
        q_path = os.path.join(int_dir, f"question-{i+1:02d}.mp3")
        concat_audio(q_segments, q_path)

        all_segments.extend(q_segments)

    # Full interview audio
    full_path = os.path.join(int_dir, "full-interview.mp3")
    concat_audio(all_segments, full_path)

    # Metadata
    meta = {
        "type": "interview",
        "topic": interview["topic"],
        "questions": [
            {"number": i + 1, "text": q["text"], "type": q["type"], "response_time_seconds": 45}
            for i, q in enumerate(interview["questions"])
        ],
    }
    with open(os.path.join(int_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    # Prompt sheet (for text-based practice without audio)
    prompt_md = f"# Interview — {interview['topic']}\n\n"
    prompt_md += f"*{interview['intro']}*\n\n"
    for i, q in enumerate(interview["questions"], 1):
        prompt_md += f"## Question {i} ({q['type']})\n\n"
        prompt_md += f"> {q['text']}\n\n"
        prompt_md += f"⏱️ 45 seconds — no preparation time\n\n"
        prompt_md += "**Your response:**\n\n\n---\n\n"

    prompt_md += "## Self-Assessment\n\n"
    prompt_md += "| Dimension | Score (1-5) | Notes |\n|-----------|------------|-------|\n"
    prompt_md += "| Fluency | | |\n| Intelligibility | | |\n| Language Use | | |\n| Organization | | |\n"
    prompt_md += "\n**Tip:** Use the Idea → Reason → Example structure. Aim for ~150 wpm and speak for the full 45 seconds.\n"

    with open(os.path.join(int_dir, "prompts.md"), "w", encoding="utf-8") as f:
        f.write(prompt_md)

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"✅ Interview {index}: {interview['topic']}（4 questions × 45s）")


async def main_async(args):
    base = Path(args.output)
    base.mkdir(parents=True, exist_ok=True)

    if args.type in ("repeat", "all"):
        sets = REPEAT_SETS
        if args.set:
            sets = [s for s in sets if s["set_id"] == args.set]
        for rset in sets:
            await build_repeat_set(rset, str(base))

    if args.type in ("interview", "all"):
        for i, interview in enumerate(INTERVIEW_SETS, 1):
            await build_interview(interview, str(base), i)

    print(f"\n🎤 口說練習已產生於：{base}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TOEFL 2026 Speaking Generator")
    parser.add_argument("--type", choices=["repeat", "interview", "all"], default="all")
    parser.add_argument("--output", default="./speaking/")
    parser.add_argument("--set", type=int, help="Specific repeat set number")
    parser.add_argument("--topic", type=str, help="Interview topic filter")
    args = parser.parse_args()
    asyncio.run(main_async(args))
