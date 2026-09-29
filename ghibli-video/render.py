"""マイナーだけどおすすめなジブリ映画3選 — TikTok 縦動画レンダラー

images/ の20枚から 1080x1920 / 30fps の mp4 を作る。
audio/timeline.json があれば、カットの長さをナレーションに合わせる (なければ下のカット表の秒数)。
使い方: python3 ghibli-video/render.py
"""
import json
import math
import subprocess
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "images"
OUT = ROOT / "output"
HERE = Path(__file__).resolve().parent
FONT = HERE / "fonts" / "NotoSansJP.ttf"
EMOJI = HERE / "fonts" / "emoji_1f447.png"

W, H, FPS = 1080, 1920, 30
PANEL_H = round(W * 1038 / 1920)  # 横長画像を横幅いっぱいに置いたときの高さ (584)
TELOP_Y = 1350                    # 通常テロップの中心 (画面中央よりやや下)
RANK_Y = 470                      # 順位テロップの中心 (上部)

# ---- カット表 -------------------------------------------------------------
# (開始秒, 終了秒, 画像, テロップ, 動き, 追加演出)
#   動き: zoom / fastzoom / slowzoom / pan_r / pan_l
#   画像: ファイル名 / ("flip", [...]) 高速切替 / ("stack", [...]) 縦3分割
HOOK = ["umi_01", "kokuriko_01", "marnie_01"]
CUTS = [
    (4, 7, ("stack", HOOK), "マイナーだけどおすすめな\nジブリ映画3選", "slowzoom", {}),
    (7, 9, "marnie_02", "思い出のマーニー", "zoom", {"rank": "第3位", "flash": 8}),
    (9, 12, "marnie_03", "心を閉ざした少女・杏奈", "zoom", {}),
    (12, 15, "marnie_04", "北海道の海辺の屋敷で", "pan_r", {}),
    (15, 18, "marnie_05", "金髪の少女マーニー", "zoom", {}),
    (18, 21, "marnie_06", "二人に隠された秘密", "pan_l", {}),
    (21, 23, "marnie_07", "最後は涙が止まらない", "zoom", {"darken": True}),
    (23, 25, "kokuriko_02", "コクリコ坂から", "zoom", {"rank": "第2位", "flash": 8}),
    (25, 28, "kokuriko_03", "1963年・横浜", "pan_r", {}),
    (28, 31, "kokuriko_04", "毎朝旗を揚げる少女・海", "zoom", {}),
    (31, 34, "kokuriko_05", "少年・俊との甘酸っぱい恋", "pan_l", {}),
    (34, 37, "kokuriko_06", "古い部室棟カルチェラタン", "zoom", {}),
    (37, 39, "kokuriko_07", "昭和レトロな空気が最高", "pan_r", {}),
    (39, 42, "umi_02", "海がきこえる", "zoom", {"rank": "第1位", "flash": 14}),
    (42, 45, "umi_03", "実はテレビ用に作られた幻の作品", "pan_l", {}),
    (45, 48, "umi_04", "高知の高校生・拓", "zoom", {}),
    (48, 52, "umi_05", "東京から来た転校生・里伽子", "slowzoom", {}),
    (52, 55, "umi_06", "リアルな青春が刺さる", "pan_r", {}),
    (55, 60, ("stack", ["marnie_05", "kokuriko_04", "umi_05"]), "どれか観たことある？", "zoom",
     {"emoji": True, "labels": ["思い出のマーニー", "コクリコ坂から", "海がきこえる"]}),
]


def retime(cuts, timeline_path):
    """ナレーションの区間 (audio/timeline.json) に合わせてカットの秒数を決め直す。区間とカットは1対1"""
    if not timeline_path.exists():
        return cuts
    segs = json.loads(timeline_path.read_text())
    assert len(segs) == len(cuts), "timeline.json の区間数がカット表と合わない"
    return [(seg["start"], seg["end"]) + c[2:] for seg, c in zip(segs, cuts)]


CUTS = retime(CUTS, ROOT / "audio" / "timeline.json")
DON_TIMES = [c[0] for c in CUTS if "rank" in c[5]]


# ---- 素材の準備 -----------------------------------------------------------
def font(size, weight=b"Black"):
    f = ImageFont.truetype(str(FONT), size)
    f.set_variation_by_name(weight)
    return f


_src, _bg = {}, {}


def src(name):
    if name not in _src:
        _src[name] = Image.open(IMG / f"{name}.jpg").convert("RGB")
    return _src[name]


def blurred_bg(name):
    """同じ画像を画面いっぱいに拡大してぼかした背景"""
    if name not in _bg:
        im = src(name)
        s = H / im.height
        big = im.resize((math.ceil(im.width * s), H), Image.BILINEAR)
        x = (big.width - W) // 2
        big = big.crop((x, 0, x + W, H)).filter(ImageFilter.GaussianBlur(40))
        _bg[name] = ImageEnhance.Brightness(big).enhance(0.6)
    return _bg[name]


def ease_out(t):
    return 1 - (1 - t) ** 3


