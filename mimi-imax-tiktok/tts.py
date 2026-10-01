"""edge-tts でシーンごとのナレーションを合成し、字幕の区切りごとの時刻を JSON に書く。"""
import asyncio
import json
import os
import sys

import certifi

# エージェントプロキシ環境では、その CA を信頼しないと TLS が通らない
CA = os.environ.get("TTS_CA_BUNDLE")
if CA:
    certifi.where = lambda: CA

import edge_tts

from script import PITCH, RATE, SCENES, VOICE

OUT = sys.argv[1] if len(sys.argv) > 1 else "build"


async def synth(i, scene):
    text = "".join(r for _, r in scene["subs"])
    words = []
    mp3 = f"{OUT}/narr{i}.mp3"
    com = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH, boundary="WordBoundary")
    with open(mp3, "wb") as f:
        async for chunk in com.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "text": chunk["text"],
                    "start": chunk["offset"] / 1e7,
                    "end": (chunk["offset"] + chunk["duration"]) / 1e7,
                })
    return mp3, words


def align(scene, words):
    """読みテキスト上の位置で、各字幕チャンクの開始時刻を単語境界から求める。"""
    full = "".join(r for _, r in scene["subs"])
    # 各単語が full のどこから始まるか
    pos, spans = 0, []
    for w in words:
        k = full.find(w["text"], pos)
        if k < 0:
            continue
        spans.append((k, k + len(w["text"]), w["start"], w["end"]))
        pos = k + len(w["text"])
    out, cpos = [], 0
    for disp, read in scene["subs"]:
        t = None
        for a, b, s, e in spans:
            if a >= cpos:  # チャンク先頭以降で最初に始まる単語
                t = s
                break
            if a < cpos < b:  # 「10月23日から11月2日」のように1語がチャンクをまたぐときは按分
                t = s + (e - s) * (cpos - a) / (b - a)
                break
        out.append({"text": disp, "start": t})
        cpos += len(read)
    out[0]["start"] = 0.0
    return out


async def main():
    os.makedirs(OUT, exist_ok=True)
    timing = []
    for i, sc in enumerate(SCENES):
        mp3, words = await synth(i, sc)
        timing.append({"audio": mp3, "subs": align(sc, words), "words": words})
    with open(f"{OUT}/timing.json", "w") as f:
        json.dump(timing, f, ensure_ascii=False, indent=1)


asyncio.run(main())
