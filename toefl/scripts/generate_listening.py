#!/usr/bin/env python3
"""
TOEFL 2026 Listening Exercise Generator

Audio design:
  - 1.5s silence before each clip starts (settle-in time)
  - Conversations: 0.8s pause between speaker turns
  - Academic talks: natural pacing at 140-160 wpm
  - Announcements: slightly formal pacing at 130 wpm
  - Choose a Response: statement → 2s pause → beep (answer prompt)
  - All clips end with 1s silence before questions
  - Difficulty tiers: Module 1 (mixed) → Hard Module 2 (academic)

Usage:
    uv run python scripts/generate_listening.py --type all --output ./listening/ --difficulty hard
    uv run python scripts/generate_listening.py --type conversation --week 3
    uv run python scripts/generate_listening.py --type choose-response --count 10
"""

import argparse
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

# Add parent dir for local imports
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

# ── Voice Profiles ──────────────────────────────────────────
# Each voice has a persona to maintain consistency across exercises

VOICES = {
    "professor_m":   {"id": "en-US-GuyNeural",    "rate": "-5%",  "desc": "Male professor, measured pace"},
    "professor_f":   {"id": "en-US-AriaNeural",    "rate": "-5%",  "desc": "Female professor, clear"},
    "student_f":     {"id": "en-US-JennyNeural",   "rate": "+5%",  "desc": "Female student, natural"},
    "student_m":     {"id": "en-US-TonyNeural",    "rate": "+5%",  "desc": "Male student, casual"},
    "advisor":       {"id": "en-US-SaraNeural",    "rate": "+0%",  "desc": "Academic advisor, warm"},
    "announcer":     {"id": "en-US-AriaNeural",     "rate": "-8%",  "desc": "PA announcer, formal slow"},
    "librarian":     {"id": "en-US-JennyNeural",   "rate": "-3%",  "desc": "Librarian, helpful"},
    "narrator":      {"id": "en-US-AriaNeural",     "rate": "+0%",  "desc": "Narrator / directions"},
}

# ── Audio Timing Constants (milliseconds) ────────────────────

SETTLE_IN = 1500         # Silence before clip starts
TURN_GAP = 800           # Pause between speaker turns in conversation
LONG_PAUSE = 1200        # Pause after a key point in a lecture
ANSWER_PAUSE = 2000      # Pause before answer beep (Choose a Response)
END_SILENCE = 1000       # Silence after clip ends
QUESTION_GAP = 3000      # Gap between questions in exercise mode

# ── Content: Choose a Response (Module 1 staple) ─────────────

