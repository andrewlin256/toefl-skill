---
name: toefl
description: >
  TOEFL iBT 2026 備考教練與學習系統。在空白資料夾中自動展開完整的 12 週學習計畫、
  每日訓練素材、進度追蹤、模擬考、Anki 單字卡生成、TTS 聽力練習、口說評估、寫作批改。
  當使用者提到 TOEFL、托福、英語檢定備考、英文考試準備、托福口說練習、托福寫作批改、
  托福聽力訓練、托福閱讀練習、托福模擬考、TOEFL mock test、TOEFL study plan、
  /toefl、或任何與 TOEFL 考試相關的學習需求時，務必觸發此技能。
  即使使用者只是說「幫我準備英文考試」或「我要考托福」也應觸發。
---

# TOEFL iBT 2026 備考教練

一套 Claude Code 驅動的模組化 TOEFL 備考系統。

## 模組總覽

本技能由 8 個獨立模組組成，採用 progressive disclosure——只在需要時才讀取對應模組。

```
toefl/
├── SKILL.md                          ← 你現在在這裡（路由器）
├── scripts/
│   ├── init.py                       ← 🏁 初始化模組
│   ├── daily.py                      ← 📅 每日追蹤模組
│   ├── scaffold.py                   ← 🔧 資料夾結構產生器（由 init.py 呼叫）
│   ├── progress.py                   ← 📊 進度追蹤與統計
│   ├── adaptive.py                   ← 🧠 自適應引擎（動態調整難度與時間分配）
│   ├── speaking_coach.py             ← 🎤 口說教練模組
│   ├── writing_grader.py             ← ✍️ 寫作批改模組
│   ├── mock_test.py                  ← 📝 模擬考模組
│   ├── generate_listening.py         ← 🎧 聽力素材產生器
│   └── generate_anki.py              ← 📚 Anki 單字卡產生器
└── references/
    ├── exam-format-2026.md           ← 📋 2026 新制完整格式
    ├── study-plan-12week.md          ← 📅 12 週計畫模板
    ├── scoring-rubrics.md            ← 📏 ETS 評分標準
    ├── vocabulary-core.md            ← 📖 核心學術字彙
    └── resources-guide.md            ← 🔗 備考素材完整指南（官方+免費+工具）
```

---

## 路由邏輯

根據使用者的意圖，選擇對應模組：

### 🏁 首次使用 / 初始化
**觸發詞：** `/toefl`、「開始準備托福」、「建立學習計畫」、初次進入空白資料夾
**動作：**
1. 執行 `scripts/init.py`（引導問卷 → 產生 config → 建立資料夾 → 產生診斷考）
2. 如果非互動環境，用 `--non-interactive` 搭配參數

```bash
python scripts/init.py --target .
# 或非互動模式
python scripts/init.py --target . --non-interactive --target-score 5.0 --exam-date 2026-07-15
```

### 📅 每日進入 / 今天練什麼
**觸發詞：** 「今天練什麼」、「開始練習」、進入已初始化的資料夾
**動作：**
1. 執行 `scripts/daily.py --target ./toefl-prep/`
2. 顯示今日任務、連續天數、倒數計時
3. 引導完成各項練習

```bash
python scripts/daily.py --target ./toefl-prep/           # 顯示今日任務
python scripts/daily.py --target ./toefl-prep/ --complete  # 標記完成
python scripts/daily.py --target ./toefl-prep/ --advance   # 推進下一天
python scripts/daily.py --target ./toefl-prep/ --status    # 本週總覽
```

### 📊 看進度 / 弱項分析
**觸發詞：** 「看進度」、「我的成績」、「弱項分析」
**動作：** 執行 `scripts/progress.py --action show --target ./toefl-prep/`

```bash
python scripts/progress.py --action show --target ./toefl-prep/
python scripts/progress.py --action log --target ./toefl-prep/ --minutes 30 --section reading --score 4.5
```

