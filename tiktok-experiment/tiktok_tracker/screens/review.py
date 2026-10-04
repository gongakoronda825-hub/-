"""画面4: 月次振り返り"""

from datetime import datetime

import streamlit as st

from .. import config, logic, storage
from ._common import flash, show_flash


def render():
    st.title("④ 月次振り返り")
    st.caption("変更カテゴリごとの平均再生数を、その月のベースラインと比べます。")
    show_flash()

    baseline = storage.load("baseline")
    posts = storage.load("posts")
    reviews = storage.load("reviews")

    c1, c2 = st.columns([1, 2])
    months = logic.available_months(posts)
    with_posts = {logic.post_month(x) for x in posts["posted_at"]}
    default = next((i for i, m in enumerate(months) if m in with_posts), 0)
    month = c1.selectbox("振り返る月", months, index=default)
    threshold = c2.slider(
        "「効いた」とみなすライン（ベースライン比 何%以上）", 0, 50, config.DEFAULT_EFFECT_THRESHOLD, step=5,
    )

    base = logic.baseline_for_month(baseline, month)
    month_posts = logic.posts_in_month(posts, month)
    measured = month_posts.dropna(subset=["views"])

    if base is None:
        st.warning("ベースラインが未登録のため比較できません。①でベースラインを登録してください。")
        base_views = None
    else:
        base_views = float(base["avg_views"])
        st.markdown(
            f"比較に使うベースライン: **{base['date']}** の記録（平均再生数 "
            f"**{logic.fmt(base_views, '回')}**、視聴維持率 {logic.fmt(base['avg_retention'], '%', 1)}、"
            f"保存数 {logic.fmt(base['avg_saves'], '件', 1)}）"
        )
        st.caption("月初以前で最新のベースラインを使います（無ければ最初の記録）。")

    st.markdown(f"この月の投稿: **{len(month_posts)}本**（数値入力済み {len(measured)}本）")
    if len(month_posts) > len(measured):
        st.caption("再生数が未入力の投稿は集計から外しています。③投稿ログで入力できます。")

    worked = not_worked = None
    if base_views is not None and not measured.empty:
        summary = logic.category_summary(measured, base_views)
        st.subheader("変更カテゴリ別の平均再生数")
        st.dataframe(
            summary, hide_index=True, width="stretch",
            column_config={
                "平均再生数": st.column_config.NumberColumn(format="%d"),
                "ベースライン": st.column_config.NumberColumn(format="%d"),
                "差": st.column_config.NumberColumn(format="%+d"),
                "差(%)": st.column_config.NumberColumn(format="%+.1f%%"),
            },
        )
        st.caption("ベースライン比（%）。0より右なら、ベースラインより再生された。")
        st.bar_chart(summary.set_index("変更カテゴリ")[["差(%)"]], horizontal=True, height=60 + 40 * len(summary))
        if (summary["投稿数"] < 2).any():
            st.caption("※ 投稿数が1本のカテゴリは偶然の影響が大きいので、結論は控えめに。")

        worked, not_worked = logic.split_by_effect(measured, base_views, threshold)
        st.subheader("施策ごとの結果（自動）")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"##### ✅ 効いた施策（+{threshold}%以上）")
            _effect_list(worked)
        with c2:
            st.markdown(f"##### ❌ 効かなかった施策（+{threshold}%未満）")
            _effect_list(not_worked)
    elif base_views is not None:
        st.info("この月に数値入力済みの投稿がありません。")

    st.divider()
    _review_form(reviews, month, worked, not_worked)


def _effect_list(df):
    if df is None or df.empty:
        st.caption("該当なし")
        return
    for _, p in df.iterrows():
        st.markdown(
            f"- **{p['change'] or '（変えた点 未記入）'}**［{p['category']}］ "
            f"{logic.fmt(p['views'], '回')}（{logic.fmt_pct(p['diff_pct'])}）"
        )


def _review_form(reviews, month, worked, not_worked):
    st.subheader(f"{month} の振り返りを書く")
    saved = logic.find_review(reviews, month)
    if saved is not None:
        st.caption(f"保存済み（{saved['saved_at']}）。書き換えて保存すると上書きされます。")

    hints = {
        "worked": _hints(worked),
        "not_worked": _hints(not_worked),
        "next": [],
    }
    sections = [
        ("worked", "✅ 効いた施策"),
        ("not_worked", "❌ 効かなかった施策"),
        ("next", "🧪 来月試すこと"),
    ]
    row = {"month": month}
    cols = st.columns(3)
    for (prefix, title), col in zip(sections, cols):
        with col:
            st.markdown(f"**{title}**")
            for i in (1, 2, 3):
                hint = hints[prefix][i - 1] if len(hints[prefix]) >= i else ""
                row[f"{prefix}_{i}"] = st.text_input(
                    f"{title} {i}行目", label_visibility="collapsed",
                    value="" if saved is None else saved[f"{prefix}_{i}"],
                    placeholder=hint or f"{i}行目", key=f"review_{month}_{prefix}_{i}",
                )
    st.caption("薄い文字は自動集計からの候補です。自分の言葉で「なぜ効いた/効かなかったか」まで書くと、そのまま学びになります。")

    if st.button("振り返りを保存", type="primary"):
        row["saved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        storage.save("reviews", logic.upsert_review(reviews, row))
        flash(f"{month} の振り返りを保存しました。")
        st.rerun()


def _hints(df):
    if df is None or df.empty:
        return []
    return [f"{p['change']}（{logic.fmt_pct(p['diff_pct'])}）" for _, p in df.head(3).iterrows()]
