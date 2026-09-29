"""ナレーション音声を作る (VOICEVOX:春日部つむぎ)

カットの頭に合わせて1フレーズずつ読み上げ、audio/narration.mp3 に並べる。
フレーズが次の枠に収まらないときは、その分だけ読む速さを上げる。
事前に VOICEVOX Engine を 127.0.0.1:50021 で起動しておくこと。
使い方: python3 ghibli-video/narration.py
"""
import io
import json
import subprocess
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "audio"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
ENGINE = "http://127.0.0.1:50021"
SPEAKER = 8         # 春日部つむぎ ノーマル
BASE_SPEED = 1.15   # 標準の読み上げ速度
MAX_SPEED = 1.45
SR = 44100
TOTAL = 60.0

# (開始秒, 読み上げ文)。人名は読み間違いを防ぐためカタカナ/ひらがなで渡す
LINES = [
    (0.10, "ジブリ好きなのに、これ観てないのはもったいない！"),
    (4.25, "マイナーだけど本当におすすめなジブリ映画、3選！"),
    (7.35, "第3位、思い出のマーニー。"),
    (9.05, "心を閉ざした少女、アンナが、"),
    (12.05, "北海道の海辺の屋敷で出会った、"),
    (15.05, "金髪の少女、マーニー。"),
    (18.05, "二人の関係に隠された秘密がわかった瞬間、"),
    (21.05, "涙が止まらなくなります。"),
    (23.35, "第2位、コクリコ坂から。"),
    (25.05, "舞台は1963年の横浜。"),
    (28.05, "毎朝旗を揚げる少女、ウミと、"),
    (31.05, "少年、シュンの甘酸っぱい恋。"),
    (34.05, "古い部室棟、カルチェラタンの雰囲気と、"),
    (37.05, "昭和レトロな街並みが最高です。"),
    (39.40, "そして第1位は、海がきこえる。"),
    (42.05, "実はテレビ用に作られた、知る人ぞ知る一本。"),
    (45.05, "高知の高校生、タクと、"),
    (48.05, "東京から来た転校生、リカコ。わがままなのに目が離せない彼女との、"),
    (52.30, "リアルな青春が刺さります。"),
    (55.10, "あなたはどれを観たことある？コメントで教えてね！"),
]


def post(path, params, body=b""):
    url = f"{ENGINE}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return r.read()


def synth(text, speed):
    """VOICEVOX で読み上げ → float32 mono 44.1kHz。前後の無音は切る"""
    q = json.loads(post("/audio_query", {"text": text, "speaker": SPEAKER}))
    q.update(speedScale=speed, prePhonemeLength=0.0, postPhonemeLength=0.05,
             outputSamplingRate=SR, outputStereo=False)
    wav = post("/synthesis", {"speaker": SPEAKER}, json.dumps(q).encode())
    with wave.open(io.BytesIO(wav)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768
    idx = np.nonzero(np.abs(a) > 0.01)[0]
    return a[max(0, idx[0] - 400): idx[-1] + 2000] if len(idx) else a


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    buf = np.zeros(int(SR * TOTAL), np.float32)
    report = []
    for k, (start, text) in enumerate(LINES):
        limit = (LINES[k + 1][0] if k + 1 < len(LINES) else TOTAL) - start - 0.08
        speed = BASE_SPEED
        while True:
            clip = synth(text, speed)
            dur = len(clip) / SR
            if dur <= limit or speed >= MAX_SPEED:
                break
            speed = min(MAX_SPEED, round(speed + 0.05, 2))
        a = int(start * SR)
        buf[a:a + len(clip)] += clip[: len(buf) - a]
        flag = "" if dur <= limit else "  ※枠をはみ出し"
        print(f"{start:5.2f}-{start + dur:5.2f}s (枠 {start + limit:5.2f}) x{speed:.2f} {text}{flag}")

    wav = OUT / "_narration.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((np.clip(buf, -1, 1) * 32767).astype("<i2").tobytes())
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", str(wav), "-af", "loudnorm=I=-16:TP=-1.5",
                    "-ar", str(SR), "-b:a", "192k", str(OUT / "narration.mp3")], check=True)
    wav.unlink()
    print("->", OUT / "narration.mp3")


if __name__ == "__main__":
    main()
