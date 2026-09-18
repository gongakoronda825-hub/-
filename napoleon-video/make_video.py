#!/usr/bin/env python3
"""棒人間が歴史・雑学を1つ紹介する30秒動画を作る。

  python3 napoleon-video/make_video.py            # 通常
  python3 napoleon-video/make_video.py --preview  # 1フレームだけ output/preview.png に出す

台本 -> ナレーション合成 -> PNG連番の描画 -> ffmpeg で MP4。
"""

import argparse
import glob
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile
import wave

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import renderer as R   # noqa: E402
import script          # noqa: E402
import tts             # noqa: E402

# --- 設定 -------------------------------------------------------------------
FPS = 30
DURATION = 30.0            # 秒
INTRO = 0.7                # 最初のナレーションが始まるまで
OUTRO_MIN = 1.2            # 最後のナレーション後の余韻
GAP = 0.45                 # 文と文のあいだ
SAMPLE_RATE = 48000
BGM_VOLUME = 0.10

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "output")
OUT_MP4 = os.path.join(OUT_DIR, "test_video.mp4")
PREVIEW_PNG = os.path.join(OUT_DIR, "preview.png")


# --- 音声 -------------------------------------------------------------------
def read_wav_mono(path):
    with wave.open(path, "rb") as w:
        n, ch, sw, sr = w.getnframes(), w.getnchannels(), w.getsampwidth(), w.getframerate()
        raw = w.readframes(n)
    if sw != 2:
        raise RuntimeError("16bit wav を想定しています: %s" % path)
    a = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768.0
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    if sr != SAMPLE_RATE:
        idx = np.linspace(0, len(a) - 1, int(len(a) * SAMPLE_RATE / sr)).astype(np.int64)
        a = a[idx]
    return a


def write_wav_mono(path, samples):
    clipped = np.clip(samples, -1.0, 1.0)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes((clipped * 32767).astype("<i2").tobytes())


def synth_segments(backend, workdir):
    """全セグメントを合成し、30秒に収まる話速を選ぶ。[(wavパス, 長さ), ...] を返す。"""
    n = len(script.SEGMENTS)
    budget = DURATION - INTRO - OUTRO_MIN - GAP * (n - 1)
    rate = 1.0
    for attempt in range(4):
        clips = []
        for i, seg in enumerate(script.SEGMENTS):
            p = os.path.join(workdir, "seg_%02d.wav" % i)
            d = tts.synth(backend, seg["narration"], p, rate)
            clips.append((p, d))
        total = sum(d for _, d in clips)
        print("  話速 %.2f -> ナレーション合計 %.2fs (許容 %.2fs)" % (rate, total, budget))
        if total <= budget or attempt == 3:
            return clips, rate
        rate = min(1.6, rate * (total / budget) * 1.02)
    return clips, rate


def build_timeline(durations):
    """各セグメントの開始/終了秒。"""
    spans, t = [], INTRO
    for d in durations:
        spans.append((t, t + d))
        t += d + GAP
    return spans


def fallback_timeline():
    """音声が作れない時は文字数比で30秒を割る。"""
    weights = [len(s["narration"]) for s in script.SEGMENTS]
    total_w = float(sum(weights))
    usable = DURATION - INTRO - OUTRO_MIN - GAP * (len(weights) - 1)
    spans, t = [], INTRO
    for w in weights:
        d = usable * w / total_w
        spans.append((t, t + d))
        t += d + GAP
    return spans


def build_track(clips, spans, workdir):
    """セグメント音声を30秒のトラックに並べる。"""
    track = np.zeros(int(DURATION * SAMPLE_RATE), dtype=np.float32)
    for (path, _), (start, _) in zip(clips, spans):
        a = read_wav_mono(path)
        s = int(start * SAMPLE_RATE)
        e = min(s + len(a), len(track))
        track[s:e] += a[:e - s]
    peak = float(np.max(np.abs(track)))
    if peak > 0:
        track *= 0.92 / peak
    out = os.path.join(workdir, "narration.wav")
    write_wav_mono(out, track)
    return out, track


# --- 口パク -----------------------------------------------------------------
def mouth_envelope(track, n_frames):
    """音の大きさから各フレームの口の開き(0-1)を作る。"""
    win = int(SAMPLE_RATE / FPS)
    env = np.zeros(n_frames, dtype=np.float32)
    for i in range(n_frames):
        chunk = track[i * win:(i + 1) * win]
        if len(chunk):
            env[i] = float(np.sqrt(np.mean(chunk ** 2)))
    if env.max() > 0:
        env = env / env.max()
    env = np.clip(env * 2.4, 0.0, 1.0) ** 0.7
    # 軽くなめらかに
    k = np.array([0.25, 0.5, 0.25], dtype=np.float32)
    return np.convolve(env, k, mode="same")


def fake_envelope(spans, n_frames):
    rnd = random.Random(11)
    phase = [rnd.uniform(0, 6.28) for _ in spans]
    env = np.zeros(n_frames, dtype=np.float32)
    for i in range(n_frames):
        t = i / float(FPS)
        for j, (s, e) in enumerate(spans):
            if s <= t < e:
                v = 0.5 + 0.5 * math.sin(2 * math.pi * 5.5 * t + phase[j])
                env[i] = max(0.0, v) ** 1.5
    return env


