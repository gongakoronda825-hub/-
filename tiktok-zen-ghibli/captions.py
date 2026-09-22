"""字幕の区切りと、ナレーション音声に合わせたタイミング計算。

各文を「画面に出す単位」に割り、VOICEVOXのAudioQueryが持つモーラ長から
それぞれの表示開始・終了時刻を求める。モーラ長の合計は実際の音声より数%
長く出るので、文ごとに実測の長さへ比例補正してから使う。
"""

# 文ごとの字幕チャンク。連結すると generate_narration.SCRIPT の本文と一致する。
CAPTIONS = [
    ["君たちはどう生きるか"],
    ["京都で、", "「君たちはどう生きるか」の世界で", "禅に触れられるイベントがあります。"],
    ["それが、", "「禅とジブリ」京都展。"],
    ["10月3日から、", "京都市京セラ美術館で開催されます。"],
    ["ジブリの名作から、", "死生観や人生哲学などを", "禅的に読みとき、",
     "宮﨑駿・高畑勲両監督との", "映画制作の経験に照らして、", "禅を語ります。"],
    ["本展は、この「禅とジブリ」を", "原点として生まれました。"],
    ["「君たちはどう生きるか」の世界を通して、", "禅に触れられる体感型の展覧会です。"],
    ["ジブリ作品に込められた問いや、", "生き方についても、",
     "禅という新たな視点から", "楽しむことができます。"],
    ["さらに、鈴木敏夫さんと", "禅僧による対談をもとにした展示も。"],
    ["ただのジブリ展とは少し違う、", "「君たちはどう生きるか」を",
     "もう一度深く味わえるイベントです。"],
    ["開催は12月6日まで。"],
    ["ジブリ好きなら、", "ぜひチェックしてみてください。"],
]

# 字幕送りの見た目にほとんど影響しない文字は、カラオケ表示の重みを下げる。
SMALL_KANA = "ぁぃぅぇぉっゃゅょァィゥェォッャュョ"
NO_TIME = "、。「」『』（）・！？ 　"


def char_weight(ch):
    if ch in NO_TIME:
        return 0.0
    if ch in SMALL_KANA:
        return 0.45
    return 1.0


def query_items(query):
    """AudioQueryを (種類, 長さ) の並びにほどく。長さはspeedScale適用前。"""
    items = []
    for phrase in query["accent_phrases"]:
        for mora in phrase["moras"]:
            items.append(("mora", (mora.get("consonant_length") or 0.0)
                          + mora["vowel_length"]))
        pause = phrase.get("pause_mora")
        if pause:
            items.append(("pause", (pause.get("consonant_length") or 0.0)
                          + pause["vowel_length"]))
    return items


def mora_count(query):
    return sum(len(p["moras"]) for p in query["accent_phrases"])


def sentence_captions(query_of, sentence, chunks, span):
    """1文のチャンクに (テキスト, 開始秒, 終了秒, カラオケ用の区間) を割り当てる。"""
    query = query_of(sentence)
    items = query_items(query)
    speed = query["speedScale"]
    pre = query["prePhonemeLength"] / speed
    post = query["postPhonemeLength"] / speed
    lengths = [d / speed for _, d in items]

    # モーラ長の総和は実測より数%長い（エンジン側でフレーム単位に丸められる）。
    # 文の実測長にそろえておけば、文の終わりでも字幕がずれない。
    predicted = pre + sum(lengths) + post
    scale = (span[1] - span[0]) / predicted if predicted else 1.0
    lengths = [d * scale for d in lengths]

    counts = [mora_count(query_of(chunk)) for chunk in chunks]
    total = mora_count(query)
    if sum(counts) != total:
        # 読みの分割が想定とずれた場合は文字数の重みで按分する。
        weights = [sum(char_weight(c) for c in chunk) or 1.0 for chunk in chunks]
        acc, counts = 0.0, []
        for w in weights:
            acc += w
            counts.append(round(total * acc / sum(weights)))
        counts = [b - a for a, b in zip([0] + counts, counts)]

    # 実モーラのn番目が items の何番目かを引けるようにする。
    mora_at = [i for i, (kind, _) in enumerate(items) if kind == "mora"]
    starts = [0]
    for c in counts:
        starts.append(starts[-1] + c)

    out = []
    for chunk, first, last in zip(chunks, starts, starts[1:]):
        begin = mora_at[first] if first < len(mora_at) else len(items)
        end = mora_at[last] if last < len(mora_at) else len(items)
        start = span[0] + pre + sum(lengths[:begin])
        out.append({
            "text": chunk,
            "start": start,
            "end": start + sum(lengths[begin:end]),
            "items": [(items[i][0], lengths[i]) for i in range(begin, end)],
        })
    return out


def build_captions(query_of, script, spans, audio_end):
    """全文の字幕を組み、表示終了を次の字幕の開始まで伸ばす。"""
    captions = []
    for (sentence, _), chunks, span in zip(script, CAPTIONS, spans):
        assert "".join(chunks) == sentence, f"字幕と本文が一致しない: {sentence}"
        captions += sentence_captions(query_of, sentence, chunks, span)
    for current, following in zip(captions, captions[1:]):
        current["show_until"] = following["start"]
    captions[-1]["show_until"] = audio_end
    return captions


def to_srt(captions):
    def stamp(t):
        ms = int(round(t * 1000))
        h, ms = divmod(ms, 3600000)
        m, ms = divmod(ms, 60000)
        s, ms = divmod(ms, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    for i, cap in enumerate(captions, 1):
        lines.append(f"{i}\n{stamp(cap['start'])} --> {stamp(cap['show_until'])}\n"
                     f"{cap['text']}\n")
    return "\n".join(lines)
