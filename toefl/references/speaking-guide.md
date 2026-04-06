# 口說模組使用指南

## 產生練習
```bash
uv run python scripts/generate_speaking.py --type all --output ./speaking/
uv run python scripts/generate_speaking.py --type repeat --set 1   # 特定 Listen & Repeat set
uv run python scripts/generate_speaking.py --type interview         # Interview 練習
```

## 音檔結構（精確計時）

### Listen & Repeat
```
[0.5s 靜音] → [句子音檔] → [0.3s 靜音] → [BEEP 880Hz 250ms] → [錄音靜音 8-12s]
```
- Items 1-2: 8 秒錄音時間
- Items 3-5: 10 秒
- Items 6-7: 12 秒

### Interview
```
[介紹旁白] → [2s 靜音] → [問題音檔] → [0.5s 靜音] → [雙 BEEP] → [45s 錄音靜音] → [單 BEEP = 停止]
```

## Claude 評估流程（文字版回答）
1. 使用者提交文字版回答
2. 讀取 `references/scoring-rubrics.md` 的口說評分標準
3. 依照四維度評分：Fluency / Intelligibility / Language Use / Organization
4. 給出具體錯誤和修正建議
5. 提供模範回答參考

## Shadowing 練習建議素材
- TED-Ed (1-3 min): 清晰發音、學術主題
- BBC Learning English: 6 Minute English
- NPR Short Wave: 科學新聞 (2-3 min)
- 用 edge-tts 產生自定句子練習