### 🎤 口說練習
**觸發詞：** 「口說練習」、「練口說」、「speaking practice」
**動作：**
1. 執行 `scripts/speaking_coach.py` 產生題目
2. 如需音檔，執行 `scripts/generate_listening.py --type repeat` 產生 TTS
3. 使用者完成後，讀取 `references/scoring-rubrics.md` 的口說段落進行評估

```bash
python scripts/speaking_coach.py --type full --output ./toefl-prep/speaking/
python scripts/speaking_coach.py --type repeat --output ./toefl-prep/speaking/
python scripts/speaking_coach.py --type interview --output ./toefl-prep/speaking/ --topic technology
```

**Claude 評估口說回答時：**
- 讀取 `references/scoring-rubrics.md` 的 Speaking 段落
- Listen & Repeat：檢查 Repeat Accuracy / Fluency / Intelligibility
- Interview：檢查 Fluency / Intelligibility / Language Use / Organization
- 使用標準回饋格式（rubric 檔案底部有模板）

### ✍️ 寫作練習 / 批改
**觸發詞：** 「寫作練習」、「批改我的寫作」、「練寫作」、「writing practice」
**動作：**
1. 執行 `scripts/writing_grader.py` 產生題目
2. 使用者完成後，讀取 `references/scoring-rubrics.md` 的寫作段落進行批改

```bash
python scripts/writing_grader.py --type full --output ./toefl-prep/writing/
python scripts/writing_grader.py --type sentence --output ./toefl-prep/writing/ --count 10
python scripts/writing_grader.py --type email --output ./toefl-prep/writing/
python scripts/writing_grader.py --type discussion --output ./toefl-prep/writing/
```

**Claude 批改寫作時：**
- 讀取 `references/scoring-rubrics.md` 的 Writing 段落
- Email：檢查是否涵蓋所有要點 / 語氣 / 文法 / 拼字
- Discussion：檢查觀點 / 論證 / 回應他人 / 文法
- 使用標準回饋格式（列出具體錯誤 + 修正 + 模範回答）

### 🎧 聽力練習
**觸發詞：** 「聽力練習」、「練聽力」、「listening practice」
**動作：** 執行 `scripts/generate_listening.py` 產生音檔和練習題

```bash
python scripts/generate_listening.py --type all --output ./toefl-prep/listening/
python scripts/generate_listening.py --type conversation --output ./toefl-prep/listening/
python scripts/generate_listening.py --type academic --output ./toefl-prep/listening/
```

**依賴：** `pip install edge-tts`

### 📚 單字 / Anki
**觸發詞：** 「背單字」、「產生 Anki」、「vocabulary」、「單字卡」
**動作：**
1. 讀取 `references/vocabulary-core.md` 選擇本週單字
2. 執行 `scripts/generate_anki.py` 產生 .apkg

### 📖 推薦素材 / 該用什麼來練
**觸發詞：** 「推薦素材」、「該看什麼」、「有什麼資源」、「練習素材」、「怎麼找聽力材料」
**動作：** 讀取 `references/resources-guide.md`，根據使用者的程度和弱項推薦對應素材

resources-guide.md 包含：
- 官方 ETS 資源（模擬考、Interactive Sampler）
- 模擬考平台比較（Magoosh、BestMyTest、TestSucceed 等）
- 各科素材來源（按難度分級 Lv1–5）
- Podcast 推薦（入門/中級/進階）
- YouTube 頻道推薦
- 開源工具鏈（edge-tts 語音選擇、語速調整指令）
- 每週素材排程建議
- 避免使用的過時資源清單

```bash
python scripts/generate_anki.py --output ./toefl-prep/vocabulary/anki-decks/ --week 1
```

**依賴：** `pip install genanki`

### 🧠 自適應調整 / 弱項分析
**觸發詞：** 「弱項分析」、「調整計畫」、「重新平衡」、「難度調整」、「里程碑檢查」
**動作：** 執行 `scripts/adaptive.py`

