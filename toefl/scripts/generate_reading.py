#!/usr/bin/env python3
"""
TOEFL 2026 Reading Exercise Generator

Produces exercises for all 3 new question types:
  1. Complete the Words — academic text with blanked-out letters
  2. Read in Daily Life — short practical texts (emails, menus, notices)
  3. Read an Academic Passage — ~200-word passage + 5 MCQs

Difficulty tiers match adaptive routing:
  Module 1 (mixed): difficulty 1-2
  Hard Module 2:    difficulty 3
  Easy Module 2:    difficulty 1 (capped at 4.0)

Usage:
    uv run python scripts/generate_reading.py --type all --output ./reading/ --difficulty hard
    uv run python scripts/generate_reading.py --type complete-words --count 3
    uv run python scripts/generate_reading.py --type daily-life --week 5
"""

import argparse
import json
import os
import random
from pathlib import Path


# ── Complete the Words ────────────────────────────────────────
# Academic paragraph with strategic letter removal
# Targeting AWL words that appear in TOEFL contexts

COMPLETE_WORDS_ITEMS = [
    {
        "difficulty": 1,
        "passage": (
            "Climate change is one of the most significant {chall_nges} facing the modern world. "
            "Scientists have gathered extensive {ev_dence} showing that global temperatures are rising. "
            "The primary {f_ctor} contributing to this trend is the burning of fossil fuels, "
            "which releases carbon dioxide into the {atmo_phere}. "
            "Many governments have begun to {impl_ment} policies aimed at reducing emissions. "
            "However, the {eff_ctiveness} of these measures remains a topic of debate among researchers. "
            "Some experts {argu_} that more aggressive action is needed, "
            "while others believe that technological {inn_vation} will provide solutions. "
            "The {con_equences} of inaction could include rising sea levels and extreme weather events. "
            "International {coop_ration} is essential to addressing this global challenge."
        ),
        "answers": ["challenges", "evidence", "factor", "atmosphere", "implement",
                     "effectiveness", "argue", "innovation", "consequences", "cooperation"],
    },
    {
        "difficulty": 2,
        "passage": (
            "The field of {neur_science} has made remarkable progress in understanding how the brain processes language. "
            "Recent {res_arch} using functional MRI technology has revealed that multiple brain regions "
            "{coll_borate} during speech production and comprehension. "
            "One {sign_ficant} discovery is that the brain's language network is more {flex_ble} than previously thought. "
            "Adult learners can develop neural {path_ays} similar to those of native speakers, "
            "particularly through {immers_ve} learning environments. "
            "This finding {contr_dicts} the traditional belief that language acquisition becomes impossible after puberty. "
            "However, the {acquis_tion} of native-like pronunciation remains considerably more {diff_cult} for older learners."
        ),
        "answers": ["neuroscience", "research", "collaborate", "significant", "flexible",
                     "pathways", "immersive", "contradicts", "acquisition", "difficult"],
    },
    {
        "difficulty": 3,
        "passage": (
            "The concept of {sust_inability} has evolved significantly since its introduction in environmental discourse. "
            "Initially {assoc_ated} primarily with ecological conservation, "
            "it now {encom_asses} economic and social dimensions as well. "
            "Contemporary {schol_rs} emphasize the {interd_pendence} of these three pillars, "
            "arguing that {envir_nmental} protection cannot succeed without addressing {ineq_ality} and economic viability. "
            "This {hol_stic} approach has influenced corporate governance, "
            "leading many organizations to adopt {compr_hensive} sustainability frameworks. "
            "The {prolif_ration} of such initiatives, however, has also raised concerns about greenwashing."
        ),
        "answers": ["sustainability", "associated", "encompasses", "scholars", "interdependence",
                     "environmental", "inequality", "holistic", "comprehensive", "proliferation"],
    },
]

# ── Read in Daily Life ────────────────────────────────────────
# Short practical texts: 15-150 words

