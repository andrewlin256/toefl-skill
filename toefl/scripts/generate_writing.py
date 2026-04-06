#!/usr/bin/env python3
"""
TOEFL 2026 Writing Exercise Generator

Three task types:
  1. Build a Sentence — scrambled words → correct sentence (binary scoring)
  2. Write an Email — scenario + 3 bullet points → email (7 min, 100-180 words)
  3. Academic Discussion — professor Q + 2 student posts → your response (10 min, 120+ words)

Usage:
    uv run python scripts/generate_writing.py --type all --output ./writing/
    uv run python scripts/generate_writing.py --type email --count 3
    uv run python scripts/generate_writing.py --type build-sentence --count 10
"""

import argparse
import json
import os
import random
from pathlib import Path


# ── Build a Sentence ──────────────────────────────────────────
# 5-8 words + optional distractor, answer must be unique

BUILD_SENTENCE_ITEMS = [
    # Easy (Week 1-4)
    {"words": ["wanted", "she", "know", "to", "which", "colleges", "I'm", "considering"], "distractor": None,
     "answer": "She wanted to know which colleges I'm considering.", "grammar_point": "Indirect question (no inversion)"},
    {"words": ["the", "who", "students", "completed", "assignment", "the", "early", "received"], "distractor": "were",
     "answer": "The students who completed the assignment early received...", "grammar_point": "Relative clause (who)"},
    {"words": ["important", "it", "is", "that", "attend", "students", "orientation"], "distractor": None,
     "answer": "It is important that students attend orientation.", "grammar_point": "Subjunctive / it-cleft"},
    {"words": ["professor", "the", "suggested", "we", "review", "chapter", "before", "the", "exam"], "distractor": "would",
     "answer": "The professor suggested we review the chapter before the exam.", "grammar_point": "Subjunctive after suggest"},
    {"words": ["despite", "the", "rain", "continued", "game", "the", "heavy"], "distractor": None,
     "answer": "Despite the heavy rain, the game continued.", "grammar_point": "Despite + noun phrase"},

    # Medium (Week 5-8)
    {"words": ["had", "if", "I", "known", "earlier", "would", "have", "I", "applied"], "distractor": "did",
     "answer": "If I had known earlier, I would have applied.", "grammar_point": "Third conditional"},
    {"words": ["not", "only", "did", "improve", "she", "grades", "her", "but", "also", "leadership", "skills", "her"], "distractor": None,
     "answer": "Not only did she improve her grades, but also her leadership skills.", "grammar_point": "Not only...but also (inversion)"},
    {"words": ["the", "research", "which", "was", "conducted", "last", "year", "significant", "yielded", "results"], "distractor": "had",
     "answer": "The research which was conducted last year yielded significant results.", "grammar_point": "Passive relative clause"},

    # Hard (Week 9-12)
    {"words": ["were", "it", "not", "for", "scholarship", "the", "unable", "to", "I", "would", "be", "attend"], "distractor": "had",
     "answer": "Were it not for the scholarship, I would be unable to attend.", "grammar_point": "Inverted conditional (formal)"},
    {"words": ["the", "extent", "to", "which", "affects", "poverty", "outcomes", "educational", "widely", "is", "documented"], "distractor": None,
     "answer": "The extent to which poverty affects educational outcomes is widely documented.", "grammar_point": "Complex noun phrase + relative"},
]

# ── Write an Email ────────────────────────────────────────────

