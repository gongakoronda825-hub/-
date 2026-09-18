#!/usr/bin/env python3
"""棒人間が歴史・雑学を1つ紹介する30秒動画を作る (ノート落書き風)。

  python3 napoleon-video/make_video.py            # 通常
  python3 napoleon-video/make_video.py --preview  # 1枚だけ output/preview.png に出す

台本 -> ナレーション合成 -> PNG連番の描画 -> ffmpeg で MP4。
絵は 10fps のパラパラで描き、ffmpeg で 30fps に伸ばす。
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
FPS = 30                   # 出力動画のfps
ANIM_FPS = 10              # 絵を描き直すfps (パラパラ漫画の感じ)
DURATION = 30.0            # 秒
INTRO = 0.7                # 最初のナレーションが始まるまで
OUTRO_MIN = 1.2            # 最後のナレーション後の余韻
GAP = 0.45                 # 文と文のあいだ
MARK_DELAY = 1.5           # 字幕が出てから強調を書き足すまで
MARK_DRAW = 0.7            # 強調を書き終えるまでの時間
FIG_DELAY = 0.15           # 図解を描き始めるまで
FIG_DRAW = 2.4             # 図解を描き終えるまでの時間
TURN_DUR = 0.42            # ページをめくる時間
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


def polish_track(path, workdir):
    """こもりを取り、明瞭度を上げ、音量をそろえる。"""
    out = os.path.join(workdir, "narration_fx.wav")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-af",
             "highpass=f=75,"
             "equalizer=f=260:t=q:w=1.0:g=-2.5,"     # こもりを削る
             "equalizer=f=2800:t=q:w=1.2:g=3.0,"     # 子音を立てる
             "acompressor=threshold=-18dB:ratio=3:attack=10:release=220,"
             "alimiter=limit=0.95",
             "-ar", str(SAMPLE_RATE), "-ac", "1", out], check=True)
    except Exception as e:
        print("  音声の仕上げをスキップ: %s" % e)
        return path, read_wav_mono(path)
    # コンプで下がった分を戻す
    a = read_wav_mono(out)
    peak = float(np.max(np.abs(a)))
    if peak > 0:
        a = a * (0.94 / peak)
        write_wav_mono(out, a)
    print("  音声を整えました (ピーク %.2f -> 0.94)" % peak)
    return out, a


# --- 口パク -----------------------------------------------------------------
def mouth_envelope(track, n_steps):
    """音の大きさから各ステップの口の開き(0-1)を作る。"""
    win = int(SAMPLE_RATE / ANIM_FPS)
    env = np.zeros(n_steps, dtype=np.float32)
    for i in range(n_steps):
        chunk = track[i * win:(i + 1) * win]
        if len(chunk):
            env[i] = float(np.sqrt(np.mean(chunk ** 2)))
    if env.max() > 0:
        env = env / env.max()
    return np.clip(env * 2.4, 0.0, 1.0) ** 0.7


def fake_envelope(spans, n_steps):
    rnd = random.Random(11)
    phase = [rnd.uniform(0, 6.28) for _ in spans]
    env = np.zeros(n_steps, dtype=np.float32)
    for i in range(n_steps):
        t = i / float(ANIM_FPS)
        for j, (s, e) in enumerate(spans):
            if s <= t < e:
                env[i] = max(0.0, math.sin(2 * math.pi * 4.0 * t + phase[j])) ** 1.2
    return env


# --- タイミング -------------------------------------------------------------
def turn_start(spans, i):
    """セグメント i を出すためにページをめくり始める時刻。"""
    return spans[i][0] - TURN_DUR - 0.05


def segment_at(spans, t):
    """その時刻に表示しているセグメントの番号 (めくり始めた時点で次に切り替わる)。"""
    idx = 0
    for i in range(1, len(spans)):
        if t >= turn_start(spans, i):
            idx = i
    return idx


def transition_at(spans, t):
    """ページめくりの最中なら (めくる前のセグメント番号, 進み具合0-1)。"""
    for i in range(1, len(spans)):
        t0 = turn_start(spans, i)
        if t0 <= t < t0 + TURN_DUR:
            return i - 1, (t - t0) / TURN_DUR
    return None


def reveal_at(spans, i, t):
    """書き足しの進み具合 (0-1)。図解ページは早く長めに描く。"""
    if script.SEGMENTS[i].get("art") == "figure":
        delay, draw = FIG_DELAY, FIG_DRAW
    else:
        delay, draw = MARK_DELAY, MARK_DRAW
    return max(0.0, min(1.0, (t - spans[i][0] - delay) / draw))


def speak_at(spans, t):
    return 1.0 if any(s - 0.2 <= t < e + 0.2 for s, e in spans) else 0.25


# --- 描画 -------------------------------------------------------------------
def compose(bg, spans, seg_i, t, mouth, speak, blinks, step):
    seg = script.SEGMENTS[seg_i]
    return R.draw_frame(bg, t, DURATION, script.TITLE_LINES, script.TAG,
                        seg["subtitle"], seg.get("marks"),
                        reveal_at(spans, seg_i, t), mouth,
                        speak, blinks, step, art=seg.get("art", "character"))


def render_steps(frames_dir, spans, env, n_steps):
    bg = R.make_background()
    blinks = R.blink_schedule(DURATION)
    for i in range(n_steps):
        t = i / float(ANIM_FPS)
        mouth, speak = float(env[i]), speak_at(spans, t)
        turn = transition_at(spans, t)
        if turn:                                  # ページをめくっている最中
            prev_i, p = turn
            before = compose(bg, spans, prev_i, t, mouth, speak, blinks, i)
            after = compose(bg, spans, prev_i + 1, t, mouth, speak, blinks, i)
            img = R.page_turn(before, after, p)
        else:
            img = compose(bg, spans, segment_at(spans, t), t,
                          mouth, speak, blinks, i)
        img.save(os.path.join(frames_dir, "%05d.png" % i), compress_level=1)
        if i % 30 == 0:
            print("    step %d/%d" % (i, n_steps))


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
           "-framerate", str(ANIM_FPS), "-i", os.path.join(frames_dir, "%05d.png")]
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
    ap.add_argument("--preview", action="store_true", help="1枚だけ書き出して終了")
    ap.add_argument("--at", type=float, default=8.0, help="--preview で描く時刻(秒)")
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)

    if args.preview:
        spans = fallback_timeline()
        t = args.at
        bg, blinks, step = R.make_background(), R.blink_schedule(DURATION), int(t * ANIM_FPS)
        turn = transition_at(spans, t)
        if turn:
            prev_i, p = turn
            img = R.page_turn(compose(bg, spans, prev_i, t, 0.7, 1.0, blinks, step),
                              compose(bg, spans, prev_i + 1, t, 0.7, 1.0, blinks, step), p)
        else:
            img = compose(bg, spans, segment_at(spans, t), t, 0.7, 1.0, blinks, step)
        img.save(PREVIEW_PNG)
        print("preview (%.1fs) -> %s" % (t, PREVIEW_PNG))
        return

    backend, backend_name = tts.pick_backend()
    print("[1/4] 音声合成: %s" % backend_name)

    workdir = tempfile.mkdtemp(prefix="stickvideo_")
    frames_dir = os.path.join(workdir, "frames")
    os.makedirs(frames_dir)
    n_steps = int(DURATION * ANIM_FPS)

    try:
        audio_path, track = None, None
        if backend:
            try:
                clips, rate = synth_segments(backend, workdir)
                spans = build_timeline([d for _, d in clips])
                if spans[-1][1] > DURATION:
                    print("  警告: 音声が30秒に収まらないため末尾を切り詰めます")
                audio_path, track = build_track(clips, spans, workdir)
                audio_path, track = polish_track(audio_path, workdir)
            except Exception as e:                      # 合成が転んでも動画は作る
                print("  音声合成に失敗: %s -> 字幕のみで続行" % e)
                backend, backend_name = None, "音声なし (字幕のみ)"
        if not backend:
            spans = fallback_timeline()

        env = mouth_envelope(track, n_steps) if track is not None \
            else fake_envelope(spans, n_steps)

        print("[2/4] セグメント割り当て")
        for i, (s, e) in enumerate(spans):
            print("  %d: %5.2fs - %5.2fs  %s" % (i, s, e,
                  " / ".join(script.SEGMENTS[i]["subtitle"])))

        print("[3/4] 作画 (%dステップ = %dfps のパラパラ)" % (n_steps, ANIM_FPS))
        render_steps(frames_dir, spans, env, n_steps)

        bgm = find_bgm()
        print("[4/4] ffmpeg 結合 (BGM: %s)" % (os.path.basename(bgm) if bgm else "なし"))
        encode(frames_dir, audio_path, bgm)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)

    print("\n完成: %s" % OUT_MP4)
    print("音声: %s" % backend_name)


if __name__ == "__main__":
    main()
