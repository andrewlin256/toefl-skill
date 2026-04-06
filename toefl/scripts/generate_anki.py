#!/usr/bin/env python3
"""
TOEFL Vocabulary Anki Deck Generator
Generates .apkg files using genanki with TOEFL academic vocabulary.

Usage:
    python generate_anki.py --output ./vocabulary/anki-decks/ --week 1
    python generate_anki.py --output ./vocabulary/anki-decks/ --words-file ./vocabulary/word-lists/week-01.json
    python generate_anki.py --output ./vocabulary/anki-decks/ --custom-words "ubiquitous,ephemeral,paradigm"

Dependencies:
    pip install genanki
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import genanki
except ImportError:
    print("❌ genanki 未安裝。請執行：pip install genanki")
    sys.exit(1)


# ── Anki Model ──────────────────────────────────────────────

TOEFL_MODEL = genanki.Model(
    1607392320,
    "TOEFL 2026 Vocabulary",
    fields=[
        {"name": "Word"},
        {"name": "Pronunciation"},
        {"name": "PartOfSpeech"},
        {"name": "Definition"},
        {"name": "ChineseDefinition"},
        {"name": "ExampleSentence"},
        {"name": "Synonyms"},
        {"name": "Week"},
    ],
    templates=[
        {
            "name": "Word → Definition",
            "qfmt": """
<div class="card front">
    <div class="word">{{Word}}</div>
    <div class="pos">{{PartOfSpeech}}</div>
</div>""",
            "afmt": """
<div class="card back">
    <div class="word">{{Word}}</div>
    <div class="pron">{{Pronunciation}}</div>
    <div class="pos">{{PartOfSpeech}}</div>
    <hr>
    <div class="def">{{Definition}}</div>
    <div class="zh-def">{{ChineseDefinition}}</div>
    <div class="example">{{ExampleSentence}}</div>
    <div class="syn">Synonyms: {{Synonyms}}</div>
</div>""",
        },
        {
            "name": "Definition → Word",
            "qfmt": """
<div class="card front">
    <div class="def">{{Definition}}</div>
    <div class="zh-def">{{ChineseDefinition}}</div>
</div>""",
            "afmt": """
<div class="card back">
    <div class="word">{{Word}}</div>
    <div class="pron">{{Pronunciation}}</div>
    <div class="pos">{{PartOfSpeech}}</div>
    <hr>
    <div class="def">{{Definition}}</div>
    <div class="example">{{ExampleSentence}}</div>
</div>""",
        },
        {
            "name": "Spelling (Listen → Type)",
            "qfmt": """
<div class="card front">
    <div class="def">{{Definition}}</div>
    <div class="hint">Spell the word ({{PartOfSpeech}})</div>
    {{type:Word}}
</div>""",
            "afmt": """
<div class="card back">
    {{type:Word}}
    <hr>
    <div class="word">{{Word}}</div>
    <div class="pron">{{Pronunciation}}</div>
    <div class="example">{{ExampleSentence}}</div>
</div>""",
        },
    ],
    css="""
