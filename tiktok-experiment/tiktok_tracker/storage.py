"""CSVの読み書き。Excelで開いても文字化けしないよう UTF-8 (BOM付き) で保存する。"""

import pandas as pd

from . import config


def _path(name):
    filename, _, _ = config.TABLES[name]
    return config.DATA_DIR / filename


def load(name):
    """テーブルを読み込む。ファイルが無ければ空の表を返す。"""
    _, columns, numeric = config.TABLES[name]
    path = _path(name)
    if path.exists():
        df = pd.read_csv(path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    else:
        df = pd.DataFrame(columns=columns)
    return normalize(name, df)


def normalize(name, df):
    """列をそろえ、数値列は数値（空欄は NaN）、文字列列は str（空欄は ""）にする。"""
    _, columns, numeric = config.TABLES[name]
    df = df.copy()
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    df = df[columns]
    for col in columns:
        if col in numeric:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = df[col].fillna("").astype(str).str.strip()
    return df.reset_index(drop=True)


def save(name, df):
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    df = normalize(name, df)
    df.to_csv(_path(name), index=False, encoding="utf-8-sig")
    return df


def append(name, row):
    df = load(name)
    new = normalize(name, pd.DataFrame([row]))
    df = new if df.empty else pd.concat([df, new], ignore_index=True)
    return save(name, df)


def next_post_id(posts):
    ids = posts["id"].dropna()
    return int(ids.max()) + 1 if len(ids) else 1
