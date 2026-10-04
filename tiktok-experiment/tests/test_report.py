from datetime import datetime

import pandas as pd

from tiktok_tracker import report, storage

from . import sample


def test_markdown_order_and_numbers():
    goals = storage.normalize("goals", pd.DataFrame([{
        "created_at": "2026-09-01", "metric": "再生数", "start_value": 1000,
        "current_value": 1500, "target_value": 3000, "deadline": "2026-12-31",
    }]))
    reviews = storage.normalize("reviews", pd.DataFrame([{
        "month": "2026-09", "worked_1": "冒頭で結論を出すと伸びた", "next_1": "冒頭の型を固定する",
    }]))
    md = report.build_markdown(sample.baseline(), goals, sample.posts(), reviews,
                               generated_at=datetime(2026, 10, 4))
    heads = ["## 1. ベースライン", "## 2. 目標", "## 3. 実施した施策", "## 4. 結果の数字", "## 5. 学び"]
    positions = [md.index(h) for h in heads]
    assert positions == sorted(positions)
    assert "**4本**" in md
    assert "| 直近10本の平均再生数 | 1,000回 | 1,500回 | +50.0% |" in md
    assert "達成率 50.0%" in md
    assert "冒頭で結論を出すと伸びた" in md
    assert "| 2026-09-03 | 冒頭1秒に結論 | 冒頭 | 仮説 | 1,500回 | +50.0% |" in md


def test_markdown_empty_data():
    empty = {n: storage.normalize(n, pd.DataFrame()) for n in ("baseline", "goals", "posts", "reviews")}
    md = report.build_markdown(empty["baseline"], empty["goals"], empty["posts"], empty["reviews"])
    assert "未登録" in md and "未設定" in md