def panel(name, motion, t, w=W, h=PANEL_H):
    """画像の中でズーム/パンする (Ken Burns)。t は 0..1"""
    im = src(name)
    if motion == "fastzoom":
        z = 1.0 + 0.2 * ease_out(t)
    elif motion in ("zoom", "slowzoom"):
        z = 1.0 + 0.1 * t
    else:
        z = 1.1
    cw, ch = im.width / z, im.height / z
    cy = (im.height - ch) / 2
    if motion == "pan_r":      # カメラが右へ動く
        cx = (im.width - cw) * t
    elif motion == "pan_l":
        cx = (im.width - cw) * (1 - t)
    else:
        cx = (im.width - cw) / 2
    return im.resize((w, h), Image.BICUBIC, box=(cx, cy, cx + cw, cy + ch))


def text_layer(text, size, max_w=1000, stroke=None, line_gap=1.25):
    """白文字＋黒フチのテロップを RGBA で作る"""
    lines = text.split("\n")
    while True:
        f = font(size)
        sw = stroke if stroke is not None else max(6, size // 8)
        widths = [f.getbbox(l, stroke_width=sw)[2] for l in lines]
        if max(widths) <= max_w or size <= 30:
            break
        size -= 2
    lh = int(size * line_gap)
    im = Image.new("RGBA", (max(widths) + 20, lh * len(lines) + sw * 2 + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        x = (im.width - widths[i]) // 2
        d.text((x, 10 + i * lh), l, font=f, fill="white", stroke_width=sw, stroke_fill="black")
    return im


def with_emoji(layer, emoji_size):
    em = Image.open(EMOJI).convert("RGBA").resize((emoji_size, emoji_size), Image.LANCZOS)
    out = Image.new("RGBA", (layer.width + emoji_size + 8, max(layer.height, emoji_size)), (0, 0, 0, 0))
    out.alpha_composite(layer, (0, (out.height - layer.height) // 2))
    out.alpha_composite(em, (layer.width + 4, (out.height - emoji_size) // 2 - 4))
    return out


def paste_center(frame, layer, cy, scale=1.0, alpha=1.0):
    if scale != 1.0:
        layer = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        a = layer.getchannel("A").point(lambda v: int(v * alpha))
        layer = layer.copy()
        layer.putalpha(a)
    frame.alpha_composite(layer, ((W - layer.width) // 2, int(cy - layer.height / 2)))


# ---- 1フレーム描画 --------------------------------------------------------
def build_layers(cut):
    s, e, img, telop, motion, fx = cut
    L = {}
    if telop:
        stacked = isinstance(img, tuple) and img[0] == "stack"
        L["telop"] = text_layer(telop, 84 if ("rank" in fx or stacked) else 70)
        if fx.get("emoji"):
            L["telop"] = with_emoji(L["telop"], 90)
        if stacked:  # 写真の上に重ねるので半透明の帯を敷く
            t = L["telop"]
            band = Image.new("RGBA", (W, t.height + 40), (0, 0, 0, 150))
            band.alpha_composite(t, ((W - t.width) // 2, 20))
            L["telop"] = band
    if "rank" in fx:
        L["rank"] = text_layer(fx["rank"], 210, stroke=16)
    if "labels" in fx:
        L["labels"] = [text_layer(t, 40, stroke=6) for t in fx["labels"]]
    return L


def render_frame(cut, layers, i, n):
    s, e, img, telop, motion, fx = cut
    t = i / max(1, n - 1)
    sec = i / FPS

    if isinstance(img, tuple) and img[0] == "stack":
        names = img[1]
        frame = Image.new("RGBA", (W, H), (12, 12, 12, 255))
        frame.alpha_composite(blurred_bg(names[1]).convert("RGBA"))
        gap = 12
        top = (H - 3 * PANEL_H - 2 * gap) // 2
        for k, nm in enumerate(names):
            p = panel(nm, motion if motion != "slowzoom" else "zoom", t * (0.6 if motion == "slowzoom" else 1))
            frame.paste(p, (0, top + k * (PANEL_H + gap)))
            if "labels" in layers:
                lab = layers["labels"][k]
                frame.alpha_composite(lab, (16, top + k * (PANEL_H + gap) + PANEL_H - lab.height - 6))
        telop_y = H // 2
    else:
        if isinstance(img, tuple) and img[0] == "flip":
            name = img[1][(i // 5) % len(img[1])]
        else:
            name = img
        frame = blurred_bg(name).convert("RGBA")
        frame.paste(panel(name, motion, t), (0, (H - PANEL_H) // 2))
        telop_y = TELOP_Y

    if fx.get("darken"):
        k = 1 - 0.75 * (t ** 1.6)
        frame = Image.eval(frame.convert("RGB"), lambda v: int(v * k)).convert("RGBA")

    if "rank" in layers:
        pop = min(1.0, sec / 0.2)
        paste_center(frame, layers["rank"], RANK_Y, scale=1.35 - 0.35 * ease_out(pop))
    if "telop" in layers:
        delay = 0.25 if "rank" in fx else 0.0
        a = min(1.0, max(0.0, (sec - delay) / 0.15))
        if a > 0:
            paste_center(frame, layers["telop"], telop_y, alpha=a)

    if fx.get("flash") and i < fx["flash"]:
        a = int(255 * (1 - i / fx["flash"]) ** 1.5)
        frame.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, a)))
    return frame.convert("RGB")


# ---- 効果音 (効果音ラボ https://soundeffect-lab.info/) --------------------
# (秒, ファイル, 音量倍率)
SFX = [(CUTS[0][0], "jean1.mp3", 0.9)]                                    # タイトル「ジャン！」
SFX += [(t, "drum-japanese2.mp3", 1.0) for t in DON_TIMES]          # 順位発表「和太鼓でドドン」
SFX += [(CUTS[-1][0], "kira1.mp3", 0.8)]                                   # 締め「キラッ」


def load_sfx(name, sr):
    path = HERE / "sfx" / name
    if not path.exists():  # 素材の再配布は規約で禁止なのでリポジトリには置かず、毎回サイトから取る
        path.parent.mkdir(exist_ok=True)
        subprocess.run(["curl", "-sSf", "-A", "Mozilla/5.0", "-e", "https://soundeffect-lab.info/sound/anime/",
                        "-o", str(path), f"https://soundeffect-lab.info/sound/anime/mp3/{name}"], check=True)
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-i", str(HERE / "sfx" / name),
                          "-f", "s16le", "-ac", "1", "-ar", str(sr), "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, "<i2").astype(np.float64) / 32768
    idx = np.nonzero(np.abs(a) > 0.02)[0]
    return a[max(0, idx[0] - 100):] if len(idx) else a   # 頭の無音を切って映像とぴったり合わせる


# ---- BGM (各順位の説明中に流す作品の曲。著作物なのでリポジトリには置かない) ----
BGM = {"第3位": "marnie.m4a", "第2位": "kokuriko.m4a", "第1位": "umi.m4a"}
BGM_GAIN = 0.28      # ナレーションが聞こえるように下げる
BGM_FADE_OUT = 0.5


def decode(path, sr, channels):
    raw = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-loglevel", "error", "-i", str(path),
                          "-f", "s16le", "-ac", str(channels), "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, "<i2").astype(np.float64).reshape(-1, channels) / 32768


def bgm_sections():
    """順位発表のカットから、次の順位発表 (最後はエンディング) の直前までを1区間にする"""
    starts = [(c[0], c[5]["rank"]) for c in CUTS if "rank" in c[5]]
    ends = [s for s, _ in starts[1:]] + [CUTS[-1][0]]
    return [(s, e, BGM[r]) for (s, r), e in zip(starts, ends)]


def make_audio(path, total):
    sr = 44100
    buf = np.zeros((int(sr * total), 2), dtype=np.float64)

    def add(clip, t):
        a = int(t * sr)
        n = min(len(clip), len(buf) - a)
        buf[a:a + n] += clip[:n]

    narration = ROOT / "audio" / "narration.mp3"
    if narration.exists():
        add(decode(narration, sr, 2), 0.0)
    for t, name, gain in SFX:
        add(np.repeat(load_sfx(name, sr)[:, None], 2, axis=1) * gain, t)
    for s, e, name in bgm_sections():
        f = HERE / "bgm" / name
        if not f.exists():
            print("BGM なし:", f)
            continue
        clip = decode(f, sr, 2)
        idx = np.nonzero(np.abs(clip).max(axis=1) > 0.01)[0]
        clip = clip[idx[0]:] if len(idx) else clip        # 画面録画の頭の無音を切る
        n = int((e - s) * sr)
        clip = clip[:n] * BGM_GAIN
        env = np.ones(len(clip))
        fi, fo = int(0.05 * sr), int(BGM_FADE_OUT * sr)
        env[:fi] = np.linspace(0, 1, fi)
        env[-fo:] = np.minimum(env[-fo:], np.linspace(1, 0, fo))
        add(clip * env[:, None], s)

    pcm = (np.clip(buf, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def main():
    OUT.mkdir(exist_ok=True)
    total = CUTS[-1][1]
    wav = OUT / "_mix.wav"
    make_audio(wav, total)  # ナレーション・効果音・BGM をまとめたステレオ音声

    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", str(wav)]
    cmd += ["-map", "0:v", "-map", "1:a", "-af", "alimiter=limit=0.89:level=false"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-t", str(total), "-movflags", "+faststart",
            str(OUT / "ghibli_minor3.mp4")]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    for c, cut in enumerate(CUTS):
        n = round(cut[1] * FPS) - round(cut[0] * FPS)
        layers = build_layers(cut)
        for i in range(n):
            proc.stdin.write(render_frame(cut, layers, i, n).tobytes())
        print(f"cut {c + 1:2d}/{len(CUTS)} done ({cut[0]}-{cut[1]}s, {n} frames)", flush=True)
    proc.stdin.close()
    proc.wait()
    wav.unlink()
    print("->", OUT / "ghibli_minor3.mp4")


if __name__ == "__main__":
    main()