CHOOSE_RESPONSE_ITEMS = [
    # Easy (Module 1 warm-up)
    {
        "difficulty": 1,
        "prompt": "Excuse me, do you know where the registrar's office is?",
        "speaker": "student_f",
        "options": [
            "A. Yes, it's on the second floor of the administration building.",
            "B. I registered for three courses this semester.",
            "C. The office opens at nine o'clock.",
            "D. You're excused from today's class.",
        ],
        "answer": "A",
        "explanation": "The question asks for a location. Only A provides directions.",
    },
    {
        "difficulty": 1,
        "prompt": "Would you like to join our study group for the midterm?",
        "speaker": "student_m",
        "options": [
            "A. The midterm covers chapters four through eight.",
            "B. That sounds great. When do you usually meet?",
            "C. I already joined the soccer club.",
            "D. The group project is due next week.",
        ],
        "answer": "B",
        "explanation": "B is the only response that acknowledges the invitation and continues the conversation naturally.",
    },
    # Medium
    {
        "difficulty": 2,
        "prompt": "I was thinking about switching my major from biology to chemistry, but I'm not sure if my credits would transfer.",
        "speaker": "student_f",
        "options": [
            "A. Chemistry has a lot of lab requirements.",
            "B. You should talk to your academic advisor about that.",
            "C. Biology is a more popular major.",
            "D. I switched my schedule last week too.",
        ],
        "answer": "B",
        "explanation": "The speaker expresses uncertainty about credit transfer — advising them to see an advisor is the most helpful response.",
    },
    {
        "difficulty": 2,
        "prompt": "Professor, I noticed the reading assignment for next week isn't posted on the course website yet.",
        "speaker": "student_m",
        "options": [
            "A. Thanks for pointing that out. I'll upload it this afternoon.",
            "B. The website was redesigned over the summer.",
            "C. You should read at least thirty pages per week.",
            "D. Next week's class is cancelled.",
        ],
        "answer": "A",
        "explanation": "A acknowledges the issue and provides a resolution — this is the natural response from a professor.",
    },
    # Hard (pragmatic inference)
    {
        "difficulty": 3,
        "prompt": "I've been waiting for the shuttle for twenty minutes. This is the third time this week it's been late.",
        "speaker": "student_f",
        "options": [
            "A. The shuttle runs every fifteen minutes.",
            "B. Maybe you should file a complaint with campus transportation.",
            "C. I usually walk to class.",
            "D. Twenty minutes isn't that long.",
        ],
        "answer": "B",
        "explanation": "The speaker is expressing frustration (not just stating a fact). B acknowledges the frustration and offers actionable advice.",
    },
    {
        "difficulty": 3,
        "prompt": "I can't believe the library is closing for renovations right before finals week.",
        "speaker": "student_m",
        "options": [
            "A. The renovations should be finished by next semester.",
            "B. I know, the timing is terrible. Have you tried the study rooms in the student center?",
            "C. The library has a great collection of journals.",
            "D. Finals week starts on December tenth.",
        ],
        "answer": "B",
        "explanation": "The speaker's tone implies frustration and need for alternatives. B validates the feeling and offers a practical solution.",
    },
]

# ── Content: Conversations (Module 1 + Module 2) ─────────────

