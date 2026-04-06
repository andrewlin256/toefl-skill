# 閱讀模組使用指南

## 產生練習
```bash
uv run python scripts/generate_reading.py --type all --output ./reading/ --difficulty hard
```

## 題型與腳本對應
| 題型 | 參數 | 難度建議 |
|------|------|----------|
| Complete the Words | `--type complete-words` | Week 1-4: easy → Week 5+: hard |
| Read in Daily Life | `--type daily-life` | 全階段混合 |
| Academic Passage | `--type academic` | Week 5+: medium/hard |

## Claude 引導流程
1. 確認使用者本週進度（讀 progress.json）
2. 選擇對應難度的練習
3. 使用者作答後，逐題講解錯誤選項為何錯
4. Complete the Words 錯題 → 加入本週 Anki deck
5. 記錄正確率到 progress.json

## 高分要點
- 詳見 `references/high-score-patterns.md` 的閱讀段落
- Complete the Words 是拉分關鍵，需要 90%+ 正確率
- Academic Passage 推論題是 4.0 vs 5.0 的分水嶺
