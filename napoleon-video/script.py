"""台本データ。1セグメント = 1文 = 1字幕。

art  は本文の絵。character (棒人間) か figure (比較図)。
marks は「あとから書き足した風」の強調のリスト。
  kind: circle (赤の丸囲み) / marker (黄マーカー) / underline (赤の二重線) / focus (集中線)
  line: 字幕の何行目に付けるか / word: その行のどの語に付けるか
"""

TAG = "#歴史のウソ  #1分雑学"
TITLE_LINES = ["ナポレオンは", "チビじゃなかった"]

SEGMENTS = [
    {
        "narration": "ナポレオンはチビだった。よく聞く話ですが、実は大きな誤解です。",
        "subtitle": ["「ナポレオンはチビ」", "それ、実は大きな誤解"],
        "art": "character",
        "marks": [{"kind": "circle", "line": 1, "word": "大きな誤解"}],
    },
    {
        "narration": "記録に残る身長は、五フィート二インチ。フランスの古い単位で、約百六十九センチ。",
        "subtitle": ["記録は5フィート2インチ", "仏の旧単位で約169cm"],
        "art": "character",
        "marks": [{"kind": "marker", "line": 1, "word": "約169cm"}],
    },
    {
        "narration": "当時のフランス人男性の平均は、約百六十五センチ。むしろ平均より高いんです。",
        "subtitle": ["当時の平均は約165cm", "むしろ平均より高い"],
        "art": "figure",          # ページをめくると比較図が描いてある
        "marks": [],
    },
    {
        "narration": "小さな皇帝のイメージは、イギリスの風刺画が広めたもの。今も私たちは騙されたままです。",
        "subtitle": ["「小さな皇帝」像は", "英国の風刺画が作った"],
        "art": "character",
        "marks": [{"kind": "underline", "line": 1, "word": "風刺画"},
                  {"kind": "focus"}],
    },
]