CONVERSATIONS = [
    {
        "difficulty": 2,
        "title": "Requesting a Deadline Extension",
        "context": "A student visits a professor's office to discuss a paper deadline.",
        "lines": [
            {"s": "student_m", "t": "Professor Chen, do you have a moment? I wanted to ask about the research paper that's due on Friday."},
            {"s": "professor_f", "t": "Sure, come in. What's on your mind?"},
            {"s": "student_m", "t": "Well, I've been working on it steadily, but I've had trouble finding enough sources for my argument about renewable energy policy. The library's database was down for two days last week."},
            {"s": "professor_f", "t": "I see. That's frustrating. How far along are you with the paper?"},
            {"s": "student_m", "t": "I have my outline and about half the paper written. I just need more time to find credible sources and incorporate them properly. I don't want to submit something that isn't well-supported."},
            {"s": "professor_f", "t": "I appreciate that you're taking the research seriously. I can give you until Monday, but I should mention that there will be a five-percent penalty for late submissions according to the syllabus. However, given the database issue, I'll waive that this time."},
            {"s": "student_m", "t": "Thank you so much. That makes a big difference. I'll make sure to use at least the eight peer-reviewed sources you recommended."},
            {"s": "professor_f", "t": "Good. And one more thing — have you tried the interlibrary loan system? If our database doesn't have what you need, you can request articles from other universities. It usually takes about twenty-four hours."},
        ],
        "questions": [
            {"q": "Why does the student visit the professor?", "opts": ["A. To submit his paper early", "B. To request more time for an assignment", "C. To ask about the grading rubric", "D. To discuss his thesis topic"], "ans": "B"},
            {"q": "What reason does the student give for needing more time?", "opts": ["A. He was sick last week", "B. He had too many other assignments", "C. The library database was unavailable", "D. He changed his topic"], "ans": "C"},
            {"q": "What does the professor offer?", "opts": ["A. A new topic", "B. An extension until Monday without penalty", "C. Extra credit", "D. Help finding sources"], "ans": "B"},
            {"q": "What does the professor suggest the student try?", "opts": ["A. A different database", "B. The interlibrary loan system", "C. Google Scholar", "D. Emailing other professors"], "ans": "B"},
        ],
    },
    {
        "difficulty": 3,
        "title": "Housing Assignment Mix-Up",
        "context": "A student goes to the housing office about a room assignment problem.",
        "lines": [
            {"s": "student_f", "t": "Hi, I'm having an issue with my housing assignment for next semester. The system shows me in a triple room in Morrison Hall, but I applied and was approved for a single room in Greenfield."},
            {"s": "advisor", "t": "Let me pull up your file. What's your student ID?"},
            {"s": "student_f", "t": "It's seven four two one eight zero. I have the confirmation email right here on my phone if you need to see it."},
            {"s": "advisor", "t": "I see. So your original application was indeed for a single in Greenfield, and it was approved in March. But it looks like when the system migrated to the new software in April, several assignments were shuffled. You're not the only one affected."},
            {"s": "student_f", "t": "That's concerning. Is there a way to fix it? I specifically chose a single because I'm a graduate student and I need quiet for my research."},
            {"s": "advisor", "t": "Absolutely. I'll file a correction request today. The original approval takes priority. In the meantime, I'd recommend also emailing Doctor Patterson in graduate housing — she's been handling these migration cases directly and can sometimes expedite things."},
            {"s": "student_f", "t": "Great. How long does the correction usually take?"},
            {"s": "advisor", "t": "Typically five to seven business days, but with the email to Doctor Patterson, it could be faster. I'll also flag your case as urgent since it involves a graduate student accommodation."},
        ],
        "questions": [
            {"q": "What is the student's problem?", "opts": ["A. She was assigned to the wrong building and room type", "B. Her housing application was rejected", "C. She wants to change roommates", "D. Her room has maintenance issues"], "ans": "A"},
            {"q": "What caused the assignment error?", "opts": ["A. The student submitted the wrong form", "B. A software migration shuffled assignments", "C. The room was already taken", "D. Budget cuts reduced available rooms"], "ans": "B"},
            {"q": "Why does the student need a single room?", "opts": ["A. She has a medical condition", "B. She is a resident advisor", "C. She needs quiet for graduate research", "D. She doesn't get along with roommates"], "ans": "C"},
            {"q": "What TWO steps does the advisor recommend?", "opts": ["A. Filing a correction and emailing Dr. Patterson", "B. Applying to a different building", "C. Waiting until next semester", "D. Speaking to the dean"], "ans": "A"},
        ],
    },
]

# ── Content: Announcements ───────────────────────────────────

ANNOUNCEMENTS = [
    {
        "difficulty": 2,
        "title": "Lab Safety Training Requirement",
        "speaker": "announcer",
        "text": (
            "Attention all students enrolled in laboratory courses for the fall semester. "
            "This is a reminder that completion of the online lab safety training module is mandatory "
            "before you can attend your first lab session. The training covers proper handling of chemicals, "
            "emergency procedures, and equipment protocols. It takes approximately forty-five minutes to complete. "
            "The deadline to finish the training is September fifth. Students who have not completed it by that date "
            "will be temporarily dropped from their lab section and must re-enroll once certified. "
            "To access the module, log into the student portal and navigate to the Safety Training tab under Academic Services. "
            "If you completed lab safety training last year, please note that certification expires annually "
            "and you must retake it. For questions, contact the Office of Environmental Health and Safety."
        ),
        "questions": [
            {"q": "What is the purpose of this announcement?", "opts": ["A. To announce a new lab course", "B. To remind students about mandatory safety training", "C. To introduce a new safety officer", "D. To describe lab equipment"], "ans": "B"},
            {"q": "What happens if a student misses the deadline?", "opts": ["A. They receive a warning", "B. They must pay a fee", "C. They are dropped from their lab section", "D. They fail the course"], "ans": "C"},
            {"q": "How long does the training take?", "opts": ["A. Thirty minutes", "B. Forty-five minutes", "C. One hour", "D. Two hours"], "ans": "B"},
        ],
    },
]

