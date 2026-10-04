from datetime import date, datetime

import pandas as pd
import pytest

from tiktok_tracker import logic, storage

from . import sample


@pytest.mark.parametrize("text", ["", "   ", None])
def test_change_empty_warns(text):
    assert logic.check_change(text)


@pytest.mark.parametrize("text", ["冒頭を変えた、尺も短くした", "冒頭,尺", "冒頭，尺"])
def test_change_multiple_warns(text):
    assert "複数" in logic.check_change(text)[0]


def test_change_single_ok():
    assert logic.check_change("冒頭1秒に結論のテロップを入れた") == []


def test_pending_posts_ready_after_48h():
    posts = sample.posts()
    p = logic.pending_posts(posts, now=datetime(2026, 9, 25, 12, 0))
    assert list(p["id"]) == [4]
    assert not p.loc[0, "ready"]
    p = logic.pending_posts(posts, now=datetime(2026, 9, 26, 7, 0))
    assert p.loc[0, "ready"]
    assert p.loc[0, "missing"] == "再生数・視聴維持率(%)・保存数・いいね数"


def test_baseline_for_month():
    b = sample.baseline()
    assert logic.baseline_for_month(b, "2026-09")["date"] == "2026-09-01"
    assert logic.baseline_for_month(b, "2026-11")["date"] == "2026-10-01"
    # 月初以前の記録が無い月は最初の記録
    assert logic.baseline_for_month(b, "2026-08")["date"] == "2026-09-01"
    assert logic.baseline_for_month(storage.load("baseline").iloc[0:0], "2026-09") is None


def test_suggest_current_value():
    b = sample.baseline()
    assert logic.suggest_current_value("再生数", b) == 1500
    assert logic.suggest_current_value("視聴維持率", b) == 35
    assert logic.suggest_current_value("フォロワー増加数", b) == 300
    assert logic.suggest_current_value("フォロワー増加数", b, since="2026-10-02") == 0


def test_rates():
    assert logic.achievement_rate(1500, 3000) == 50
    assert logic.achievement_rate(1500, 0) is None
    assert logic.progress_rate(1000, 1500, 3000) == 25
    assert logic.progress_rate(1000, 1500, 1000) is None
    assert logic.days_left("2026-10-10", today=date(2026, 10, 4)) == 6


def test_category_summary_and_split():
    posts = logic.posts_in_month(sample.posts(), "2026-09")
    s = logic.category_summary(posts, 1000.0)
    assert list(s["変更カテゴリ"]) == ["冒頭", "尺"]  # 未入力の投稿時間は除外
    row = s[s["変更カテゴリ"] == "冒頭"].iloc[0]
    assert row["投稿数"] == 2 and row["平均再生数"] == 1400 and row["差(%)"] == 40.0

    worked, not_worked = logic.split_by_effect(posts, 1000.0, threshold=35)
    assert list(worked["id"]) == [1]
    assert list(not_worked["id"]) == [2, 3]  # 悪い順


def test_storage_roundtrip(data_dir):
    storage.save("posts", sample.posts())
    loaded = storage.load("posts")
    assert len(loaded) == 4
    assert pd.isna(loaded.loc[3, "views"])
    assert loaded.loc[0, "change"] == "冒頭1秒に結論"
    assert storage.next_post_id(loaded) == 5


def test_upsert_review():
    reviews = storage.load("reviews").iloc[0:0]
    reviews = logic.upsert_review(reviews, {"month": "2026-09", "worked_1": "a"})
    reviews = logic.upsert_review(reviews, {"month": "2026-09", "worked_1": "b"})
    assert len(reviews) == 1 and reviews.iloc[0]["worked_1"] == "b"
