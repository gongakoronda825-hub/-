"""各画面がエラーなく描画できるかの確認（Streamlit AppTest）。"""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from tiktok_tracker import storage

from . import sample

APP = str(Path(__file__).resolve().parent.parent / "app.py")
PAGES = ["baseline", "goal", "posts", "review", "export"]


ROOT = str(Path(__file__).resolve().parent.parent)


def _run(page):
    """画面の render() を単体で動かす。"""
    script = (
        f"import sys; sys.path.insert(0, {ROOT!r})\n"
        f"from tiktok_tracker.screens import {page}\n"
        f"{page}.render()\n"
    )
    at = AppTest.from_string(script, default_timeout=30).run()
    assert not at.exception, at.exception
    return at


def test_app_entry(data_dir):
    at = AppTest.from_file(APP, default_timeout=30).run()
    assert not at.exception, at.exception
    assert at.title[0].value.startswith("①")


@pytest.mark.parametrize("page", PAGES)
def test_pages_empty(data_dir, page):
    _run(page)


@pytest.mark.parametrize("page", PAGES)
def test_pages_with_data(data_dir, page):
    storage.save("baseline", sample.baseline())
    storage.save("posts", sample.posts())
    _run(page)


def test_change_warning_shown(data_dir):
    at = _run("posts")
    at.text_input(key="post_0_change").input("冒頭を変えた、尺も短くした").run()
    assert any("複数" in w.value for w in at.warning)