EMAIL_PROMPTS = [
    {
        "difficulty": 2,
        "scenario": (
            "You are a student at a university. Last week, you attended a career fair organized by "
            "the Career Services office. You met a recruiter from a company you're interested in, "
            "but you forgot to exchange contact information."
        ),
        "recipient": "Career Services Office",
        "bullets": [
            "Describe which company and recruiter you spoke with",
            "Explain why you need the recruiter's contact information",
            "Ask if Career Services can help you connect with the recruiter",
        ],
        "tone": "semi-formal",
        "sample_response": (
            "Subject: Request for Recruiter Contact from Career Fair\n\n"
            "Dear Career Services Team,\n\n"
            "I am writing to ask for your help regarding a connection I made at last week's career fair. "
            "I had a very productive conversation with a recruiter named Sarah from GreenTech Solutions, "
            "who mentioned an internship opportunity in their sustainability department.\n\n"
            "Unfortunately, I forgot to ask for her business card before the event ended. I am very "
            "interested in applying for the internship she described, and I would like to follow up "
            "with her directly to ask some additional questions about the application process.\n\n"
            "Would it be possible for you to share her contact information, or could you forward my "
            "email to her on my behalf? I would greatly appreciate any help you can provide.\n\n"
            "Thank you for your time.\n\n"
            "Best regards,\nAlex Chen"
        ),
        "score": 5,
        "score_notes": "Addresses all 3 bullets with specific details, appropriate semi-formal tone, clear purpose stated in first sentence.",
    },
    {
        "difficulty": 2,
        "scenario": (
            "You recently moved into a new apartment near campus. The apartment manager promised "
            "that the heating system would be repaired before your move-in date, but it still "
            "isn't working. Winter is approaching."
        ),
        "recipient": "Apartment Manager",
        "bullets": [
            "Remind the manager of the repair promise",
            "Explain how the broken heating is affecting you",
            "Request a specific timeline for the repair",
        ],
        "tone": "polite but firm",
        "sample_response": None,
        "score": None,
    },
    {
        "difficulty": 3,
        "scenario": (
            "You are a graduate student. Your thesis advisor has suggested you change your research "
            "methodology from qualitative interviews to quantitative surveys. You have concerns "
            "about this change but want to maintain a good relationship with your advisor."
        ),
        "recipient": "Thesis Advisor (Professor Kim)",
        "bullets": [
            "Acknowledge the advisor's suggestion",
            "Explain your concerns about switching methodologies",
            "Propose a compromise or alternative approach",
        ],
        "tone": "respectful, academic",
        "sample_response": None,
        "score": None,
    },
]

# ── Academic Discussion ───────────────────────────────────────

DISCUSSION_PROMPTS = [
    {
        "difficulty": 2,
        "professor": {
            "name": "Professor Williams",
            "question": (
                "This week, we're discussing whether universities should require all students to take "
                "at least one course in computer science, regardless of their major. Proponents say that "
                "coding is a fundamental skill in the modern economy. Critics argue that it takes time "
                "away from students' chosen fields. What do you think? Should computer science be a "
                "universal requirement?"
            ),
        },
        "students": [
            {
                "name": "Mark",
                "response": (
                    "I strongly support making computer science mandatory. In today's job market, "
                    "almost every field uses technology in some way. Even if you're studying art or history, "
                    "knowing how to code can help you analyze data, build websites, or automate tasks. "
                    "It's like how we require math — not because everyone will be a mathematician, "
                    "but because the skills are universally useful."
                ),
            },
            {
                "name": "Elena",
                "response": (
                    "I disagree with making it a requirement. University is expensive, and students "
                    "should be able to focus on courses that are directly relevant to their career goals. "
                    "If a music major wants to learn coding, they can take an elective. But forcing everyone "
                    "into a CS course could lower the quality of the class and frustrate students who "
                    "aren't interested. We should respect students' autonomy to choose their own education."
                ),
            },
        ],
    },
    {
        "difficulty": 3,
        "professor": {
            "name": "Professor Nakamura",
            "question": (
                "Today's topic is the role of failure in innovation. Some business leaders and educators "
                "argue that we should encourage people to 'fail fast and fail often,' suggesting that "
                "failure is a necessary step toward success. Others worry that this mindset can lead to "
                "carelessness and wasted resources. In your view, is celebrating failure a productive "
                "attitude, or does it have significant downsides?"
            ),
        },
        "students": [
            {
                "name": "David",
                "response": (
                    "I think the 'fail fast' mentality is overrated. While it's true that some great "
                    "innovations came from failed experiments, that doesn't mean failure itself is valuable. "
                    "What matters is what you learn from it. Just failing repeatedly without careful analysis "
                    "is wasteful. I think we should emphasize 'learn fast' instead of 'fail fast.'"
                ),
            },
            {
                "name": "Priya",
                "response": (
                    "I see the value in normalizing failure, especially in education. Many students are "
                    "so afraid of making mistakes that they never take risks or try creative solutions. "
                    "If we create environments where failure is seen as a learning opportunity rather than "
                    "a punishment, people will be more willing to innovate. The key is having a system "
                    "that supports reflection after failure."
                ),
            },
        ],
    },
]