```bash
python scripts/adaptive.py --target ./toefl-prep/ --action analyze     # 完整分析報告
python scripts/adaptive.py --target ./toefl-prep/ --action rebalance   # 重新分配時間
python scripts/adaptive.py --target ./toefl-prep/ --action difficulty  # 建議難度等級
python scripts/adaptive.py --target ./toefl-prep/ --action checkpoint  # 里程碑檢查
```

**自適應引擎做什麼：**
- 從 progress.json 和模擬考數據計算各科差距（gap = 目標分數 - 現有分數）
- 差距越大的科目 → 分配更多每日練習時間（最高 45%，最低 10%）
- 根據現有分數推薦題目難度等級（Lv1 基礎 ~ Lv5 高級）
- 偵測分數下降趨勢 → 發出警告
- 各科差距 > 1.5 分 → 判定嚴重不平衡，建議集中補強
- 產生 adaptive.json 供其他模組讀取
- 里程碑檢查（25%/50%/75%/100% 進度點）

**daily.py 整合：** 
daily.py 會自動讀取 adaptive.json（如存在），用自適應建議替換固定計畫。

**何時觸發 rebalance：**
- 每次模擬考後自動建議
- 使用者主動要求
- 里程碑檢查未通過時

### 📝 模擬考
**觸發詞：** 「模擬考」、「mock test」、「做一次完整測驗」
**動作：**
1. 執行 `scripts/mock_test.py --action create` 建立考試資料夾
2. 按科目順序引導考試（R → L → S → W）
3. 各科目使用對應模組產生題目
4. 完成後評分並更新 progress.json

```bash
python scripts/mock_test.py --target ./toefl-prep/ --action create
python scripts/mock_test.py --target ./toefl-prep/ --action score --test 1 --reading 4.5 --listening 5.0 --speaking 4.0 --writing 4.5
python scripts/mock_test.py --target ./toefl-prep/ --action history
```

---

## 工具鏈

| 工具 | 用途 | 安裝 | 必要性 |
|------|------|------|--------|
| `edge-tts` | TTS 聽力素材 + 跟讀音檔 | `pip install edge-tts` | 聽力/口說必要 |
| `genanki` | Anki 單字卡 .apkg | `pip install genanki` | 單字功能必要 |
| `Kokoro TTS` | 離線高品質 TTS | `pip install kokoro` | 選用（替代 edge-tts） |

---

## 2026 新制速查

需要詳細資訊時，讀取 `references/exam-format-2026.md`。

**計分：** 1.0–6.0（CEFR 對齊），總分 = 四科平均
**自適應：** R/L 的 Module 1 表現決定 Module 2 難度（Hard path 上限 6.0 / Easy path 上限 4.0）

| 科目 | 時間 | 題型 |
|------|------|------|
| Reading | 18–27 min | Complete Words / Daily Life / Academic Passage |
| Listening | 18–27 min | Choose Response / Conversations / Announcements / Academic Talks |
| Speaking | ~10 min | Listen & Repeat (7) + Interview (4)，全 AI 評分 |
| Writing | ~23 min | Build a Sentence (10) + Email (1) + Discussion (1) |

---

## Claude 行為準則

1. **首次進入：** 檢查 toefl-prep/config.json 是否存在。不存在 → 跑 init.py。存在 → 跑 daily.py。
2. **Progressive disclosure：** 不要一次讀取所有 reference 檔案。只在需要時才讀取對應段落。
3. **語言：** 預設用繁體中文與使用者溝通，但所有 TOEFL 練習內容用英文。
4. **批改時：** 一定要讀取 `references/scoring-rubrics.md` 再評分，確保標準一致。
5. **鼓勵：** 保持正面態度，強調進步而非缺點。每次練習結束給出 1–2 個具體改進建議。
6. **追蹤：** 每次練習後提醒使用者更新 progress.json（或自動幫他更新）。
