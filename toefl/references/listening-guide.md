# 聽力模組使用指南

## 產生練習
```bash
uv run python scripts/generate_listening.py --type all --output ./listening/ --difficulty hard
```

## 題型與腳本對應
| 題型 | 參數 | 音檔設計 |
|------|------|----------|
| Choose a Response | `--type choose-response` | 語句 → 2s 停頓 → beep |
| Conversation | `--type conversation` | 每句間 0.8s 停頓 |
| Announcement | `--type announcement` | 正式語速 -8% |
| Academic Talk | `--type academic` | [PAUSE] 標記 → 1.2s 自然停頓 |

## Claude 引導流程
1. 播放音檔前提醒：「只播放一次，做好筆記準備」
2. 播放後出題（題目在 questions.md）
3. 使用者作答後對答案，講解錯誤原因
4. 如有需要，提供逐字稿（transcript.md）讓使用者比對
5. 分析筆記問題：是聽力問題、還是題型理解問題、還是筆記不足？

## 筆記教學重點
- 用縮寫和符號，不逐字抄
- 記結構而非細節：主題 → 論點 → 例子 → 結論
- 特別注意結尾的「下次課」暗示
