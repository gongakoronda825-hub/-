"""冒頭に差し込む舞台映像（カーテンコール）を 1080x1920 の縦動画にし、本編の前につなげる。元の映像の音はそのまま使う。

使い方: python3 opening.py <コマのフォルダ> <音声.wav> <本編.mp4> <出力.mp4> [ロゴ.png]
ロゴを渡すと、舞台の背景の前・出演者の後ろ（明るい所＝人を避ける）に、画面に固定して重ねる。
コマは 30fps で o_001.jpg〜 の名前で書き出しておく（README 参照）。
"""
import glob
import subprocess
import sys

import imageio_ffmpeg
import numpy as np
from scipy import ndimage
from PIL import Image, ImageFilter

W, H, FPS = 1080, 1920, 30
frames_dir, audio_path, main_path, out_path = sys.argv[1:5]
logo_path = sys.argv[5] if len(sys.argv) > 5 else None
frames = sorted(glob.glob(f"{frames_dir}/o_*.jpg"))
n = len(frames)


def ease_io(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ロゴ（透明PNG）。画面上の位置は固定
LOGO_W, LOGO_CY = 940, 640
if logo_path:
    _lg = Image.open(logo_path).convert("RGBA")
    LOGO = _lg.resize((LOGO_W, int(_lg.height * LOGO_W / _lg.width)), Image.LANCZOS)
    LOGO_X, LOGO_Y = (W - LOGO.width) // 2, LOGO_CY - LOGO.height // 2
    LOGO_A = np.asarray(LOGO.getchannel("A")).astype(np.float32) / 255
    LOGO_RGB = np.asarray(LOGO.convert("RGB")).astype(np.float32)


# 人の切り抜き：カメラは固定なので、全コマの中央値で「人のいない舞台」の画を作り、
# それとの差が大きい所を人とみなす（暗い髪や黒い衣装も拾える）
PLATE_SCALE = 4
if logo_path:
    _stack = []
    for _p in frames:
        _im = Image.open(_p).convert("RGB")
        _stack.append(np.asarray(_im.resize((_im.width // PLATE_SCALE, _im.height // PLATE_SCALE), Image.BILINEAR)).astype(np.int16))
    PLATE = np.median(np.stack(_stack), axis=0).astype(np.int16)
    del _stack


def person_mask(im):
    """元の映像のコマ im で、人のいる所を 0〜255 の画像で返す（元の映像と同じ大きさ）"""
    small = np.asarray(im.resize((im.width // PLATE_SCALE, im.height // PLATE_SCALE), Image.BILINEAR)).astype(np.int16)
    diff = np.abs(small - PLATE).max(axis=2).astype(np.float32)
    m = np.clip((diff - 14) / 14, 0, 1)
    # 照明の変化で舞台セット（柱など）が拾われるのを防ぐため、画面の下（舞台の床）から
    # つながっている部分だけを人とみなす
    lab, _ = ndimage.label(m > 0.3)
    keep = np.isin(lab, np.unique(lab[-8:][lab[-8:] > 0]))
    m = m * ndimage.binary_dilation(keep, iterations=2)
    mi = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MedianFilter(3)).filter(ImageFilter.MaxFilter(3))
    return mi.resize(im.size, Image.BILINEAR).filter(ImageFilter.GaussianBlur(2))


def put_logo_behind_people(frame, mask):
    """ロゴを、人のいない所（舞台の背景）にだけ描く。mask は画面全体の人の範囲"""
    x0, y0, x1, y1 = LOGO_X, LOGO_Y, LOGO_X + LOGO.width, LOGO_Y + LOGO.height
    person = np.asarray(mask.crop((x0, y0, x1, y1))).astype(np.float32) / 255
    a = (LOGO_A * (1 - person))[..., None]
    base = np.asarray(frame.crop((x0, y0, x1, y1))).astype(np.float32)
    out = base * (1 - a) + LOGO_RGB * a
    frame.paste(Image.fromarray(out.astype(np.uint8)), (x0, y0))
    return frame


def compose(i):
    im = Image.open(frames[i]).convert("RGB")
    # 余白は同じ映像のぼかしで埋める
    s = max(W / im.width, H / im.height) * 1.05
    small = im.resize((im.width // 4, im.height // 4))
    bg = small.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.BILINEAR)
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    bg = Image.eval(bg.filter(ImageFilter.GaussianBlur(40)), lambda v: int(v * 0.4))
    # 映像は高さ 1000px で大きく置き、中央（千尋）を中心に左右へ少しだけパン
    fh = 1000
    fw = int(im.width * fh / im.height)
    fg = im.resize((fw, fh), Image.LANCZOS)
    k = ease_io(i / max(n - 1, 1))
    x = -(fw - W) * (0.38 + 0.24 * k)
    bg.paste(fg, (int(x), (H - fh) // 2))
    if logo_path:
        mask = Image.new("L", (W, H), 0)
        mask.paste(person_mask(im).resize((fw, fh), Image.BILINEAR), (int(x), (H - fh) // 2))
        bg = put_logo_behind_people(bg, mask)
    return bg


ff = imageio_ffmpeg.get_ffmpeg_exe()
tmp = out_path + ".opening.mp4"
enc = [ff, "-y", "-loglevel", "error",
       "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
       "-i", audio_path,
       "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p",
       "-af", "loudnorm=I=-16:TP=-1.5,afade=t=out:st=%.2f:d=0.12" % (n / FPS - 0.12),
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-shortest", tmp]
proc = subprocess.Popen(enc, stdin=subprocess.PIPE)
for i in range(n):
    proc.stdin.write(compose(i).tobytes())
proc.stdin.close()
proc.wait()

# 冒頭の映像 → 本編 の順につなぐ
subprocess.run([ff, "-y", "-loglevel", "error", "-i", tmp, "-i", main_path,
                "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]",
                "-map", "[v]", "-map", "[a]",
                "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS),
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out_path], check=True)
