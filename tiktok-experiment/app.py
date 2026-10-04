"""TikTok改善実験トラッカー

起動: streamlit run app.py
"""

import streamlit as st

from tiktok_tracker.screens import baseline, export, goal, posts, review

st.set_page_config(page_title="TikTok改善実験トラッカー", page_icon="📈", layout="wide")

pages = [
    st.Page(baseline.render, title="① 現状の記録", icon="📊", url_path="baseline", default=True),
    st.Page(goal.render, title="② 目標設定", icon="🎯", url_path="goal"),
    st.Page(posts.render, title="③ 投稿ログ", icon="📝", url_path="posts"),
    st.Page(review.render, title="④ 月次振り返り", icon="🔍", url_path="review"),
    st.Page(export.render, title="⑤ ガクチカ素材の出力", icon="📄", url_path="export"),
]

with st.sidebar:
    st.markdown("### 📈 TikTok改善実験")
    st.caption("仮説 → 検証 → 改善 を数字で残す")

st.navigation(pages).run()