DAILY_LIFE_ITEMS = [
    {
        "difficulty": 1,
        "title": "Dormitory Move-In Notice",
        "text_type": "notice",
        "text": (
            "**MOVE-IN DAY — Fall 2026**\n\n"
            "Date: August 25 (Sunday)\n"
            "Check-in time: 8:00 AM – 4:00 PM\n"
            "Location: Front desk of your assigned building\n\n"
            "What to bring:\n"
            "- Student ID (required)\n"
            "- Housing agreement (signed)\n"
            "- Bedding and personal items\n\n"
            "Parking: Temporary unloading zone available in Lot C.\n"
            "Vehicles must be moved within 30 minutes.\n\n"
            "Questions? Contact Housing Services at housing@university.edu"
        ),
        "questions": [
            {"q": "What document is required at check-in?", "opts": ["A. Passport", "B. Student ID", "C. Driver's license", "D. Birth certificate"], "ans": "B"},
            {"q": "How long can vehicles stay in the unloading zone?", "opts": ["A. 15 minutes", "B. 30 minutes", "C. 1 hour", "D. No limit"], "ans": "B"},
        ],
    },
    {
        "difficulty": 2,
        "title": "Email from Campus Bookstore",
        "text_type": "email",
        "text": (
            "Subject: Your textbook order — partial shipment\n\n"
            "Hi Jordan,\n\n"
            "Two of the three textbooks you ordered are ready for pickup at the campus bookstore "
            "(Building D, first floor). Your order number is #BK-20261045.\n\n"
            "Unfortunately, \"Introduction to Environmental Science\" (3rd edition) is currently "
            "backordered and is expected to arrive by September 8. We'll send you another email "
            "when it's available.\n\n"
            "In the meantime, your professor has placed a copy on reserve at the library, "
            "which you can borrow for 2-hour periods.\n\n"
            "Pickup hours: Mon–Fri 9 AM – 6 PM, Sat 10 AM – 2 PM\n\n"
            "Best,\n"
            "Campus Bookstore Team"
        ),
        "questions": [
            {"q": "How many textbooks are ready for pickup?", "opts": ["A. One", "B. Two", "C. Three", "D. None"], "ans": "B"},
            {"q": "What can Jordan do while waiting for the backordered book?", "opts": ["A. Download a digital version", "B. Buy it from another store", "C. Borrow a library reserve copy", "D. Ask for a refund"], "ans": "C"},
            {"q": "When is the bookstore open on Saturday?", "opts": ["A. 9 AM – 6 PM", "B. 10 AM – 2 PM", "C. 10 AM – 6 PM", "D. Closed"], "ans": "B"},
        ],
    },
    {
        "difficulty": 3,
        "title": "Shuttle Service Update",
        "text_type": "text_message",
        "text": (
            "**From: Campus Transit**\n"
            "**To: All registered riders**\n\n"
            "Due to the homecoming parade on Oct 12, the following routes will be affected:\n\n"
            "🔴 **Red Line**: Suspended 10 AM – 3 PM. Use Blue Line as alternative (adds ~8 min).\n"
            "🔵 **Blue Line**: Running on extended schedule (every 10 min instead of 15).\n"
            "🟢 **Green Line**: Detour via Oak St. Normal frequency.\n\n"
            "The North Campus stop will be temporarily relocated to the corner of Elm and 5th "
            "(approx. 200m from usual location).\n\n"
            "Regular service resumes at 4 PM. Plan ahead."
        ),
        "questions": [
            {"q": "What is causing the service disruption?", "opts": ["A. Construction", "B. A homecoming parade", "C. A weather event", "D. A driver shortage"], "ans": "B"},
            {"q": "If you normally take the Red Line at noon, what should you do?", "opts": ["A. Wait for it to resume", "B. Take the Blue Line instead", "C. Take the Green Line", "D. Walk"], "ans": "B"},
            {"q": "How often will the Blue Line run during the disruption?", "opts": ["A. Every 5 minutes", "B. Every 10 minutes", "C. Every 15 minutes", "D. Every 20 minutes"], "ans": "B"},
        ],
    },
]

# ── Academic Passages (~200 words + 5 MCQs) ───────────────────

