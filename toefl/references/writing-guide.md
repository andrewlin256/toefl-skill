# 寫作模組使用指南

## 產生練習
```bash
uv run python scripts/generate_writing.py --type all --output ./writing/
uv run python scripts/generate_writing.py --type build-sentence
uv run python scripts/generate_writing.py --type email
uv run python scripts/generate_writing.py --type discussion
```

## Claude 批改流程

### Build a Sentence
1. 出題（從腳本內建題庫或 Claude 即時產生）
2. 使用者排列單字
3. 比對正確答案：全對 1 分，有誤 0 分
4. 講解文法考點（關係子句、間接問句、倒裝等）

### Write an Email（7 分鐘計時）
1. 顯示題目（scenario + 3 bullets）
2. 使用者寫完後提交
3. 讀取 `references/scoring-rubrics.md` 的 Email 評分標準
4. 逐一檢查：3 個要點是否都有回應、語氣是否得體、文法錯誤列表
5. 給出 0-5 分 + 各維度分數 + 具體修改建議
6. 如有範例回答，提供比較

### Academic Discussion（10 分鐘計時）
1. 顯示教授問題 + 兩位學生回覆
2. 使用者寫回應
3. 檢查重點：是否有新論點？是否回應了其他學生？字數夠嗎？
4. 給出 0-5 分 + 修改建議

## 批改輸出格式
使用 `references/scoring-rubrics.md` 中定義的標準格式。
