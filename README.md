# toefl

[![Build & Release Skill](https://github.com/htlin222/toefl-skill/actions/workflows/release.yml/badge.svg)](https://github.com/htlin222/toefl-skill/actions/workflows/release.yml)
[![GitHub Release](https://img.shields.io/github/v/release/htlin222/toefl-skill?include_prereleases&label=skill%20version)](https://github.com/htlin222/toefl-skill/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey.svg)](https://opensource.org/licenses/MIT)
[![Skills Protocol](https://img.shields.io/badge/protocol-vercel--labs%2Fskills-blue)](https://github.com/vercel-labs/skills)
[![Compatible Agents](https://img.shields.io/badge/agents-40%2B-green)](https://github.com/vercel-labs/skills#supported-agents)

> TOEFL iBT 2026 備考教練與學習系統。在空白資料夾中自動展開完整的 12 週學習計畫、每日訓練素材、進度追蹤、模擬考、Anki 單字卡生成、TTS 聽力練習、口說評估、寫作批改。

## Install

```bash
npx skills add htlin222/toefl-skill
npx skills add -g htlin222/toefl-skill        # global
npx skills add htlin222/toefl-skill --agent claude-code  # specific agent
```

## What it does

一套 Claude Code 驅動的模組化 TOEFL 備考系統。本技能由 8 個獨立模組組成，採用 progressive disclosure——只在需要時才讀取對應模組。

## Skill structure

```
toefl/
├── references
│   ├── exam-format-2026.md
│   ├── high-score-patterns.md
│   ├── listening-guide.md
│   ├── reading-guide.md
│   ├── resources-guide.md
│   ├── scoring-rubrics.md
│   ├── speaking-guide.md
│   ├── study-plan-12week.md
│   ├── vocabulary-core.md
│   └── writing-guide.md
├── scripts
│   ├── adaptive.py
│   ├── audio_utils.py
│   ├── daily.py
│   ├── generate_anki.py
│   ├── generate_listening.py
│   ├── generate_reading.py
│   ├── generate_speaking.py
│   ├── generate_writing.py
│   ├── init.py
│   ├── mock_test.py
│   ├── progress.py
│   ├── scaffold.py
│   ├── setup_env.py
│   ├── speaking_coach.py
│   └── writing_grader.py
└── SKILL.md
```

## Protocol

This skill follows the [vercel-labs/skills](https://github.com/vercel-labs/skills) protocol.
Each push to `main` triggers a GitHub Action that packages the skill as a `.skill` file
and creates a release tagged with the commit SHA.

## License

MIT License
