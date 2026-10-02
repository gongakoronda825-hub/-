"""VOICEVOX エンジンでシーンごとのナレーションを合成し、字幕の区切りごとの時刻を JSON に書く。

エンジンは別に起動しておく（例: docker run -d -p 50021:50021 voicevox/voicevox_engine:cpu-latest）。
字幕の区切りの時刻は、シーン全文の audio_query のモーラ長から求める（区切りごとに別々に合成すると
文の途中で抑揚が切れるため、合成はシーン単位で1回にする）。
"""
import json
import os
import sys
import urllib.parse
import urllib.request

from script import PAUSE_SCALE, SCENES, SPEAKER, SPEED

ENGINE = os.environ.get("VOICEVOX_URL", "http://localhost:50021")
OUT = sys.argv[1] if len(sys.argv) > 1 else "build"


def post(path, params, body=None):
    url = f"{ENGINE}{path}?{urllib.parse.urlencode(params)}"
    data = json.dumps(body).encode() if body is not None else b""
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as r:
        return r.read()


def query(text):
    q = json.loads(post("/audio_query", {"text": text, "speaker": SPEAKER}))
    q["speedScale"] = SPEED
    q["pauseLengthScale"] = PAUSE_SCALE  # 読点などの間を詰める
    q["prePhonemeLength"] = 0.05
    q["postPhonemeLength"] = 0.1
    q["outputSamplingRate"] = 48000
    return q


def moras(q):
    """[(長さ, 発音するモーラか)] を並べる。"""
    out = []
    for ap in q["accent_phrases"]:
        for m in ap["moras"]:
            out.append(((m["consonant_length"] or 0) + m["vowel_length"], True))
        if ap.get("pause_mora"):
            out.append((ap["pause_mora"]["vowel_length"] * PAUSE_SCALE, False))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    timing = []
    for i, sc in enumerate(SCENES):
        reads = [r for _, r in sc["subs"]]
        q = query("".join(reads))
        # 区切りごとのモーラ数（区切り単体で問い合わせて数える）
        counts = [sum(1 for _, voiced in moras(query(r)) if voiced) for r in reads]
        bounds, acc = [], 0
        for c in counts[:-1]:
            acc += c
            bounds.append(acc)
        t, n, starts = q["prePhonemeLength"], 0, [0.0]
        for length, voiced in moras(q):
            if voiced:
                if n in bounds and len(starts) <= bounds.index(n) + 1:
                    starts.append(t / SPEED)
                n += 1
            t += length
        speech_end = t / SPEED
        wav = f"{OUT}/narr{i}.wav"
        with open(wav, "wb") as f:
            f.write(post("/synthesis", {"speaker": SPEAKER}, q))
        while len(starts) < len(reads):  # モーラ数がずれたときの保険
            starts.append(starts[-1])
        timing.append({
            "audio": wav,
            "end": speech_end,
            "subs": [{"text": d, "start": s} for (d, _), s in zip(sc["subs"], starts)],
        })
    with open(f"{OUT}/timing.json", "w") as f:
        json.dump(timing, f, ensure_ascii=False, indent=1)


main()
