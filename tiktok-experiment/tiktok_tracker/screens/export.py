"""画面5: ガクチカ素材の出力"""

from datetime import datetime

import streamlit as st

from .. import config, report, storage


def render():
    st.title("⑤ ガクチカ素材の出力")
    st.caption("ベースライン → 目標 → 実施した施策 → 結果の数字 → 学び の順に、Markdownにまとめます。")

    now = datetime.now()
    md = report.build_markdown(
        storage.load("baseline"), storage.load("goals"),
        storage.load("posts"), storage.load("reviews"), generated_at=now,
    )
    filename = f"gakuchika_{now:%Y%m%d}.md"

    c1, c2 = st.columns(2)
    if c1.button("Markdownファイルに書き出す", type="primary"):
        config.EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        path = config.EXPORT_DIR / filename
        path.write_text(md, encoding="utf-8")
        st.success(f"書き出しました: `{path}`")
    c2.download_button("ダウンロード", md, file_name=filename, mime="text/markdown")

    preview, raw = st.tabs(["プレビュー", "Markdown（コピー用）"])
    with preview:
        st.markdown(md)
    with raw:
        st.code(md, language="markdown")
