"""画面2: 目標設定"""

from datetime import date, timedelta

import streamlit as st

from .. import config, logic, storage
from ._common import flash, show_flash


def render():
    st.title("② 目標設定")
    st.caption("追いかける指標を1つに絞り、期限つきの目標を立てます。")
    show_flash()

    baseline = storage.load("baseline")
    goals = storage.load("goals")
    goal = logic.latest_goal(goals)

    if goal is not None:
        _show_goal(goal, goals, baseline)
        st.divider()
        st.subheader("目標を立て直す")
        st.caption("新しく登録すると、それが現在の目標になります（過去の目標は履歴に残ります）。")
    else:
        st.subheader("目標を立てる")

    metric = st.radio("指標（1つだけ選ぶ）", list(config.GOAL_METRICS), horizontal=True)
    unit, digits = config.GOAL_METRICS[metric]
    step = 1.0 if digits == 0 else 0.1
    num_format = f"%.{digits}f"
    suggestion = logic.suggest_current_value(metric, baseline)
    if metric == "フォロワー増加数":
        st.caption("「現在値」は、最初のベースラインからの増加人数です（記録から自動で候補を入れています）。")

    c1, c2, c3 = st.columns(3)
    current = c1.number_input(
        f"現在値（{unit}）", min_value=0.0 if metric != "フォロワー増加数" else None,
        step=step, value=suggestion, format=num_format, key=f"goal_current_{metric}",
    )
    target = c2.number_input(f"目標値（{unit}）", min_value=0.0, step=step, value=None,
                             format=num_format, key=f"goal_target_{metric}")
    deadline = c3.date_input("期限", value=date.today() + timedelta(days=30), min_value=date.today())
    if suggestion is None:
        st.caption("ベースラインを登録すると、現在値の候補が自動で入ります。")

    if st.button("この目標を登録", type="primary"):
        if current is None or target is None:
            st.error("現在値と目標値を入力してください。")
        elif target <= 0:
            st.error("目標値は0より大きくしてください。")
        else:
            storage.append("goals", {
                "created_at": date.today().isoformat(),
                "metric": metric,
                "start_value": current,
                "current_value": current,
                "target_value": target,
                "deadline": deadline.isoformat(),
            })
            flash("目標を登録しました。")
            st.rerun()


def _show_goal(goal, goals, baseline):
    metric = goal["metric"]
    unit, digits = config.GOAL_METRICS.get(metric, ("", 0))
    rate = logic.achievement_rate(goal["current_value"], goal["target_value"])
    progress = logic.progress_rate(goal["start_value"], goal["current_value"], goal["target_value"])
    left = logic.days_left(goal["deadline"])

    st.subheader(f"現在の目標：{metric}を {logic.fmt(goal['target_value'], unit, digits)} に")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("達成率", logic.fmt_pct(rate, signed=False), help="現在値 ÷ 目標値")
    c2.metric("現在値", logic.fmt(goal["current_value"], unit, digits),
              delta=_delta(goal["current_value"], goal["start_value"], unit, digits), help="設定時からの変化")
    c3.metric("目標値", logic.fmt(goal["target_value"], unit, digits))
    c4.metric("期限まで", "期限切れ" if left is not None and left < 0 else logic.fmt(left, "日"),
              help=f"期限: {goal['deadline']}")
    if rate is not None:
        st.progress(min(max(rate, 0), 100) / 100)
    if progress is not None:
        st.caption(
            f"設定時の値 {logic.fmt(goal['start_value'], unit, digits)} から見た伸び幅の進捗: "
            f"{logic.fmt_pct(progress, signed=False)}"
        )

    with st.expander("現在値を更新する"):
        suggestion = logic.suggest_current_value(metric, baseline, since=goal["created_at"])
        if suggestion is not None:
            st.caption(f"最新のベースラインから計算した候補: {logic.fmt(suggestion, unit, digits)}")
        new_value = st.number_input(
            f"新しい現在値（{unit}）", step=1.0 if digits == 0 else 0.1, format=f"%.{digits}f",
            value=suggestion if suggestion is not None else float(goal["current_value"]),
            key="goal_update_value",
        )
        if st.button("現在値を保存"):
            idx = goals.sort_values("created_at").index[-1]
            goals.loc[idx, "current_value"] = new_value
            storage.save("goals", goals)
            flash("現在値を更新しました。")
            st.rerun()

    if len(goals) > 1:
        with st.expander("目標の履歴"):
            hist = goals.sort_values("created_at", ascending=False).rename(columns={
                "created_at": "設定日", "metric": "指標", "start_value": "設定時の値",
                "current_value": "現在値", "target_value": "目標値", "deadline": "期限",
            })
            st.dataframe(hist, hide_index=True, width="stretch")


def _delta(current, start, unit, digits):
    if current is None or start is None:
        return None
    diff = current - start
    return f"{diff:+,.{digits}f}{unit}"