.card { font-family: 'Georgia', serif; text-align: center; padding: 20px; }
.word { font-size: 28px; font-weight: bold; color: #2c3e50; margin-bottom: 8px; }
.pron { font-size: 16px; color: #7f8c8d; font-style: italic; }
.pos { font-size: 14px; color: #95a5a6; margin-bottom: 10px; }
.def { font-size: 18px; color: #2c3e50; margin: 10px 0; }
.zh-def { font-size: 16px; color: #3498db; margin: 5px 0; }
.example { font-size: 14px; color: #555; font-style: italic; margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 5px; }
.syn { font-size: 13px; color: #7f8c8d; }
.hint { font-size: 14px; color: #e74c3c; margin: 10px 0; }
hr { border: 1px solid #ecf0f1; }
""",
)

# ── Sample vocabulary (first 4 weeks) ──────────────────────

CORE_VOCABULARY = {
    1: [
        {"word": "adequate", "pron": "/ˈæd.ɪ.kwət/", "pos": "adj.", "def": "sufficient for a particular purpose", "zh": "足夠的", "ex": "The funding was adequate to complete the research project.", "syn": "sufficient, enough"},
        {"word": "analyze", "pron": "/ˈæn.ə.laɪz/", "pos": "v.", "def": "to examine in detail", "zh": "分析", "ex": "Scientists analyzed the data from the experiment.", "syn": "examine, study, investigate"},
        {"word": "approach", "pron": "/əˈproʊtʃ/", "pos": "n./v.", "def": "a way of dealing with something", "zh": "方法；接近", "ex": "The professor suggested a new approach to the problem.", "syn": "method, strategy"},
        {"word": "benefit", "pron": "/ˈben.ɪ.fɪt/", "pos": "n./v.", "def": "an advantage or profit gained", "zh": "好處；受益", "ex": "Students benefit from hands-on laboratory experience.", "syn": "advantage, gain"},
        {"word": "concept", "pron": "/ˈkɑːn.sept/", "pos": "n.", "def": "an abstract idea", "zh": "概念", "ex": "The concept of sustainability is central to environmental science.", "syn": "idea, notion"},
        {"word": "consist", "pron": "/kənˈsɪst/", "pos": "v.", "def": "to be composed or made up of", "zh": "由...組成", "ex": "The exam consists of four sections.", "syn": "comprise, include"},
        {"word": "context", "pron": "/ˈkɑːn.tekst/", "pos": "n.", "def": "the circumstances surrounding an event", "zh": "脈絡；上下文", "ex": "Understanding the historical context is essential.", "syn": "setting, background"},
        {"word": "derive", "pron": "/dɪˈraɪv/", "pos": "v.", "def": "to obtain from a source", "zh": "源自；獲得", "ex": "Many English words derive from Latin.", "syn": "obtain, originate"},
        {"word": "distribute", "pron": "/dɪˈstrɪb.juːt/", "pos": "v.", "def": "to give out or spread", "zh": "分配；散佈", "ex": "The professor distributed the syllabus on the first day.", "syn": "allocate, disperse"},
        {"word": "establish", "pron": "/ɪˈstæb.lɪʃ/", "pos": "v.", "def": "to set up or found", "zh": "建立", "ex": "The university established a new research center.", "syn": "found, create, set up"},
        {"word": "estimate", "pron": "/ˈes.tɪ.meɪt/", "pos": "v./n.", "def": "to roughly calculate or judge", "zh": "估計", "ex": "Researchers estimate that the population will double.", "syn": "approximate, assess"},
        {"word": "evident", "pron": "/ˈev.ɪ.dənt/", "pos": "adj.", "def": "clearly seen or understood", "zh": "明顯的", "ex": "The effects of climate change are increasingly evident.", "syn": "obvious, apparent, clear"},
        {"word": "factor", "pron": "/ˈfæk.tɚ/", "pos": "n.", "def": "a circumstance contributing to a result", "zh": "因素", "ex": "Economic factors played a role in the migration.", "syn": "element, component"},
        {"word": "function", "pron": "/ˈfʌŋk.ʃən/", "pos": "n./v.", "def": "the purpose or role of something", "zh": "功能；運作", "ex": "The brain functions as the control center of the body.", "syn": "role, purpose, operate"},
        {"word": "indicate", "pron": "/ˈɪn.dɪ.keɪt/", "pos": "v.", "def": "to point out or show", "zh": "指出；顯示", "ex": "The results indicate a strong correlation.", "syn": "show, suggest, demonstrate"},
        {"word": "interpret", "pron": "/ɪnˈtɝː.prɪt/", "pos": "v.", "def": "to explain the meaning of", "zh": "詮釋", "ex": "Students were asked to interpret the poem.", "syn": "explain, construe"},
        {"word": "major", "pron": "/ˈmeɪ.dʒɚ/", "pos": "adj.", "def": "important, serious, or significant", "zh": "主要的", "ex": "Pollution is a major environmental concern.", "syn": "significant, primary"},
        {"word": "method", "pron": "/ˈmeθ.əd/", "pos": "n.", "def": "a way of doing something", "zh": "方法", "ex": "The scientific method involves hypothesis testing.", "syn": "technique, procedure"},
        {"word": "occur", "pron": "/əˈkɝː/", "pos": "v.", "def": "to happen or take place", "zh": "發生", "ex": "Earthquakes frequently occur along fault lines.", "syn": "happen, take place"},
        {"word": "principle", "pron": "/ˈprɪn.sə.pəl/", "pos": "n.", "def": "a fundamental truth or rule", "zh": "原則", "ex": "The principle of supply and demand governs markets.", "syn": "rule, law, tenet"},
    ],
    # Weeks 2-4 can be generated dynamically by Claude based on student's needs
}


def generate_deck(words: list, week: int, output_dir: str):
    """Generate an Anki deck from a list of word dictionaries."""
    deck = genanki.Deck(
        2059400110 + week,
        f"TOEFL 2026 — Week {week:02d}",
    )

    for w in words:
        note = genanki.Note(
            model=TOEFL_MODEL,
            fields=[
                w.get("word", ""),
                w.get("pron", ""),
                w.get("pos", ""),
                w.get("def", ""),
                w.get("zh", ""),
                w.get("ex", ""),
                w.get("syn", ""),
                str(week),
            ],
        )
        deck.add_note(note)

    output_path = os.path.join(output_dir, f"toefl-week-{week:02d}.apkg")
    genanki.Package(deck).write_to_file(output_path)
    print(f"✅ Anki deck 已產生：{output_path}（{len(words)} 張卡片）")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="TOEFL Vocabulary Anki Deck Generator")
    parser.add_argument("--output", default="./vocabulary/anki-decks/", help="Output directory")
    parser.add_argument("--week", type=int, default=1, help="Week number (uses built-in word list)")
    parser.add_argument("--words-file", type=str, help="Path to JSON file with word list")
    parser.add_argument("--custom-words", type=str, help="Comma-separated list of words (Claude will fill details)")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    if args.words_file:
        with open(args.words_file, "r", encoding="utf-8") as f:
            words = json.load(f)
        generate_deck(words, args.week, args.output)
    elif args.custom_words:
        # Generate minimal entries for custom words (Claude should enrich these)
        words = [{"word": w.strip(), "pron": "", "pos": "", "def": "", "zh": "", "ex": "", "syn": ""} for w in args.custom_words.split(",")]
        generate_deck(words, args.week, args.output)
    else:
        words = CORE_VOCABULARY.get(args.week, CORE_VOCABULARY[1])
        generate_deck(words, args.week, args.output)


if __name__ == "__main__":
    main()