# ── Content: Academic Talks (Hard Module 2 only) ──────────────

ACADEMIC_TALKS = [
    {
        "difficulty": 3,
        "title": "Neuroplasticity and Language Acquisition",
        "speaker": "professor_m",
        "text": (
            "So, last time we discussed the critical period hypothesis, "
            "the idea that there's a window during childhood when language acquisition happens most naturally. "
            "[PAUSE] "
            "Today I want to complicate that picture a bit by talking about neuroplasticity. "
            "Neuroplasticity refers to the brain's ability to reorganize itself by forming new neural connections throughout life. "
            "[PAUSE] "
            "Now, the traditional view, championed by Lenneberg in the nineteen sixties, "
            "held that after puberty, the brain loses much of its capacity to acquire language natively. "
            "And there's evidence for this — think of the difficulty most adults have achieving native-like pronunciation in a second language. "
            "[PAUSE] "
            "But recent research has challenged the absoluteness of this view. "
            "A twenty twenty-two study by Hartshorne and colleagues analyzed data from nearly seven hundred thousand English learners "
            "and found that while the critical period for achieving native-level grammar does end around seventeen or eighteen, "
            "the decline is gradual, not a cliff. "
            "[PAUSE] "
            "Moreover, neuroimaging studies show that adult language learners can develop neural pathways "
            "that closely resemble those of native speakers, especially with intensive immersion. "
            "The key factor isn't age per se — it's the quantity and quality of input. "
            "[PAUSE] "
            "This has practical implications for language education. "
            "Programs that emphasize immersive, contextual learning tend to produce better outcomes than grammar-translation methods, "
            "even for adult learners. "
            "In our next class, we'll look at specific case studies of successful late language acquisition "
            "and what they tell us about optimal learning strategies."
        ),
        "questions": [
            {"q": "What is the main topic of this lecture?", "opts": [
                "A. Why children learn languages better than adults",
                "B. How neuroplasticity challenges traditional views on language learning age limits",
                "C. The history of neuroscience research",
                "D. Methods for teaching grammar to adults",
            ], "ans": "B"},
            {"q": "According to the study mentioned, when does the critical period for native-level grammar end?", "opts": [
                "A. Around age ten",
                "B. At puberty",
                "C. Around seventeen or eighteen",
                "D. It never ends",
            ], "ans": "C"},
            {"q": "What factor does the professor identify as most important for adult language acquisition?", "opts": [
                "A. Starting age",
                "B. Natural talent",
                "C. Quantity and quality of input",
                "D. Grammar instruction",
            ], "ans": "C"},
            {"q": "What will the next class cover?", "opts": [
                "A. More neuroimaging studies",
                "B. Case studies of successful late language acquisition",
                "C. A review of the critical period hypothesis",
                "D. An exam on neuroplasticity",
            ], "ans": "B"},
        ],
    },
]


# ── Audio Generation Engine ───────────────────────────────────

async def tts_to_file(text: str, voice_key: str, output_path: str):
    """Generate TTS audio with voice profile settings."""
    v = VOICES[voice_key]
    communicate = edge_tts.Communicate(text, v["id"], rate=v["rate"])
    await communicate.save(output_path)