# --- フレーム描画 -----------------------------------------------------------
def subtitle_at(spans, t):
    for i, (s, e) in enumerate(spans):
        if s - 0.25 <= t < e + (GAP - 0.1):
            return script.SEGMENTS[i]["subtitle"]
    if t >= spans[-1][1]:
        return script.SEGMENTS[-1]["subtitle"]
    return script.SEGMENTS[0]["subtitle"]


def speak_at(spans, t):
    for s, e in spans:
        if s - 0.2 <= t < e + 0.2:
            return 1.0
    return 0.25


def render_frames(frames_dir, spans, env, n_frames):
    bg = R.make_background()
    blinks = R.blink_schedule(DURATION)
    for i in range(n_frames):
        t = i / float(FPS)
        img = R.draw_frame(bg, t, DURATION, script.TITLE,
                           subtitle_at(spans, t), float(env[i]),
                           speak_at(spans, t), blinks)
        img.save(os.path.join(frames_dir, "%05d.png" % i), compress_level=1)
        if i % 60 == 0:
            print("    frame %d/%d" % (i, n_frames))


# --- BGM / ffmpeg -----------------------------------------------------------
def find_bgm():
    """ルート直下に置かれた royalty-free BGM を探す (無ければ None)。"""
    hits = []
    for ext in ("mp3", "wav", "m4a", "ogg", "flac"):
        hits += glob.glob(os.path.join(ROOT, "*." + ext))
    hits = [h for h in hits if "narration" not in os.path.basename(h).lower()]
    if not hits:
        return None
    hits.sort(key=lambda p: ("bgm" not in os.path.basename(p).lower(), p))
    return hits[0]


def encode(frames_dir, audio_path, bgm_path):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-stats",
           "-framerate", str(FPS), "-i", os.path.join(frames_dir, "%05d.png")]
    if audio_path:
        cmd += ["-i", audio_path]
    if audio_path and bgm_path:
        cmd += ["-stream_loop", "-1", "-i", bgm_path,
                "-filter_complex",
                "[2:a]volume=%.3f,afade=t=out:st=%.1f:d=1.5[bg];"
                "[1:a][bg]amix=inputs=2:duration=first:dropout_transition=0,"
                "alimiter=limit=0.95[aout]" % (BGM_VOLUME, DURATION - 1.5),
                "-map", "0:v", "-map", "[aout]"]
    elif audio_path:
        cmd += ["-map", "0:v", "-map", "1:a"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", "-r", str(FPS)]
    if audio_path:
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    cmd += ["-t", "%.3f" % DURATION, "-movflags", "+faststart", OUT_MP4]
    subprocess.run(cmd, check=True)


# --- メイン -----------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true", help="1フレームだけ書き出して終了")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)

    if args.preview:
        bg = R.make_background()
        R.draw_frame(bg, 1.7, DURATION, script.TITLE,
                     script.SEGMENTS[1]["subtitle"], 0.75, 1.0,
                     R.blink_schedule(DURATION)).save(PREVIEW_PNG)
        print("preview -> %s" % PREVIEW_PNG)
        return

    backend, backend_name = tts.pick_backend()
    print("[1/4] 音声合成: %s" % backend_name)

    workdir = tempfile.mkdtemp(prefix="stickvideo_")
    frames_dir = os.path.join(workdir, "frames")
    os.makedirs(frames_dir)
    n_frames = int(DURATION * FPS)

    try:
        audio_path, track = None, None
        if backend:
            try:
                clips, rate = synth_segments(backend, workdir)
                spans = build_timeline([d for _, d in clips])
                if spans[-1][1] > DURATION:
                    print("  警告: 音声が30秒に収まらないため末尾を切り詰めます")
                audio_path, track = build_track(clips, spans, workdir)
            except Exception as e:                      # 合成が転んでも動画は作る
                print("  音声合成に失敗: %s -> 字幕のみで続行" % e)
                backend, backend_name = None, "音声なし (字幕のみ)"
        if not backend:
            spans = fallback_timeline()

        env = mouth_envelope(track, n_frames) if track is not None \
            else fake_envelope(spans, n_frames)

        print("[2/4] セグメント割り当て")
        for i, (s, e) in enumerate(spans):
            print("  %d: %5.2fs - %5.2fs  %s" % (i, s, e,
                  script.SEGMENTS[i]["subtitle"].replace("\n", " / ")))

        print("[3/4] フレーム描画 (%d枚)" % n_frames)
        render_frames(frames_dir, spans, env, n_frames)

        bgm = find_bgm()
        print("[4/4] ffmpeg 結合 (BGM: %s)" % (os.path.basename(bgm) if bgm else "なし"))
        encode(frames_dir, audio_path, bgm)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print("\n完成: %s" % OUT_MP4)
    print("音声: %s" % backend_name)


if __name__ == "__main__":
    main()