ACADEMIC_PASSAGES = [
    {
        "difficulty": 2,
        "title": "The Urban Heat Island Effect",
        "subject": "Environmental Science",
        "passage": (
            "Urban areas often experience significantly higher temperatures than surrounding rural regions, "
            "a phenomenon known as the urban heat island effect. This temperature difference, which can reach "
            "up to 5 degrees Celsius, results from several factors. Concrete, asphalt, and building materials "
            "absorb and retain solar radiation more effectively than natural surfaces such as soil and vegetation. "
            "Additionally, human activities including transportation, industrial processes, and air conditioning "
            "generate substantial waste heat. The reduction of green spaces in cities further exacerbates the "
            "problem by eliminating the cooling effect of plant transpiration.\n\n"
            "Researchers have proposed various mitigation strategies. Green roofs, which involve planting "
            "vegetation on building tops, can reduce surface temperatures by up to 30 degrees Celsius compared "
            "to conventional roofs. Urban tree canopy programs provide shade and increase evapotranspiration. "
            "Some cities have also experimented with reflective pavement materials that redirect solar energy "
            "rather than absorbing it. While individual interventions show promise, experts emphasize that a "
            "comprehensive approach combining multiple strategies yields the most significant results."
        ),
        "questions": [
            {"q": "What is the main topic of this passage?", "opts": ["A. How to design energy-efficient buildings", "B. The causes and solutions for higher temperatures in cities", "C. A comparison of urban and rural lifestyles", "D. The effects of climate change on agriculture"], "ans": "B"},
            {"q": "According to the passage, how much warmer can urban areas be compared to rural areas?", "opts": ["A. Up to 2°C", "B. Up to 5°C", "C. Up to 10°C", "D. Up to 30°C"], "ans": "B"},
            {"q": "The word 'exacerbates' in paragraph 1 is closest in meaning to:", "opts": ["A. improves", "B. measures", "C. worsens", "D. identifies"], "ans": "C"},
            {"q": "What benefit of green roofs is mentioned?", "opts": ["A. They produce food for residents", "B. They can reduce surface temperatures significantly", "C. They increase property values", "D. They filter air pollution"], "ans": "B"},
            {"q": "What do experts recommend for the best results?", "opts": ["A. Focusing only on green roofs", "B. Planting more trees than anything else", "C. Using a combination of multiple strategies", "D. Reducing the number of vehicles"], "ans": "C"},
        ],
    },
    {
        "difficulty": 3,
        "title": "Mirror Neurons and Social Cognition",
        "subject": "Neuroscience / Psychology",
        "passage": (
            "In the early 1990s, a team of Italian neuroscientists led by Giacomo Rizzolatti made an unexpected "
            "discovery while studying motor neurons in macaque monkeys. They found that certain neurons fired not "
            "only when a monkey performed an action, such as grasping food, but also when it observed another "
            "individual performing the same action. These cells, termed mirror neurons, appeared to create an "
            "internal simulation of observed behaviors.\n\n"
            "The discovery sparked intense interest in whether humans possess a similar system. Subsequent "
            "neuroimaging studies have identified regions in the human brain, particularly the premotor cortex "
            "and inferior parietal lobule, that show mirror-like activity during both action execution and "
            "observation. Some researchers have proposed that this mirror system underlies our capacity for "
            "empathy, imitation learning, and theory of mind — the ability to attribute mental states to others.\n\n"
            "However, the mirror neuron hypothesis has also attracted criticism. Skeptics argue that the evidence "
            "for a discrete mirror neuron system in humans remains indirect, as single-neuron recordings in healthy "
            "humans are rare. Others caution against attributing complex social abilities to a single neural mechanism, "
            "noting that social cognition likely involves distributed networks rather than one specialized system."
        ),
        "questions": [
            {"q": "What was unusual about the neurons Rizzolatti's team discovered?", "opts": ["A. They only fired during sleep", "B. They responded to both performing and observing an action", "C. They were found in an unexpected brain region", "D. They only existed in primates"], "ans": "B"},
            {"q": "The phrase 'theory of mind' as used in paragraph 2 refers to:", "opts": ["A. A scientific theory about brain development", "B. The ability to understand that others have thoughts and feelings", "C. A method for studying neurons", "D. The concept of artificial intelligence"], "ans": "B"},
            {"q": "Why is direct evidence for human mirror neurons limited?", "opts": ["A. The technology doesn't exist yet", "B. Mirror neurons only exist in monkeys", "C. Single-neuron recordings in healthy humans are rarely conducted", "D. The brain regions are too small to study"], "ans": "C"},
            {"q": "What is the main argument of the critics mentioned in paragraph 3?", "opts": ["A. Mirror neurons don't exist at all", "B. Complex social abilities probably involve multiple brain systems, not just one", "C. The original monkey studies were flawed", "D. Empathy cannot be studied scientifically"], "ans": "B"},
            {"q": "How is the passage organized?", "opts": ["A. Problem → solution → evaluation", "B. Discovery → expansion → criticism", "C. Chronological history of neuroscience", "D. Comparison of two competing theories"], "ans": "B"},
        ],
    },
]


