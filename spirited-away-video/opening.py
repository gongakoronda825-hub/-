"""冒頭に差し込む舞台映像（カーテンコール）を 1080x1920 の縦動画にし、本編の前につなげる。元の映像の音はそのまま使う。

使い方: python3 opening.py <コマのフォルダ> <音声.wav> <重ねる文字.png> <本編.mp4> <出力.mp4>
コマは 30fps で o_001.jpg〜 の名前で書き出しておく（README 参照）。
"""
import glob
import subprocess
import sys

import imageio_ffmpeg
from PIL import Image, ImageFilter

W, H, FPS = 1080, 1920, 30
frames_dir, audio_path, overlay_path, main_path, out_path = sys.argv[1:6]
# 最初のフレームから出す文字（render.py で書き出した透明PNG）
overlay = Image.open(overlay_path).convert("RGBA")
frames = sorted(glob.glob(f"{frames_dir}/o_*.jpg"))
n = len(frames)


def ease_io(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


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
    # 上に文字を置くので、映像は少し下げる
    bg.paste(fg, (int(x), 600))
    out = bg.convert("RGBA")
    out.alpha_composite(overlay)
    return out.convert("RGB")


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