def generate_build_sentence(items: list, output_dir: str):
    bsd = os.path.join(output_dir, "build-sentence")
    os.makedirs(bsd, exist_ok=True)

    with open(os.path.join(bsd, "exercises.md"), "w", encoding="utf-8") as f:
        f.write("# Build a Sentence — Practice Set\n\n")
        f.write("Arrange the words to form a grammatically correct sentence.\n")
        f.write("⚠️ **Scoring: 1 point if perfect, 0 if any error. No partial credit.**\n\n---\n\n")

        for i, item in enumerate(items, 1):
            words = item["words"].copy()
            if item.get("distractor"):
                words.append(item["distractor"])
            random.shuffle(words)
            f.write(f"## {i}.\n\n")
            f.write(f"Words: **{' / '.join(words)}**")
            if item.get("distractor"):
                f.write(f"  *(one word is extra)*")
            f.write(f"\n\n")

    with open(os.path.join(bsd, "answer-key.md"), "w", encoding="utf-8") as f:
        f.write("# Build a Sentence — Answer Key\n\n")
        for i, item in enumerate(items, 1):
            f.write(f"**{i}.** {item['answer']}\n")
            f.write(f"   Grammar: {item['grammar_point']}")
            if item.get("distractor"):
                f.write(f" | Distractor: ~~{item['distractor']}~~")
            f.write("\n\n")

    print(f"✅ Build a Sentence：{len(items)} items")


def generate_emails(prompts: list, output_dir: str):
    ed = os.path.join(output_dir, "write-email")
    os.makedirs(ed, exist_ok=True)

    for i, prompt in enumerate(prompts, 1):
        ex_dir = os.path.join(ed, f"prompt-{i:02d}")
        os.makedirs(ex_dir, exist_ok=True)

        with open(os.path.join(ex_dir, "prompt.md"), "w", encoding="utf-8") as f:
            f.write(f"# Write an Email — Prompt {i}\n\n")
            f.write(f"**Difficulty:** {'⭐' * prompt['difficulty']} | **Time limit:** 7 minutes | **Target:** 100-180 words\n\n---\n\n")
            f.write(f"**Scenario:**\n\n{prompt['scenario']}\n\n")
            f.write(f"**Write an email to:** {prompt['recipient']}\n\n")
            f.write("**In your email, do the following:**\n\n")
            for bullet in prompt['bullets']:
                f.write(f"- {bullet}\n")
            f.write(f"\n**Suggested tone:** {prompt['tone']}\n")
            f.write(f"\n---\n\n## Your Response\n\nSubject:\n\n\n\n")

        if prompt.get("sample_response"):
            with open(os.path.join(ex_dir, "sample-response.md"), "w", encoding="utf-8") as f:
                f.write(f"# Sample Response (Score: {prompt['score']}/5)\n\n")
                f.write(prompt["sample_response"])
                if prompt.get("score_notes"):
                    f.write(f"\n\n---\n\n**Scorer's notes:** {prompt['score_notes']}\n")

    print(f"✅ Write an Email：{len(prompts)} prompts")


def generate_discussions(prompts: list, output_dir: str):
    dd = os.path.join(output_dir, "academic-discussion")
    os.makedirs(dd, exist_ok=True)

    for i, prompt in enumerate(prompts, 1):
        ex_dir = os.path.join(dd, f"discussion-{i:02d}")
        os.makedirs(ex_dir, exist_ok=True)

        with open(os.path.join(ex_dir, "prompt.md"), "w", encoding="utf-8") as f:
            f.write(f"# Academic Discussion — Topic {i}\n\n")
            f.write(f"**Difficulty:** {'⭐' * prompt['difficulty']} | **Time limit:** 10 minutes | **Target:** 120+ words\n\n---\n\n")
            f.write(f"**{prompt['professor']['name']}:**\n\n> {prompt['professor']['question']}\n\n")
            for student in prompt['students']:
                f.write(f"**{student['name']}:**\n\n> {student['response']}\n\n")
            f.write("---\n\n## Your Response\n\n")
            f.write("*(State your position, provide a new argument, and engage with at least one student's point)*\n\n\n\n")
            f.write("---\n\n## Self-Check Before Submitting\n\n")
            f.write("- [ ] I stated a clear position\n")
            f.write("- [ ] I provided a NEW argument (not repeating Mark or Elena)\n")
            f.write("- [ ] I referenced at least one student's point\n")
            f.write("- [ ] I used at least one complex sentence structure\n")
            f.write("- [ ] My response is 120+ words\n")

    print(f"✅ Academic Discussion：{len(prompts)} prompts")


def main():
    parser = argparse.ArgumentParser(description="TOEFL 2026 Writing Generator")
    parser.add_argument("--type", choices=["build-sentence", "email", "discussion", "all"], default="all")
    parser.add_argument("--output", default="./writing/")
    args = parser.parse_args()

    if args.type in ("build-sentence", "all"):
        generate_build_sentence(BUILD_SENTENCE_ITEMS, args.output)
    if args.type in ("email", "all"):
        generate_emails(EMAIL_PROMPTS, args.output)
    if args.type in ("discussion", "all"):
        generate_discussions(DISCUSSION_PROMPTS, args.output)

    print(f"\n✍️ 寫作練習已產生於：{args.output}")


if __name__ == "__main__":
    main()
