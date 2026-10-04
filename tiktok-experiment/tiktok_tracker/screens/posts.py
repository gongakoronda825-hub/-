"""画面3: 投稿ログ"""

from datetime import date, datetime, time

import pandas as pd
import streamlit as st

from .. import config, logic, storage
from ._common import flash, show_flash


def render():
    st.title("③ 投稿ログ")
    st.caption("1投稿につき「変えた点」は1つだけ。数値（再生数など）は投稿の48時間後に入力します。")
    show_flash()

    posts = storage.load("posts")

    _pending_section(posts)
    st.divider()
    _new_post_form(posts)
    st.divider()
    _log_table(posts)


# ---------- 48時間後の数値入力 ----------

def _pending_section(posts):
    pending = logic.pending_posts(posts)
    st.subheader("📮 数値が未入力の投稿")
    if pending.empty:
        st.success("未入力の投稿はありません。")
        return

    ready = pending[pending["ready"]]
    waiting = pending[~pending["ready"]]
    if not ready.empty:
        st.warning(f"投稿から48時間が経った投稿が **{len(ready)}件** あります。数値を入力しましょう。")
    if not waiting.empty:
        lines = []
        for _, p in waiting.iterrows():
            h = p["hours_since"]
            when = "投稿日時が不明" if h is None else f"あと約{max(config.RESULT_WAIT_HOURS - h, 0):.0f}時間"
            lines.append(f"- {p['posted_at']}「{p['title']}」… {when}")
        st.info("48時間待ちの投稿:\n" + "\n".join(lines))

    for _, p in ready.iterrows():
        pid = int(p["id"])
        with st.expander(f"{p['posted_at']}「{p['title']}」（未入力: {p['missing']}）"):
            st.caption(f"変えた点: {p['change'] or '—'}／仮説: {p['hypothesis'] or '—'}")
            values = _metric_inputs(p, key=f"fill_{pid}")
            insight = st.text_area("気づき", value=p["insight"], key=f"fill_{pid}_insight", height=80)
            if st.button("この投稿の数値を保存", key=f"fill_{pid}_save", type="primary"):
                idx = posts.index[posts["id"] == pid][0]
                for col, v in values.items():
                    posts.loc[idx, col] = v
                posts.loc[idx, "insight"] = insight
                storage.save("posts", posts)
                flash(f"「{p['title']}」の数値を保存しました。")
                st.rerun()


def _metric_inputs(row, key):
    def val(col):
        v = None if row is None else row[col]
        return None if v is None or pd.isna(v) else float(v)

    c1, c2, c3, c4 = st.columns(4)
    return {
        "views": c1.number_input("再生数", min_value=0.0, step=1.0, value=val("views"), key=f"{key}_views"),
        "retention": c2.number_input("視聴維持率(%)", min_value=0.0, max_value=100.0, step=0.1,
                                     value=val("retention"), key=f"{key}_retention"),
        "saves": c3.number_input("保存数", min_value=0.0, step=1.0, value=val("saves"), key=f"{key}_saves"),
        "likes": c4.number_input("いいね数", min_value=0.0, step=1.0, value=val("likes"), key=f"{key}_likes"),
    }


# ---------- 新規投稿 ----------

def _new_post_form(posts):
    st.subheader("✏️ 投稿を記録する")
    # 保存後に入力欄を空にするため、キーに版番号を付けて作り直す
    v = st.session_state.setdefault("post_form_version", 0)
    k = f"post_{v}_"

    c1, c2 = st.columns(2)
    d = c1.date_input("投稿日", value=date.today(), key=k + "date")
    t = c2.time_input("投稿時刻", value=time(19, 0), step=900, key=k + "time")
    title = st.text_input("動画タイトル", key=k + "title")
    c3, c4 = st.columns([3, 1])
    change = c3.text_input(
        "今回変えた点（1つだけ）", key=k + "change",
        placeholder="例: 冒頭1秒に結論のテロップを入れた",
    )
    category = c4.selectbox("変更カテゴリ", config.CATEGORIES, key=k + "category")
    warnings = logic.check_change(change)
    for w in warnings:
        st.warning(w, icon="⚠️")
    hypothesis = st.text_area(
        "仮説", key=k + "hypothesis", height=80,
        placeholder="例: 冒頭で結論を見せれば離脱が減り、視聴維持率が上がって再生数も伸びるはず",
    )

    with st.expander("数値もいま入力する（投稿から48時間経っている場合）"):
        values = _metric_inputs(None, key=k + "m")
    insight = st.text_area("気づき（あとからでもOK）", key=k + "insight", height=80)

    confirm = True
    if warnings:
        confirm = st.checkbox("警告を確認したうえで、このまま保存する", key=k + "confirm")

    if st.button("投稿を保存", type="primary", key=k + "save"):
        if not title.strip():
            st.error("動画タイトルを入力してください。")
        elif not confirm:
            st.error("「今回変えた点」の警告を確認してください（1つに絞るか、確認のチェックを入れる）。")
        else:
            storage.append("posts", {
                "id": storage.next_post_id(posts),
                "posted_at": datetime.combine(d, t).strftime("%Y-%m-%d %H:%M"),
                "title": title,
                "change": change,
                "category": category,
                "hypothesis": hypothesis,
                **values,
                "insight": insight,
            })
            st.session_state["post_form_version"] = v + 1
            flash(f"「{title}」を保存しました。")
            st.rerun()


# ---------- 一覧 ----------

def _log_table(posts):
    st.subheader("📋 投稿ログ一覧")
    if posts.empty:
        st.info("まだ投稿がありません。")
        return

    flagged = posts[posts["change"].map(lambda c: bool(logic.check_change(c)))]
    if not flagged.empty:
        st.warning(
            "「今回変えた点」が空欄・複数の投稿があります: "
            + "、".join(f"#{int(i)}「{t}」" for i, t in zip(flagged["id"], flagged["title"]))
        )

    st.caption("表の中で直接直せます。行を選んで削除もできます。編集したら「一覧の変更を保存」を押してください。")
    view = posts.sort_values("posted_at", ascending=False)
    edited = st.data_editor(
        view,
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        column_config={
            **{c: config.LABELS[c] for c in view.columns},
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "posted_at": st.column_config.TextColumn("投稿日時", help="YYYY-MM-DD HH:MM"),
            "category": st.column_config.SelectboxColumn("変更カテゴリ", options=config.CATEGORIES),
        },
        key="posts_editor",
    )
    if st.button("一覧の変更を保存"):
        edited = edited.dropna(how="all").copy()
        bad = [str(x) for x in edited["posted_at"] if logic.parse_posted_at(x) is None]
        if bad:
            st.error("投稿日時が読めない行があります（YYYY-MM-DD HH:MM で入力）: " + "、".join(bad))
            return
        next_id = storage.next_post_id(posts)
        for idx in edited.index[edited["id"].isna()]:
            edited.loc[idx, "id"] = next_id
            next_id += 1
        storage.save("posts", edited.sort_values("posted_at"))
        flash("一覧の変更を保存しました。")
        st.rerun()