async def build_conversation_audio(conv: dict, output_dir: str):
    """Build a complete conversation exercise with proper timing."""
    os.makedirs(output_dir, exist_ok=True)
    tmp = os.path.join(output_dir, "_tmp")
    os.makedirs(tmp, exist_ok=True)

    segments = []

    # 1. Settle-in silence
    settle = os.path.join(tmp, "settle.wav")
    generate_silence_file(settle, SETTLE_IN)
    segments.append(settle)

    # 2. Each dialogue line with turn gaps
    for i, line in enumerate(conv["lines"]):
        clip = os.path.join(tmp, f"line-{i:02d}.mp3")
        await tts_to_file(line["t"], line["s"], clip)
        segments.append(clip)

        # Pause between turns
        if i < len(conv["lines"]) - 1:
            gap = os.path.join(tmp, f"gap-{i:02d}.wav")
            generate_silence_file(gap, TURN_GAP)
            segments.append(gap)

    # 3. End silence
    end_sil = os.path.join(tmp, "end.wav")
    generate_silence_file(end_sil, END_SILENCE)
    segments.append(end_sil)

    # 4. Concatenate
    final = os.path.join(output_dir, "audio.mp3")
    result = concat_audio(segments, final)

    if not result:
        # Fallback: keep individual files, rename cleanly
        for i, line in enumerate(conv["lines"]):
            src = os.path.join(tmp, f"line-{i:02d}.mp3")
            dst = os.path.join(output_dir, f"line-{i:02d}.mp3")
            if os.path.exists(src):
                os.rename(src, dst)
        print(f"  ⚠️ 無法合併，已保留個別音檔")

    # Cleanup tmp
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

    return final if result else output_dir


async def build_academic_talk_audio(talk: dict, output_dir: str):
    """Build an academic talk with natural pauses at [PAUSE] markers."""
    os.makedirs(output_dir, exist_ok=True)
    tmp = os.path.join(output_dir, "_tmp")
    os.makedirs(tmp, exist_ok=True)

    # Split text at [PAUSE] markers
    parts = talk["text"].split("[PAUSE]")
    segments = []

    # Settle-in
    settle = os.path.join(tmp, "settle.wav")
    generate_silence_file(settle, SETTLE_IN)
    segments.append(settle)

    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        clip = os.path.join(tmp, f"part-{i:02d}.mp3")
        await tts_to_file(part, talk["speaker"], clip)
        segments.append(clip)

        # Natural pause between segments
        if i < len(parts) - 1:
            pause = os.path.join(tmp, f"pause-{i:02d}.wav")
            generate_silence_file(pause, LONG_PAUSE)
            segments.append(pause)

    # End silence
    end_sil = os.path.join(tmp, "end.wav")
    generate_silence_file(end_sil, END_SILENCE)
    segments.append(end_sil)

    final = os.path.join(output_dir, "audio.mp3")
    concat_audio(segments, final)

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)


async def build_choose_response_audio(items: list, output_dir: str):
    """Build Choose a Response exercises: statement → pause → beep."""
    os.makedirs(output_dir, exist_ok=True)

    for i, item in enumerate(items):
        item_dir = os.path.join(output_dir, f"item-{i+1:02d}")
        os.makedirs(item_dir, exist_ok=True)
        tmp = os.path.join(item_dir, "_tmp")
        os.makedirs(tmp, exist_ok=True)

        segments = []

        # Settle-in
        settle = os.path.join(tmp, "settle.wav")
        generate_silence_file(settle, 1000)
        segments.append(settle)

        # Statement
        stmt = os.path.join(tmp, "statement.mp3")
        await tts_to_file(item["prompt"], item["speaker"], stmt)
        segments.append(stmt)

        # Pause before answer
        pause = os.path.join(tmp, "pause.wav")
        generate_silence_file(pause, ANSWER_PAUSE)
        segments.append(pause)

        # Beep (answer now)
        beep = os.path.join(tmp, "beep.wav")
        generate_beep_file(beep, frequency=660, duration_ms=250, volume=0.3)
        segments.append(beep)

        # Brief silence after beep
        post_beep = os.path.join(tmp, "post.wav")
        generate_silence_file(post_beep, 500)
        segments.append(post_beep)

        # Concatenate
        final = os.path.join(item_dir, "audio.mp3")
        concat_audio(segments, final)

        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"✅ Choose a Response：{len(items)} 題已產生")


