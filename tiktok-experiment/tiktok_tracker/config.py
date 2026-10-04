"""アプリ全体で使う定数（CSVの列、カテゴリ、指標など）。"""

import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent

# テストなどで保存先を差し替えられるようにしておく
DATA_DIR = Path(os.environ.get("TIKTOK_TRACKER_DATA_DIR", APP_DIR / "data"))
EXPORT_DIR = Path(os.environ.get("TIKTOK_TRACKER_EXPORT_DIR", APP_DIR / "exports"))

CATEGORIES = ["冒頭", "尺", "投稿時間", "ハッシュタグ", "テーマ", "その他"]

# 目標に選べる指標 → (単位, 小数点以下の桁数)
GOAL_METRICS = {
    "再生数": ("回", 0),
    "視聴維持率": ("%", 1),
    "保存数": ("件", 1),
    "フォロワー増加数": ("人", 0),
}

# 投稿48時間後に入力する数値
POST_METRIC_COLUMNS = ["views", "retention", "saves", "likes"]
RESULT_WAIT_HOURS = 48

# 月次振り返りで「効いた」とみなす、ベースライン比の既定しきい値（%）
DEFAULT_EFFECT_THRESHOLD = 10

# テーブル名 → (ファイル名, 列, 数値列)
TABLES = {
    "baseline": (
        "baseline.csv",
        ["date", "followers", "avg_views", "avg_retention", "avg_saves"],
        ["followers", "avg_views", "avg_retention", "avg_saves"],
    ),
    "goals": (
        "goals.csv",
        ["created_at", "metric", "start_value", "current_value", "target_value", "deadline"],
        ["start_value", "current_value", "target_value"],
    ),
    "posts": (
        "posts.csv",
        [
            "id", "posted_at", "title", "change", "category", "hypothesis",
            "views", "retention", "saves", "likes", "insight",
        ],
        ["id", "views", "retention", "saves", "likes"],
    ),
    "reviews": (
        "reviews.csv",
        ["month"]
        + [f"worked_{i}" for i in (1, 2, 3)]
        + [f"not_worked_{i}" for i in (1, 2, 3)]
        + [f"next_{i}" for i in (1, 2, 3)]
        + ["saved_at"],
        [],
    ),
}

# 画面に出すときの列名
LABELS = {
    "date": "日付",
    "followers": "フォロワー数",
    "avg_views": "平均再生数",
    "avg_retention": "平均視聴維持率(%)",
    "avg_saves": "平均保存数",
    "id": "ID",
    "posted_at": "投稿日時",
    "title": "動画タイトル",
    "change": "今回変えた点",
    "category": "変更カテゴリ",
    "hypothesis": "仮説",
    "views": "再生数",
    "retention": "視聴維持率(%)",
    "saves": "保存数",
    "likes": "いいね数",
    "insight": "気づき",
}
