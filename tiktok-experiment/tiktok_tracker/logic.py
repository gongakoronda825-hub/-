"""画面から切り離した計算処理。ここだけで単体テストできるようにしてある。"""

import re
from datetime import date, datetime

import pandas as pd

from . import config

# 「1投稿で変えるのは1つだけ」を破っていそうな区切り
_MULTI_CHANGE = re.compile(r"[、，,]")


# ---------- 投稿ログ ----------

def check_change(text):
    """「今回変えた点」の書き方をチェックし、警告文のリストを返す（問題なければ空）。"""
    text = (text or "").strip()
    if not text:
        return ["「今回変えた点」が空欄です。何を1つ変えたのかを書いてください。"]
    if _MULTI_CHANGE.search(text):
        return [
            "「今回変えた点」に読点（、）があり、複数の変更が書かれているようです。"
            "変える点を1つに絞ると、何が効いたのかを説明できます。"
        ]
    return []


def parse_posted_at(value):
    """'YYYY-MM-DD HH:MM' または 'YYYY-MM-DD' を datetime に。読めなければ None。"""
    ts = pd.to_datetime(value, errors="coerce")
    return None if pd.isna(ts) else ts.to_pydatetime()


def pending_posts(posts, now=None):
    """数値が未入力の投稿を返す。hours_since（経過時間）と ready（48時間経過）列を付ける。"""
    now = now or datetime.now()
    missing = posts[config.POST_METRIC_COLUMNS].isna().any(axis=1)
    df = posts[missing].copy()
    posted = df["posted_at"].map(parse_posted_at)
    df["hours_since"] = [
        None if p is None else (now - p).total_seconds() / 3600 for p in posted
    ]
    df["ready"] = [
        h is not None and h >= config.RESULT_WAIT_HOURS for h in df["hours_since"]
    ]
    df["missing"] = [
        "・".join(config.LABELS[c] for c in config.POST_METRIC_COLUMNS if pd.isna(row[c]))
        for _, row in df.iterrows()
    ]
    return df.sort_values("posted_at").reset_index(drop=True)


def post_month(posted_at):
    p = parse_posted_at(posted_at)
    return None if p is None else p.strftime("%Y-%m")


# ---------- ベースライン ----------

