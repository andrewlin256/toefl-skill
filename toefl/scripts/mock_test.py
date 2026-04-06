#!/usr/bin/env python3
"""
TOEFL 備考系統 — 模擬考模組 (mock_test.py)
產生並管理完整的 TOEFL 模擬考。

Usage:
    python mock_test.py --target ./toefl-prep/ --action create   # 產生新模擬考
    python mock_test.py --target ./toefl-prep/ --action score --test 1 --reading 4.5 --listening 5.0 --speaking 4.0 --writing 4.5
    python mock_test.py --target ./toefl-prep/ --action history   # 查看歷次成績
"""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path


def create_mock_test(target: str):
    """Create a new mock test directory with all sections."""
    mock_dir = os.path.join(target, "mock-tests")
    os.makedirs(mock_dir, exist_ok=True)

    # Find next test number
    existing = [d for d in os.listdir(mock_dir) if d.startswith("test-") and os.path.isdir(os.path.join(mock_dir, d))]
    test_num = len(existing) + 1
    test_dir = os.path.join(mock_dir, f"test-{test_num:02d}")
    os.makedirs(test_dir, exist_ok=True)

    # Create test instruction file
    instructions = f"""# 📝 TOEFL 模擬考 #{test_num}

**日期：** {datetime.now().strftime('%Y-%m-%d')}
**總時間：** 約 90 分鐘

---

## ⚙️ 考試前設定

- [ ] 找一個安靜的地方
- [ ] 準備好計時器
- [ ] 準備紙筆（聽力筆記用）
- [ ] 關閉手機通知

---

## 📖 Section 1: Reading（18–27 分鐘）

請告訴 Claude：「開始模擬考閱讀」

Claude 會產生：
- Complete the Words 題目
- Read in Daily Life 題目
- Academic Passage 題目

**重要：** 模擬 Module 1 → Module 2 的感覺。
前半段認真作答，正確率會影響後半段難度。

---

## 🎧 Section 2: Listening（18–27 分鐘）

請告訴 Claude：「開始模擬考聽力」

Claude 會產生音檔（需 edge-tts）或唸出內容：
- Choose a Response
- Conversations
- Announcements
- Academic Talks（如果進入 Hard 路線）

**重要：** 音檔只聽一次，不可倒帶。

---

## 🎤 Section 3: Speaking（約 10 分鐘）

請告訴 Claude：「開始模擬考口說」

- Listen & Repeat：7 句跟讀
- Take an Interview：4 題即興回答（每題 45 秒）

**重要：** 沒有準備時間！

---

## ✍️ Section 4: Writing（約 23 分鐘）

請告訴 Claude：「開始模擬考寫作」

- Build a Sentence：10 題（約 7 分鐘）
- Write an Email：1 題（7 分鐘）
- Academic Discussion：1 題（10 分鐘）

---

## 📊 考後評分

完成所有科目後，請告訴 Claude：「模擬考結束，幫我評分」

Claude 會：
1. 批改閱讀和聽力（客觀題）
2. 評估口說（依 rubric）
3. 批改寫作（依 rubric）
4. 產生成績報告
5. 更新 progress.json

---

## 📋 成績記錄

| 科目 | 分數 (1–6) | 備註 |
|------|-----------|------|
| Reading | | |
| Listening | | |
| Speaking | | |
| Writing | | |
| **Total** | | |

## 檢討筆記

### 做得好的：


### 需要改進的：


### 下次模擬考前要特別練習的：

"""

    with open(os.path.join(test_dir, "instructions.md"), "w", encoding="utf-8") as f:
        f.write(instructions)

    # Create section subdirectories
    for section in ["reading", "listening", "speaking", "writing"]:
        os.makedirs(os.path.join(test_dir, section), exist_ok=True)

    # Create result placeholder
    result = {
        "test_number": test_num,
        "date": datetime.now().isoformat(),
        "status": "in_progress",
        "scores": {
            "reading": None,
            "listening": None,
            "speaking": None,
            "writing": None,
            "total": None,
        },
        "notes": "",
    }
    with open(os.path.join(test_dir, "result.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"✅ 模擬考 #{test_num} 已建立：{test_dir}")
    print(f"   打開 instructions.md 開始考試")
    print(f"   或告訴 Claude：「開始模擬考」")
    return test_dir


def score_mock_test(target: str, test_num: int, reading: float, listening: float, speaking: float, writing: float):
    """Record scores for a mock test."""
    test_dir = os.path.join(target, "mock-tests", f"test-{test_num:02d}")
    result_path = os.path.join(test_dir, "result.json")

    if not os.path.exists(result_path):
        print(f"❌ 找不到模擬考 #{test_num}")
        return

    result = json.load(open(result_path, "r"))
    total = round((reading + listening + speaking + writing) / 4 * 2) / 2

    result["status"] = "completed"
    result["scores"] = {
        "reading": reading,
        "listening": listening,
        "speaking": speaking,
        "writing": writing,
        "total": total,
    }
    result["completed_date"] = datetime.now().isoformat()

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    # Update progress.json
    progress_path = os.path.join(target, "progress.json")
    if os.path.exists(progress_path):
        progress = json.load(open(progress_path, "r"))
        progress.setdefault("mock_tests", []).append({
            "test_number": test_num,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "reading": reading,
            "listening": listening,
            "speaking": speaking,
            "writing": writing,
            "total": total,
        })
        progress["latest_scores"] = {
            "reading": reading,
            "listening": listening,
            "speaking": speaking,
            "writing": writing,
            "total": total,
        }
        if len(progress["mock_tests"]) == 1:
            progress["baseline_scores"] = progress["latest_scores"].copy()

        progress["last_updated"] = datetime.now().isoformat()
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=2, ensure_ascii=False)

    # Print report
    print(f"\n📊 模擬考 #{test_num} 成績報告")
    print("=" * 40)
    print(f"  Reading:   {reading:.1f}")
    print(f"  Listening: {listening:.1f}")
    print(f"  Speaking:  {speaking:.1f}")
    print(f"  Writing:   {writing:.1f}")
    print(f"  ──────────────────")
    print(f"  Total:     {total:.1f}")
    print()

    # CEFR mapping
    if total >= 5.0:
        print("  CEFR: C1 — 流暢學術交流 🌟")
    elif total >= 4.0:
        print("  CEFR: B2 — 獨立使用者 👍")
    elif total >= 3.0:
        print("  CEFR: B1 — 中級 📚")
    else:
        print("  CEFR: A2/B1 — 需要更多練習 💪")

    # Weak area analysis
    scores = {"reading": reading, "listening": listening, "speaking": speaking, "writing": writing}
    weakest = min(scores, key=scores.get)
    strongest = max(scores, key=scores.get)
    print(f"\n  💪 最強科目：{strongest.capitalize()} ({scores[strongest]:.1f})")
    print(f"  ⚠️  最弱科目：{weakest.capitalize()} ({scores[weakest]:.1f})")
    print(f"  📌 建議：集中加強 {weakest.capitalize()}")


def show_history(target: str):
    """Show mock test history with trends."""
    progress_path = os.path.join(target, "progress.json")
    if not os.path.exists(progress_path):
        print("❌ 找不到 progress.json")
        return

    progress = json.load(open(progress_path, "r"))
    mocks = progress.get("mock_tests", [])

    if not mocks:
        print("📝 還沒有模擬考記錄。")
        print("   執行 mock_test.py --action create 開始第一次模擬考")
        return

    print("\n📊 模擬考歷史")
    print("=" * 65)
    print(f"{'#':<4} {'日期':<12} {'R':<6} {'L':<6} {'S':<6} {'W':<6} {'Total':<6}")
    print("-" * 65)

    for m in mocks:
        print(f"#{m['test_number']:<3} {m['date']:<12} {m['reading']:<6.1f} {m['listening']:<6.1f} {m['speaking']:<6.1f} {m['writing']:<6.1f} {m['total']:<6.1f}")

    if len(mocks) >= 2:
        first = mocks[0]
        last = mocks[-1]
        diff = last["total"] - first["total"]
        print(f"\n📈 進步幅度：{diff:+.1f}（第一次 {first['total']:.1f} → 最新 {last['total']:.1f}）")

        for section in ["reading", "listening", "speaking", "writing"]:
            s_diff = last[section] - first[section]
            emoji = "📈" if s_diff > 0 else "📉" if s_diff < 0 else "➡️"
            print(f"   {emoji} {section.capitalize()}: {s_diff:+.1f}")


def main():
    parser = argparse.ArgumentParser(description="TOEFL 模擬考模組")
    parser.add_argument("--target", default="./toefl-prep/")
    parser.add_argument("--action", choices=["create", "score", "history"], default="create")
    parser.add_argument("--test", type=int, help="Test number (for scoring)")
    parser.add_argument("--reading", type=float)
    parser.add_argument("--listening", type=float)
    parser.add_argument("--speaking", type=float)
    parser.add_argument("--writing", type=float)
    args = parser.parse_args()

    if args.action == "create":
        create_mock_test(args.target)
    elif args.action == "score":
        if all([args.test, args.reading, args.listening, args.speaking, args.writing]):
            score_mock_test(args.target, args.test, args.reading, args.listening, args.speaking, args.writing)
        else:
            print("❌ 需要提供：--test N --reading X --listening X --speaking X --writing X")
    elif args.action == "history":
        show_history(args.target)


if __name__ == "__main__":
    main()