def write_exercise_meta(content: dict, output_dir: str, ex_type: str):
    """Write transcript, questions, and metadata files."""
    os.makedirs(output_dir, exist_ok=True)

    # Transcript
    transcript = f"# {content.get('title', ex_type)}\n\n"
    if "context" in content:
        transcript += f"*{content['context']}*\n\n"
    if "lines" in content:
        for line in content["lines"]:
            name = VOICES[line["s"]]["desc"].split(",")[0]
            transcript += f"**{name}:** {line['t']}\n\n"
    elif "text" in content:
        # Replace [PAUSE] with visual marker
        transcript += content["text"].replace("[PAUSE]", "\n\n---\n\n") + "\n"

    with open(os.path.join(output_dir, "transcript.md"), "w", encoding="utf-8") as f:
        f.write(transcript)

    # Questions
    questions = content.get("questions", content.get("questions", []))
    if questions:
        q_md = f"# Questions — {content.get('title', '')}\n\n"
        q_md += f"**Difficulty:** {'⭐' * content.get('difficulty', 2)}\n\n"
        for j, q in enumerate(questions, 1):
            q_md += f"## {j}. {q['q']}\n\n"
            for opt in q.get("opts", q.get("options", [])):
                q_md += f"- {opt}\n"
            q_md += f"\n<details><summary>Answer</summary>{q.get('ans', q.get('answer', ''))}"
            if "explanation" in q:
                q_md += f" — {q['explanation']}"
            q_md += "</details>\n\n"

        with open(os.path.join(output_dir, "questions.md"), "w", encoding="utf-8") as f:
            f.write(q_md)

    # Metadata
    meta = {
        "type": ex_type,
        "title": content.get("title", ""),
        "difficulty": content.get("difficulty", 2),
        "question_count": len(questions),
    }
    with open(os.path.join(output_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)


async def generate_all(args):
    """Main generation entry point."""
    base = Path(args.output)
    base.mkdir(parents=True, exist_ok=True)

    difficulty_filter = {"easy": [1], "medium": [2], "hard": [3], "all": [1, 2, 3]}
    allowed = difficulty_filter.get(args.difficulty, [1, 2, 3])

    if args.type in ("choose-response", "all"):
        items = [it for it in CHOOSE_RESPONSE_ITEMS if it["difficulty"] in allowed]
        cr_dir = base / "choose-response"
        await build_choose_response_audio(items, str(cr_dir))
        for i, item in enumerate(items):
            write_exercise_meta(item, str(cr_dir / f"item-{i+1:02d}"), "choose-response")

    if args.type in ("conversation", "all"):
        convs = [c for c in CONVERSATIONS if c["difficulty"] in allowed]
        for i, conv in enumerate(convs):
            conv_dir = base / f"conversation-{i+1:02d}"
            await build_conversation_audio(conv, str(conv_dir))
            write_exercise_meta(conv, str(conv_dir), "conversation")
            print(f"✅ Conversation {i+1}: {conv['title']}")

    if args.type in ("announcement", "all"):
        anns = [a for a in ANNOUNCEMENTS if a["difficulty"] in allowed]
        for i, ann in enumerate(anns):
            ann_dir = base / f"announcement-{i+1:02d}"
            await build_academic_talk_audio(ann, str(ann_dir))
            write_exercise_meta(ann, str(ann_dir), "announcement")
            print(f"✅ Announcement {i+1}: {ann['title']}")

    if args.type in ("academic", "all"):
        talks = [t for t in ACADEMIC_TALKS if t["difficulty"] in allowed]
        for i, talk in enumerate(talks):
            talk_dir = base / f"academic-{i+1:02d}"
            await build_academic_talk_audio(talk, str(talk_dir))
            write_exercise_meta(talk, str(talk_dir), "academic-talk")
            print(f"✅ Academic Talk {i+1}: {talk['title']}")

    print(f"\n🎧 聽力練習已產生於：{base}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TOEFL 2026 Listening Generator")
    parser.add_argument("--type", choices=["choose-response", "conversation", "announcement", "academic", "all"], default="all")
    parser.add_argument("--output", default="./listening/")
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard", "all"], default="all")
    parser.add_argument("--week", type=int, help="Generate content appropriate for this study week")
    args = parser.parse_args()
    asyncio.run(generate_all(args))
