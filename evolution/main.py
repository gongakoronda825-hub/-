"""CLI: run the evolution, then draw it.

    python3 -m evolution.main preview                  # one still -> output/preview.png
    python3 -m evolution.main video --seconds 20 --gens 14 --out output/short.mp4
    python3 -m evolution.main video                    # the real 70s cut
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

from .render import Renderer
from .sim import Params, run
from .timeline import build


def ffmpeg_bin() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def make(seed: int, gens: int, seconds: float, fps: int):
    params = Params(generations=gens)
    history, params = run(params, seed)

    outro = min(10.0, max(4.0, seconds * 0.145))
    feast = np.array([g.feast_steps for g in history])
    sched = build(feast, fps, int(round(seconds * fps)), int(round(outro * fps)))
    return Renderer(history, params, sched), history, params, sched


def cmd_preview(a):
    r, history, _, sched = make(a.seed, a.gens, a.seconds, a.fps)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    frames = a.frame if a.frame is not None else [int(sched.gens_end * 0.34)]
    for i, f in enumerate(frames):
        f = int(np.clip(f, 0, sched.total - 1))
        r.seek(f)
        img = Image.fromarray(r.render_frame(f))
        path = out if len(frames) == 1 else out.with_name(f"{out.stem}_{i}{out.suffix}")
        img.save(path)
        print(f"  {path}  (frame {f}, t={f / a.fps:.1f}s, seed={a.seed})")


def cmd_video(a):
    r, history, params, sched = make(a.seed, a.gens, a.seconds, a.fps)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    wav = None
    if not a.no_audio:
        from .audio import build_track
        wav = out.with_suffix(".wav")
        build_track(history, sched, a.fps, wav)

    cmd = [ffmpeg_bin(), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920",
           "-r", str(a.fps), "-i", "-"]
    if wav:
        cmd += ["-i", str(wav)]
    cmd += ["-map", "0:v"]
    if wav:
        cmd += ["-map", "1:a", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    total = sched.total
    for f in range(total):
        proc.stdin.write(r.render_frame(f).tobytes())
        if f % 200 == 0 and f:
            el = time.time() - t0
            print(f"  {f}/{total}  {el:.0f}s elapsed, ~{el / f * (total - f):.0f}s left",
                  flush=True)
    proc.stdin.close()
    if proc.wait() != 0:
        sys.exit("ffmpeg failed")
    if wav and not a.keep_wav:
        wav.unlink(missing_ok=True)

    meta = {
        "seed": a.seed, "generations": a.gens, "seconds": a.seconds, "fps": a.fps,
        "mean_speed_first": round(history[0].mean, 4),
        "mean_speed_last": round(history[-1].mean, 4),
        "std_first": round(history[0].std, 4), "std_last": round(history[-1].std, 4),
        "params": params.as_dict(),
    }
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"\n  {out}  ({total} frames, {time.time() - t0:.0f}s)")
    print(f"  seed {a.seed}: 平均speed {history[0].mean:.2f} -> {history[-1].mean:.2f}"
          f"   ばらつき {history[0].std:.2f} -> {history[-1].std:.2f}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="evolution")
    ap.add_argument("mode", choices=["preview", "video"])
    ap.add_argument("--seed", type=int, default=None, help="default: fresh random seed")
    ap.add_argument("--gens", type=int, default=60)
    ap.add_argument("--seconds", type=float, default=70.0)
    ap.add_argument("--fps", type=int, default=60)
    ap.add_argument("--out", default=None)
    ap.add_argument("--frame", type=int, nargs="*", default=None, help="preview: frame numbers")
    ap.add_argument("--no-audio", action="store_true")
    ap.add_argument("--keep-wav", action="store_true")
    a = ap.parse_args(argv)

    if a.seed is None:
        a.seed = random.randrange(1, 2 ** 31 - 1)
    if a.out is None:
        a.out = "output/preview.png" if a.mode == "preview" else "output/evolution.mp4"

    print(f"seed={a.seed}  gens={a.gens}  {a.seconds}s @ {a.fps}fps")
    (cmd_preview if a.mode == "preview" else cmd_video)(a)


if __name__ == "__main__":
    main()