def sorted_baseline(baseline):
    df = baseline.copy()
    df["_date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.dropna(subset=["_date"]).sort_values("_date").reset_index(drop=True)


def baseline_for_month(baseline, month):
    """その月の比較に使うベースライン（月初以前で最新のもの。無ければ最初の記録）。"""
    df = sorted_baseline(baseline)
    if df.empty:
        return None
    month_start = pd.Timestamp(f"{month}-01")
    before = df[df["_date"] <= month_start]
    row = before.iloc[-1] if not before.empty else df.iloc[0]
    return row.drop(labels="_date")


# ---------- 目標 ----------

def suggest_current_value(metric, baseline, since=None):
    """記録済みのベースラインから、目標指標の「現在値」の候補を出す。"""
    df = sorted_baseline(baseline)
    if df.empty:
        return None
    latest = df.iloc[-1]
    if metric == "再生数":
        return _num(latest["avg_views"])
    if metric == "視聴維持率":
        return _num(latest["avg_retention"])
    if metric == "保存数":
        return _num(latest["avg_saves"])
    if metric == "フォロワー増加数":
        start = df.iloc[0]
        if since:
            before = df[df["_date"] <= pd.Timestamp(since)]
            if not before.empty:
                start = before.iloc[-1]
        if pd.isna(latest["followers"]) or pd.isna(start["followers"]):
            return None
        return float(latest["followers"] - start["followers"])
    raise ValueError(metric)


def achievement_rate(current, target):
    """達成率(%) = 現在値 ÷ 目標値。"""
    if current is None or target is None or pd.isna(current) or pd.isna(target) or target <= 0:
        return None
    return current / target * 100


def progress_rate(start, current, target):
    """伸び幅ベースの進捗(%) = (現在値 - 設定時の値) ÷ (目標値 - 設定時の値)。"""
    values = (start, current, target)
    if any(v is None or pd.isna(v) for v in values) or target == start:
        return None
    return (current - start) / (target - start) * 100


def days_left(deadline, today=None):
    today = today or date.today()
    d = pd.to_datetime(deadline, errors="coerce")
    return None if pd.isna(d) else (d.date() - today).days


def latest_goal(goals):
    if goals.empty:
        return None
    return goals.sort_values("created_at").iloc[-1]


# ---------- 月次振り返り ----------

def posts_in_month(posts, month):
    months = posts["posted_at"].map(post_month)
    return posts[months == month].copy()


def available_months(posts, today=None):
    today = today or date.today()
    months = {m for m in posts["posted_at"].map(post_month) if m}
    months.add(today.strftime("%Y-%m"))
    return sorted(months, reverse=True)


def diff_pct(value, base):
    if value is None or base is None or pd.isna(value) or pd.isna(base) or base == 0:
        return None
    return (value - base) / base * 100


def category_summary(month_posts, base_views):
    """変更カテゴリごとの平均再生数をベースラインと比べた表。再生数未入力の投稿は除く。"""
    df = month_posts.dropna(subset=["views"])
    if df.empty:
        return pd.DataFrame(
            columns=["変更カテゴリ", "投稿数", "平均再生数", "ベースライン", "差", "差(%)",
                     "平均視聴維持率(%)", "平均保存数"]
        )
    g = df.groupby("category", sort=False).agg(
        n=("views", "size"),
        views=("views", "mean"),
        retention=("retention", "mean"),
        saves=("saves", "mean"),
    )
    order = {c: i for i, c in enumerate(config.CATEGORIES)}
    g = g.sort_index(key=lambda idx: idx.map(lambda c: order.get(c, len(order))))
    out = pd.DataFrame({
        "変更カテゴリ": g.index,
        "投稿数": g["n"].to_numpy(),
        "平均再生数": g["views"].round(0).to_numpy(),
        "ベースライン": base_views,
        "差": (g["views"] - base_views).round(0).to_numpy() if base_views is not None else None,
        "差(%)": [_round(diff_pct(v, base_views), 1) for v in g["views"]],
        "平均視聴維持率(%)": g["retention"].round(1).to_numpy(),
        "平均保存数": g["saves"].round(1).to_numpy(),
    })
    return out.reset_index(drop=True)


def split_by_effect(month_posts, base_views, threshold=config.DEFAULT_EFFECT_THRESHOLD):
    """投稿（=施策）ごとにベースライン比を出し、効いた / 効かなかったに分ける。

    ベースライン比が +threshold% 以上なら「効いた」、それ未満は「効かなかった」。
    """
    df = month_posts.dropna(subset=["views"]).copy()
    df["diff_pct"] = [diff_pct(v, base_views) for v in df["views"]]
    df = df.dropna(subset=["diff_pct"]).sort_values("diff_pct", ascending=False)
    worked = df[df["diff_pct"] >= threshold].reset_index(drop=True)
    not_worked = df[df["diff_pct"] < threshold].sort_values("diff_pct").reset_index(drop=True)
    return worked, not_worked


def review_lines(review, prefix):
    """保存済み振り返りから、空でない行だけを返す。"""
    if review is None:
        return []
    return [review[f"{prefix}_{i}"] for i in (1, 2, 3) if str(review[f"{prefix}_{i}"]).strip()]


def find_review(reviews, month):
    hit = reviews[reviews["month"] == month]
    return None if hit.empty else hit.iloc[-1]


def upsert_review(reviews, row):
    rest = reviews[reviews["month"] != row["month"]]
    new = pd.DataFrame([row])
    out = new if rest.empty else pd.concat([rest, new], ignore_index=True)
    return out.sort_values("month").reset_index(drop=True)


# ---------- 表示用 ----------

def fmt(value, unit="", digits=0):
    if value is None or pd.isna(value):
        return "—"
    text = f"{value:,.{digits}f}"
    return f"{text}{unit}"


def fmt_pct(value, signed=True):
    if value is None or pd.isna(value):
        return "—"
    return f"{value:+.1f}%" if signed else f"{value:.1f}%"


def _num(v):
    return None if pd.isna(v) else float(v)


def _round(v, digits):
    return None if v is None else round(v, digits)
