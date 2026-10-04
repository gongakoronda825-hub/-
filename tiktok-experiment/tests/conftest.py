import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """CSVの保存先を一時フォルダに差し替える。"""
    from tiktok_tracker import config

    monkeypatch.setattr(config, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(config, "EXPORT_DIR", tmp_path / "exports")
    monkeypatch.setenv("TIKTOK_TRACKER_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("TIKTOK_TRACKER_EXPORT_DIR", str(tmp_path / "exports"))
    return tmp_path / "data"
