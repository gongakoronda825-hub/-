"""画像・ナレーション・効果音・テロップを合わせて 1080x1920 の mp4 を書き出す。

映像のフレームは PIL で描いて ffmpeg にパイプし、テロップと字幕は ffmpeg の ass フィルタで焼き込む。
"""
import json
import math
import subprocess
import sys

from PIL import Image, ImageEnhance, ImageFilter, ImageFont

from script import SCENES

B = "build"
OUT = sys.argv[1] if len(sys.argv) > 1 else "mimi_imax_tiktok.mp4"
W, H, FPS = 1080, 1920, 30
LEAD, TAIL, LAST_TAIL = 0.12, 0.28, 0.7  # 各シーンの前後の間（秒）
XFADE = 0.22  # 画像の切り替えのクロスフェード（秒）
FG_H = round(W * 1038 / 1920)  # 横長画像を幅いっぱいに置いたときの高さ
FG_Y = 690  # 中央の画像の上端（テロップと字幕の間に収まる位置）
FONT_DIR = "fonts"
TELOP_FONT = "fonts/NotoSansCJKjp-Black.otf"

timing = json.load(open(f"{B}/timing.json"))

# ---- タイムライン -------------------------------------------------------------
scenes, t = [], 0.0
for i, (sc, tm) in enumerate(zip(SCENES, timing)):
    speech = tm["words"][-1]["end"]
    dur = LEAD + speech + (LAST_TAIL if i == len(SCENES) - 1 else TAIL)
    subs = tm["subs"]
    for k, c in enumerate(subs):
        c["abs"] = t + LEAD + c["start"]
        c["end"] = t + LEAD + subs[k + 1]["start"] if k + 1 < len(subs) else t + dur - 0.05
    scenes.append({"start": t, "end": t + dur, "narr_at": t + LEAD, **sc, "subs": subs})
    t += dur
TOTAL = t

# シーン内で画像が2枚あるときは、真ん中に一番近い字幕の切れ目で切り替える
segments = []
for i, sc in enumerate(scenes):
    imgs = sc["image"] if isinstance(sc["image"], list) else [sc["image"]]
    if len(imgs) == 1:
        segments.append((sc["start"], sc["end"], imgs[0]))
    else:
        mid = (sc["start"] + sc["end"]) / 2
        cut = min((c["abs"] for c in sc["subs"][1:]), key=lambda x: abs(x - mid))
        segments.append((sc["start"], cut, imgs[0]))
        segments.append((cut, sc["end"], imgs[1]))

# ---- 画像の下ごしらえ ----------------------------------------------------------
cache = {}


