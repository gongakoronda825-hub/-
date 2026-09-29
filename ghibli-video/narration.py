"""ナレーション音声を作る (VOICEVOX:春日部つむぎ)

1フレーズ＝1区間として、フレーズの間をほぼ空けずに audio/narration.mp3 に並べる。
各区間の開始・終了秒を audio/timeline.json に書き出し、render.py がカットの長さに使う。
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
SPEED = 1.2         # 読み上げ速度
GAP = 0.12          # フレーズ間のすき間 (秒)
PAUSE = 0.5         # 「、」「。」での間の長さ (1.0 が標準)
RANK_LEAD = 0.30    # 順位発表の「ドドン」を聞かせてから読み始めるまで (秒)
TAIL = 1.2          # 最後のフレーズのあとに残す余韻 (秒)
FPS = 30
SR = 44100

# (読み上げ文, 順位発表か[, 読み上げ速度])。人名は読み間違いを防ぐためカタカナで渡す
LINES = [
    ("ジブリ好きなのに、これ観てないのはもったいない！", False),
    ("マイナーだけど本当におすすめなジブリ映画、3選！", False),
    ("第3位、思い出のマーニー。", True),
    ("心を閉ざした少女、アンナが、", False),
    ("北海道の海辺の屋敷で出会った、", False),
    ("金髪の少女、マーニー。", False),
    ("二人の関係に隠された秘密がわかった瞬間、", False),
    ("涙が止まらなくなります。", False),
    ("第2位、コクリコ坂から。", True),
    ("舞台は1963年の横浜。", False),
    ("毎朝旗を揚げる少女、ウミと、", False),
    ("少年、シュンの甘酸っぱい恋。", False),
    ("古い部室棟、カルチェラタンの雰囲気と、", False),
    ("昭和レトロな街並みが最高です。", False),
    ("そして第1位は、海がきこえる。", True),
    ("実はテレビ用に作られた、知る人ぞ知る一本。", False),
    ("高知の高校生、タクと、", False),
    ("東京から来た転校生、リカコ。わがままなのに目が離せない彼女との、", False),
    ("リアルな青春が刺さります。", False),
    ("あなたはどれを観たことある？コメントで教えてね！", False, 1.1),  # 最後ははっきり聞かせる
]


def frame_round(t):
    return round(t * FPS) / FPS


def post(path, params, body=b""):
    url = f"{ENGINE}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return r.read()


MIN_CONSONANT = 0.045  # 子音が短すぎると聞こえなくなる (例:「教えてね」の「て」が消える) ので下限を設ける


def synth(text, speed):
    """VOICEVOX で読み上げ → float32 mono 44.1kHz。前後の無音は切る"""
    q = json.loads(post("/audio_query", {"text": text, "speaker": SPEAKER}))
    for ap in q["accent_phrases"]:
        for m in ap["moras"]:
            if m.get("consonant") and m["consonant_length"] < MIN_CONSONANT:
                m["consonant_length"] = MIN_CONSONANT
    q.update(speedScale=speed, prePhonemeLength=0.0, postPhonemeLength=0.05, pauseLengthScale=PAUSE,
             outputSamplingRate=SR, outputStereo=False)
    wav = post("/synthesis", {"speaker": SPEAKER}, json.dumps(q).encode())
    with wave.open(io.BytesIO(wav)) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float32) / 32768
    idx = np.nonzero(np.abs(a) > 0.01)[0]
    return a[max(0, idx[0] - 400): idx[-1] + 2000] if len(idx) else a


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    clips, segments = [], []
    t = 0.0
    for k, (text, rank, *opt) in enumerate(LINES):
        clip = synth(text, opt[0] if opt else SPEED)
        start = t + (RANK_LEAD if rank else 0.05)
        end = start + len(clip) / SR
        seg_end = frame_round(end + (TAIL if k == len(LINES) - 1 else GAP))
        clips.append((start, clip))
        segments.append({"start": t, "end": seg_end, "voice_start": round(start, 3),
                         "voice_end": round(end, 3), "text": text})
        print(f"{t:6.2f}-{seg_end:6.2f}s  声 {start:6.2f}-{end:6.2f}  {text}")
        t = seg_end

    buf = np.zeros(int(SR * t) + SR, np.float32)
    for start, clip in clips:
        a = int(start * SR)
        buf[a:a + len(clip)] += clip
    buf = buf[: int(SR * t)]
    (OUT / "timeline.json").write_text(json.dumps(segments, ensure_ascii=False, indent=1))
    print(f"合計 {t:.2f} 秒")

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
