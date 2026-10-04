"""画面1: 現状の記録（ベースライン）"""

from datetime import date

import streamlit as st

from .. import config, logic, storage
from ._common import flash, show_flash

CHARTS = [
    ("フォロワー数", "followers", "人", 0),
    ("直近10本の平均再生数", "avg_views", "回", 0),
    ("平均視聴維持率(%)", "avg_retention", "%", 1),
    ("平均保存数", "avg_saves", "件", 1),
]


def render():
    st.title("① 現状の記録（ベースライン）")
    st.caption("改善を始める前と、その後の定点観測の数字を記録します。月初などに定期的に登録すると推移が見えます。")
    show_flash()

    baseline = storage.load("baseline")

    with st.form("baseline_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        d = c1.date_input("日付", value=date.today())
        followers = c2.number_input("フォロワー数", min_value=0, step=1, value=None)
        c3, c4, c5 = st.columns(3)
        views = c3.number_input("直近10本の平均再生数", min_value=0.0, step=1.0, value=None)
        retention = c4.number_input("平均視聴維持率(%)", min_value=0.0, max_value=100.0, step=0.1, value=None)
        saves = c5.number_input("平均保存数", min_value=0.0, step=0.1, value=None)
        submitted = st.form_submit_button("登録する", type="primary")

    if submitted:
        if None in (followers, views, retention, saves):
            st.error("すべての項目を入力してください。")
        else:
            key = d.isoformat()
            replaced = key in set(baseline["date"])
            rest = baseline[baseline["date"] != key]
            row = {
                "date": key, "followers": followers, "avg_views": views,
                "avg_retention": retention, "avg_saves": saves,
            }
            storage.save("baseline", rest)
            storage.append("baseline", row)
            flash(f"{key} の記録を{'上書き' if replaced else '登録'}しました。")
            st.rerun()

    df = logic.sorted_baseline(baseline)
    if df.empty:
        st.info("まだ記録がありません。上のフォームから最初の数字を登録しましょう。")
        return

    st.subheader("推移")
    if len(df) == 1:
        st.caption("記録が2回以上になると線でつながります。")
    chart_df = df.set_index("_date")
    cols = st.columns(2)
    for i, (label, col, unit, digits) in enumerate(CHARTS):
        with cols[i % 2]:
            first, last = df[col].iloc[0], df[col].iloc[-1]
            st.markdown(f"**{label}**　最新 {logic.fmt(last, unit, digits)}"
                        f"（初回比 {logic.fmt_pct(logic.diff_pct(last, first))}）")
            st.line_chart(chart_df[[col]].rename(columns={col: label}), height=220)

    st.subheader("記録一覧（直接編集・行の削除もできます）")
    edited = st.data_editor(
        baseline,
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        column_config={c: config.LABELS[c] for c in baseline.columns},
        key="baseline_editor",
    )
    if st.button("一覧の変更を保存"):
        storage.save("baseline", edited.dropna(how="all"))
        flash("一覧の変更を保存しました。")
        st.rerun()