def load(name):
    if name not in cache:
        src = Image.open(f"{B}/img/{name}").convert("RGB")
        # 背景: 縦いっぱいに拡大してぼかし、少し暗くする（半分の解像度で持って描画時に拡大）
        s = (H / 2) / src.height
        bg = src.resize((round(src.width * s), H // 2), Image.LANCZOS)
        x0 = (bg.width - W // 2) // 2
        bg = bg.crop((x0, 0, x0 + W // 2, H // 2)).filter(ImageFilter.GaussianBlur(18))
        bg = ImageEnhance.Brightness(bg).enhance(0.55)
        cache[name] = (src, bg)
    return cache[name]


def ease(u):
    return 0.5 - 0.5 * math.cos(math.pi * min(max(u, 0), 1))


def render(seg_idx, tt):
    a, b, name = segments[seg_idx]
    src, bg = load(name)
    u = (tt - a) / (b - a)
    # 背景もごくゆっくり寄る
    zb = 1.0 + 0.06 * u
    cx, cy = W / 4, H / 4
    frame = bg.transform(
        (W, H), Image.AFFINE,
        (1 / (2 * zb), 0, cx - W / (4 * zb), 0, 1 / (2 * zb), cy - H / (4 * zb)),
        Image.BILINEAR,
    )
    # 前景: Ken Burns。偶数番目はズームイン＋右へ、奇数番目はズームアウト＋左へ
    zin = seg_idx % 2 == 0
    z = 1.0 + 0.12 * (ease(u) if zin else 1 - ease(u))
    pan = (0.5 + 0.35 * (ease(u) - 0.5) * (1 if zin else -1))
    k = W / src.width * z  # 出力1pxあたりの拡大率
    vw, vh = W / k, FG_H / k  # 元画像上の見える範囲
    x0 = (src.width - vw) * pan
    y0 = (src.height - vh) / 2
    fg = src.transform((W, FG_H), Image.AFFINE, (1 / k, 0, x0, 0, 1 / k, y0), Image.BICUBIC)
    frame.paste(fg, (0, FG_Y))
    return frame


def frame_at(tt):
    for i, (a, b, _) in enumerate(segments):
        if a <= tt < b or i == len(segments) - 1:
            break
    img = render(i, tt)
    # 切り替えの前後 XFADE/2 ずつで次の画像と重ねる
    if i + 1 < len(segments) and tt > b - XFADE / 2:
        w = (tt - (b - XFADE / 2)) / XFADE
        img = Image.blend(img, render(i + 1, tt), w)
    elif i > 0 and tt < a + XFADE / 2:
        w = (tt - (a - XFADE / 2)) / XFADE
        img = Image.blend(render(i - 1, tt), img, w)
    return img


# ---- テロップと字幕（ASS） ------------------------------------------------------
def ts(x):
    cs = round(x * 100)
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def telop_size(text):
    """一番長い行が幅 980px に収まる最大の文字サイズ（上限 118）。"""
    for size in range(118, 40, -2):
        f = ImageFont.truetype(TELOP_FONT, size)
        if max(f.getlength(line) for line in text.split("\n")) <= 980:
            return size
    return 40


ass = [
    "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {W}", f"PlayResY: {H}", "WrapStyle: 2",
    "ScaledBorderAndShadow: yes", "",
    "[V4+ Styles]",
    "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
    "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, "
    "MarginR, MarginV, Encoding",
    "Style: Telop,Noto Sans CJK JP Black,100,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,2,0,1,9,4,8,40,40,250,1",
    "Style: Sub,Noto Sans CJK JP Bold,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,0,0,0,0,100,100,0,0,1,6,2,2,40,40,"
    f"{H - 1500},1",
    "",
    "[Events]",
    "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
]
for sc in scenes:
    size = telop_size(sc["telop"])
    pop = r"{\fs%d\fscx60\fscy60\t(0,140,\fscx112\fscy112)\t(140,240,\fscx100\fscy100)}" % size
    text = sc["telop"].replace("\n", r"\N")
    ass.append(f"Dialogue: 1,{ts(sc['start'] + 0.04)},{ts(sc['end'])},Telop,,0,0,0,,{pop}{text}")
    for c in sc["subs"]:
        line = c["text"].replace("\n", r"\N")
        ass.append(f"Dialogue: 0,{ts(c['abs'])},{ts(c['end'])},Sub,,0,0,0,,{line}")
open(f"{B}/captions.ass", "w").write("\n".join(ass) + "\n")

# ---- 音（ナレーション＋効果音） -----------------------------------------------
inputs, chains = [], []


def add(path, at, vol):
    n = len(chains)
    inputs.extend(["-i", path])
    ms = max(0, round(at * 1000))
    chains.append(f"[{n + 1}:a]aresample=48000,aformat=channel_layouts=stereo,volume={vol},adelay={ms}:all=1[a{n}]")


for i, sc in enumerate(scenes):
    add(f"{B}/narr{i}.mp3", sc["narr_at"], 1.0)
    if i == 0:
        add(f"{B}/impact.wav", 0.0, 0.55)
    else:
        add(f"{B}/whoosh.wav", sc["start"] - 0.27, 0.45)
    if i == len(scenes) - 1:
        add(f"{B}/chime.wav", sc["start"] + 0.05, 0.3)
    else:
        add(f"{B}/pop.wav", sc["start"] + 0.05, 0.35)
# シーン内の画像切り替えにも軽い「シュッ」
for a, b, _ in segments[1:]:
    if all(abs(a - sc["start"]) > 0.01 for sc in scenes):
        add(f"{B}/whoosh.wav", a - 0.27, 0.22)

mix_in = "".join(f"[a{k}]" for k in range(len(chains)))
fc = ";".join(chains) + (
    f";{mix_in}amix=inputs={len(chains)}:normalize=0,atrim=0:{TOTAL:.3f},"
    "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]"
    f";[0:v]ass={B}/captions.ass:fontsdir={FONT_DIR}[vout]"
)
cmd = [
    "ffmpeg", "-v", "error", "-y",
    "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
    *inputs,
    "-filter_complex", fc, "-map", "[vout]", "-map", "[aout]",
    "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high",
    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{TOTAL:.3f}", OUT,
]
proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
n = math.ceil(TOTAL * FPS)
for f in range(n):
    proc.stdin.write(frame_at(f / FPS).tobytes())
proc.stdin.close()
sys.exit(proc.wait())
