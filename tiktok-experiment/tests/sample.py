"""テスト用のサンプルデータ。"""

import pandas as pd

from tiktok_tracker import storage


def baseline():
    return storage.normalize("baseline", pd.DataFrame([
        {"date": "2026-09-01", "followers": 1000, "avg_views": 1000, "avg_retention": 30, "avg_saves": 10},
        {"date": "2026-10-01", "followers": 1300, "avg_views": 1500, "avg_retention": 35, "avg_saves": 15},
    ]))


def posts():
    rows = [
        (1, "2026-09-03 19:00", "A", "冒頭1秒に結論", "冒頭", 1500, 40, 20, 100),
        (2, "2026-09-10 19:00", "B", "尺を15秒に", "尺", 800, 45, 5, 50),
        (3, "2026-09-17 21:00", "C", "冒頭に質問を置く", "冒頭", 1300, 38, 12, 80),
        (4, "2026-09-24 07:00", "D", "朝7時に投稿", "投稿時間", None, None, None, None),
    ]
    return storage.normalize("posts", pd.DataFrame([
        dict(id=i, posted_at=at, title=t, change=c, category=cat, hypothesis="仮説",
             views=v, retention=r, saves=s, likes=l, insight="")
        for i, at, t, c, cat, v, r, s, l in rows
    ]))