def generate_complete_words(items: list, output_dir: str, difficulty: list):
    """Generate Complete the Words exercises."""
    cw_dir = os.path.join(output_dir, "complete-words")
    os.makedirs(cw_dir, exist_ok=True)

    filtered = [it for it in items if it["difficulty"] in difficulty]
    for i, item in enumerate(filtered, 1):
        ex_dir = os.path.join(cw_dir, f"exercise-{i:02d}")
        os.makedirs(ex_dir, exist_ok=True)

        # Exercise file (with blanks)
        with open(os.path.join(ex_dir, "exercise.md"), "w", encoding="utf-8") as f:
            f.write(f"# Complete the Words — Exercise {i}\n\n")
            f.write(f"**Difficulty:** {'⭐' * item['difficulty']}\n\n")
            f.write("Fill in the missing letters to complete each word.\n\n---\n\n")
            f.write(item["passage"])
            f.write("\n")

        # Answer key
        with open(os.path.join(ex_dir, "answers.md"), "w", encoding="utf-8") as f:
            f.write(f"# Answer Key — Exercise {i}\n\n")
            for j, ans in enumerate(item["answers"], 1):
                f.write(f"{j}. **{ans}**\n")

        # Meta
        with open(os.path.join(ex_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump({"type": "complete-words", "difficulty": item["difficulty"], "word_count": len(item["answers"])}, f, indent=2)

    print(f"✅ Complete the Words：{len(filtered)} exercises")


def generate_daily_life(items: list, output_dir: str, difficulty: list):
    """Generate Read in Daily Life exercises."""
    dl_dir = os.path.join(output_dir, "daily-life")
    os.makedirs(dl_dir, exist_ok=True)

    filtered = [it for it in items if it["difficulty"] in difficulty]
    for i, item in enumerate(filtered, 1):
        ex_dir = os.path.join(dl_dir, f"exercise-{i:02d}")
        os.makedirs(ex_dir, exist_ok=True)

        with open(os.path.join(ex_dir, "exercise.md"), "w", encoding="utf-8") as f:
            f.write(f"# Read in Daily Life — {item['title']}\n\n")
            f.write(f"**Type:** {item['text_type']} | **Difficulty:** {'⭐' * item['difficulty']}\n\n---\n\n")
            f.write(item["text"])
            f.write("\n\n---\n\n## Questions\n\n")
            for j, q in enumerate(item["questions"], 1):
                f.write(f"### {j}. {q['q']}\n\n")
                for opt in q["opts"]:
                    f.write(f"- {opt}\n")
                f.write(f"\n<details><summary>Answer</summary>{q['ans']}</details>\n\n")

    print(f"✅ Read in Daily Life：{len(filtered)} exercises")


def generate_academic_passages(items: list, output_dir: str, difficulty: list):
    """Generate Academic Passage exercises."""
    ap_dir = os.path.join(output_dir, "academic-passages")
    os.makedirs(ap_dir, exist_ok=True)

    filtered = [it for it in items if it["difficulty"] in difficulty]
    for i, item in enumerate(filtered, 1):
        ex_dir = os.path.join(ap_dir, f"passage-{i:02d}")
        os.makedirs(ex_dir, exist_ok=True)

        with open(os.path.join(ex_dir, "exercise.md"), "w", encoding="utf-8") as f:
            f.write(f"# Academic Passage — {item['title']}\n\n")
            f.write(f"**Subject:** {item['subject']} | **Difficulty:** {'⭐' * item['difficulty']}\n\n---\n\n")
            f.write(item["passage"])
            f.write("\n\n---\n\n## Questions\n\n")
            for j, q in enumerate(item["questions"], 1):
                f.write(f"### {j}. {q['q']}\n\n")
                for opt in q["opts"]:
                    f.write(f"- {opt}\n")
                f.write(f"\n<details><summary>Answer</summary>{q['ans']}</details>\n\n")

        word_count = len(item["passage"].split())
        with open(os.path.join(ex_dir, "meta.json"), "w", encoding="utf-8") as f:
            json.dump({"type": "academic-passage", "title": item["title"], "subject": item["subject"],
                       "difficulty": item["difficulty"], "word_count": word_count, "question_count": len(item["questions"])}, f, indent=2)

    print(f"✅ Academic Passages：{len(filtered)} exercises")


def main():
    parser = argparse.ArgumentParser(description="TOEFL 2026 Reading Generator")
    parser.add_argument("--type", choices=["complete-words", "daily-life", "academic", "all"], default="all")
    parser.add_argument("--output", default="./reading/")
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard", "all"], default="all")
    parser.add_argument("--week", type=int, help="Study week for content calibration")
    args = parser.parse_args()

    diff_map = {"easy": [1], "medium": [2], "hard": [3], "all": [1, 2, 3]}
    difficulty = diff_map[args.difficulty]

    if args.type in ("complete-words", "all"):
        generate_complete_words(COMPLETE_WORDS_ITEMS, args.output, difficulty)
    if args.type in ("daily-life", "all"):
        generate_daily_life(DAILY_LIFE_ITEMS, args.output, difficulty)
    if args.type in ("academic", "all"):
        generate_academic_passages(ACADEMIC_PASSAGES, args.output, difficulty)

    print(f"\n📖 閱讀練習已產生於：{args.output}")


if __name__ == "__main__":
    main()
