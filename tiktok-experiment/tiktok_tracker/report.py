"""ガクチカ素材（Markdown）の組み立て。

順番は「ベースライン → 目標 → 実施した施策 → 結果の数字 → 学び」。
"""

from datetime import datetime

import pandas as pd

from . import config, logic

_BASELINE_ROWS = [
    ("フォロワー数", "followers", "人", 0),
    ("直近10本の平均再生数", "avg_views", "回", 0),
    ("平均視聴維持率", "avg_retention", "%", 1),
    ("平均保存数", "avg_saves", "件", 1),
]


def _cell(text):
    """表のセルに入れても崩れないようにする。"""
    return str(text).replace("|", "／").replace("\n", " ").strip() or "—"


def build_markdown(baseline, goals, posts, reviews, generated_at=None):
    generated_at = generated_at or datetime.now()
    base = logic.sorted_baseline(baseline)
    first = base.iloc[0] if not base.empty else None
    last = base.iloc[-1] if not base.empty else None
    goal = logic.latest_goal(goals)
    done = posts.dropna(subset=["views"]).copy()

    out = [
        "# TikTok改善実験の記録（ガクチカ素材）",
        "",
        f"出力日: {generated_at:%Y-%m-%d}",
        "",
    ]

    # 1. ベースライン
    out += ["## 1. ベースライン（取り組み前の現状）", ""]
    if first is None:
        out += ["（ベースラインが未登録です）", ""]
    else:
        out += [f"記録日: {first['date']}", "", "| 指標 | 値 |", "|---|---|"]
        for label, col, unit, digits in _BASELINE_ROWS:
            out.append(f"| {label} | {logic.fmt(first[col], unit, digits)} |")
        out.append("")

    # 2. 目標
    out += ["## 2. 目標", ""]
    if goal is None:
        out += ["（目標が未設定です）", ""]
    else:
        unit, digits = config.GOAL_METRICS.get(goal["metric"], ("", 0))
        rate = logic.achievement_rate(goal["current_value"], goal["target_value"])
        out += [
            f"- 指標: **{goal['metric']}**",
            f"- 設定時の値: {logic.fmt(goal['start_value'], unit, digits)}"
            f" → 目標値: **{logic.fmt(goal['target_value'], unit, digits)}**"
            f"（期限: {goal['deadline']}）",
            f"- 現在値: {logic.fmt(goal['current_value'], unit, digits)}"
            f"（達成率 {logic.fmt_pct(rate, signed=False)}）",
            "",
        ]

    # 3. 実施した施策
    out += ["## 3. 実施した施策（1投稿につき変更は1つ）", ""]
    if posts.empty:
        out += ["（投稿ログがありません）", ""]
    else:
        counts = posts["category"].value_counts()
        dates = posts["posted_at"].map(logic.parse_posted_at).dropna()
        period = f"{min(dates):%Y-%m-%d}〜{max(dates):%Y-%m-%d}" if len(dates) else "—"
        out += [
            f"期間 {period} に **{len(posts)}本** の検証投稿を行った。",
            "",
            "カテゴリ別の本数: "
            + "、".join(f"{c} {counts[c]}本" for c in config.CATEGORIES if c in counts),
            "",
            "| 投稿日 | 今回変えた点 | カテゴリ | 仮説 | 再生数 | ベースライン比 |",
            "|---|---|---|---|---|---|",
        ]
        for _, p in posts.sort_values("posted_at").iterrows():
            month = logic.post_month(p["posted_at"])
            b = logic.baseline_for_month(baseline, month) if month else None
            d = logic.diff_pct(p["views"], b["avg_views"]) if b is not None else None
            out.append(
                f"| {_cell(str(p['posted_at'])[:10])} | {_cell(p['change'])} | {_cell(p['category'])}"
                f" | {_cell(p['hypothesis'])} | {logic.fmt(p['views'], '回')} | {logic.fmt_pct(d)} |"
            )
        out.append("")

    # 4. 結果の数字
    out += ["## 4. 結果の数字", ""]
    if first is not None and last is not None and len(base) >= 2:
        out += [
            f"ベースライン（{first['date']}）と最新の記録（{last['date']}）の比較:",
            "",
            "| 指標 | 開始時 | 最新 | 変化 |",
            "|---|---|---|---|",
        ]
        for label, col, unit, digits in _BASELINE_ROWS:
            change = logic.diff_pct(last[col], first[col])
            out.append(
                f"| {label} | {logic.fmt(first[col], unit, digits)} | {logic.fmt(last[col], unit, digits)}"
                f" | {logic.fmt_pct(change)} |"
            )
        out.append("")
    else:
        out += ["（ベースラインを2回以上記録すると、開始時と最新の比較が入ります）", ""]

    if first is not None and not done.empty:
        summary = logic.category_summary(done, first["avg_views"])
        summary = summary.sort_values("差(%)", ascending=False, na_position="last")
        out += [
            f"変更カテゴリ別の平均再生数（開始時の平均 {logic.fmt(first['avg_views'], '回')} と比較）:",
            "",
            "| カテゴリ | 投稿数 | 平均再生数 | 開始時比 |",
            "|---|---|---|---|",
        ]
        for _, r in summary.iterrows():
            out.append(
                f"| {r['変更カテゴリ']} | {int(r['投稿数'])} | {logic.fmt(r['平均再生数'], '回')}"
                f" | {logic.fmt_pct(r['差(%)'])} |"
            )
        out.append("")

    if not done.empty:
        best = done.sort_values("views", ascending=False).iloc[0]
        out += [
            f"最も再生された投稿: 「{best['title']}」"
            f"（{logic.fmt(best['views'], '回')}／変えた点: {best['change']}）",
            "",
        ]

    # 5. 学び
    out += ["## 5. 学び", ""]
    wrote = False
    for _, r in reviews.sort_values("month").iterrows():
        sections = [
            ("効いた施策", logic.review_lines(r, "worked")),
            ("効かなかった施策", logic.review_lines(r, "not_worked")),
            ("次に試すこと", logic.review_lines(r, "next")),
        ]
        if not any(lines for _, lines in sections):
            continue
        wrote = True
        out += [f"### {r['month']} の振り返り", ""]
        for title, lines in sections:
            if lines:
                out.append(f"**{title}**")
                out += [f"- {line}" for line in lines]
                out.append("")
    insights = posts[posts["insight"].str.strip() != ""].sort_values("posted_at")
    if not insights.empty:
        wrote = True
        out += ["### 投稿ごとの気づき", ""]
        out += [
            f"- {str(p['posted_at'])[:10]}（{p['change'] or '変更点未記入'}）: {p['insight']}"
            for _, p in insights.iterrows()
        ]
        out.append("")
    if not wrote:
        out += ["（月次振り返りや投稿の「気づき」を入力すると、ここに入ります）", ""]

    # 面接用の下書き
    out += ["## 面接で話すときの骨子（下書き）", ""]
    out += [_pitch(first, last, goal, posts, len(base))]
    out.append("")
    return "\n".join(out)


def _pitch(first, last, goal, posts, n_baseline):
    parts = []
    if first is not None:
        parts.append(
            f"フォロワー{logic.fmt(first['followers'], '人')}・平均再生{logic.fmt(first['avg_views'], '回')}"
            "の状態から、"
        )
    if goal is not None:
        unit, digits = config.GOAL_METRICS.get(goal["metric"], ("", 0))
        parts.append(
            f"「{goal['metric']}を{logic.fmt(goal['target_value'], unit, digits)}にする」という目標を立て、"
        )
    parts.append(f"1投稿につき変更を1つに絞るルールで{len(posts)}本の仮説検証を行った。")
    if first is not None and last is not None and n_baseline >= 2:
        change = logic.diff_pct(last["avg_views"], first["avg_views"])
        parts.append(
            f"その結果、平均再生数は{logic.fmt(first['avg_views'], '回')}から"
            f"{logic.fmt(last['avg_views'], '回')}（{logic.fmt_pct(change)}）になった。"
        )
    return "".join(parts)
