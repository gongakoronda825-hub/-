#!/usr/bin/env python3
"""TikTok用の縦動画（1080x1920）を書き出す。

背景はクロマキー用の緑一色。あとで編集アプリで好きな画像・映像に差し替える前提。
字幕はナレーション音声のモーラ長から起こしているので、声とぴったり合う。
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import captions as cap_mod  # noqa: E402
import generate_narration as gn  # noqa: E402

WIDTH, HEIGHT = 1080, 1920
FPS = 30

# クロマキー用の緑。編集アプリのキーで抜きやすい標準的な値。
CHROMA = (0, 177, 64)

TEXT_COLOR = (255, 255, 255)
SPOKEN_COLOR = (255, 210, 74)      # 読み終えた文字を金色に変えて視線を運ぶ
OUTLINE_COLOR = (16, 20, 24)       # 半透明は使わない（キーで抜くと濁るため）
OUTLINE_WIDTH = 9

FONT_SIZE = 84
LINE_SPACING = 1.30
MAX_TEXT_WIDTH = 860              # 左右の余白。右端のボタン列を避ける
MAX_LINES = 2
TEXT_CENTER_Y = 1010              # 下のキャプション欄と右のボタンを避けた高さ

# 出現時の弾み。半透明にすると緑と混ざってキーで抜けなくなるので、
# 透明度は触らず大きさと位置だけ動かす。
POP_TIME = 0.20
POP_SCALE = 0.90
POP_RISE = 16

# 冒頭のフック。字幕より大きく出して、最初の数秒で足を止めてもらう。
# 2行目の字幕（同じ題名が出る）に入れ替わるまで、これだけを見せる。
HOOK_LINES = ["君たちは", "どう生きるか"]
HOOK_TEXT = "君たちはどう生きるか"
HOOK_SIZE = 112
HOOK_COLOR = SPOKEN_COLOR
HOOK_CENTER_Y = 940

NO_LINE_START = "、。」』）,.!?ー々" + cap_mod.SMALL_KANA
NO_LINE_END = "「『（"

# 行末に来ると気持ちよく切れる助詞と、行頭に来ると読みにくい助詞。
PARTICLE_STRONG = "をがにでとへはの"
PARTICLE_SOFT = "もやから"

# 行の途中で割りたくないまとまり: 鍵括弧でくるんだ題名、カタカナ語、日付。
ATOM = re.compile(r"「[^」]*」|[ァ-ヴー]+|[0-9０-９]+[月日年時分秒円]*")

ONE_LINE_FLOOR = 66
TWO_LINE_FLOOR = 64


def atoms(text):
    """折り返しの最小単位に分ける。"""
    out, pos = [], 0
    for m in ATOM.finditer(text):
        out += list(text[pos:m.start()])
        out.append(m.group())
        pos = m.end()
    return out + list(text[pos:])


def is_kanji(ch):
    return "\u4e00" <= ch <= "\u9fff" or ch in "々〇﨑"


def split_points(text):
    """まとまりの境目と、その前後にあるまとまりの長さ。"""
    ends, starts, pos = {}, {}, 0
    for atom in atoms(text):
        starts[pos] = len(atom)
        pos += len(atom)
        ends[pos] = len(atom)
    return ends, starts


def best_two_lines(text, font, max_width):
    """2行に割る位置を、日本語として切りやすいところから選ぶ。"""
    ends, starts = split_points(text)
    best = None
    for i in range(1, len(text)):
        head, tail = text[:i], text[i:]
        if font.getlength(head) > max_width or font.getlength(tail) > max_width:
            continue
        if tail[0] in NO_LINE_START or head[-1] in NO_LINE_END:
            continue
        at_boundary = i in ends
        score = 6.0 if at_boundary else 0.0
        prev, following = head[-1], tail[0]
        if prev == "、":
            score += 5
        elif prev in "」』）":
            score += 4
        elif prev in PARTICLE_STRONG:
            score += 3.5
        elif prev in PARTICLE_SOFT:
            score += 2
        if following in PARTICLE_STRONG:
            score -= 4          # 行頭の「は」「を」は読みにくい
        elif following in PARTICLE_SOFT:
            score -= 1
        if is_kanji(prev) and is_kanji(following):
            score -= 3          # 熟語を割りたくない
        if at_boundary:
            if ends.get(i, 1) >= 2:
                score += 2      # カタカナ語や題名の直後で切る
            if starts.get(i, 1) >= 2:
                score += 2
        # 行の長さが揃っているほうが見た目が落ち着く。
        score -= abs(font.getlength(head) - font.getlength(tail)) / max_width * 2
        good = at_boundary and len(head) >= 2 and len(tail) >= 2
        if best is None or score > best[0]:
            best = (score, [head, tail], good)
    return best


def char_wrap(text, font, max_width):
    lines, line = [], ""
    for ch in text:
        if line and font.getlength(line + ch) > max_width and ch not in NO_LINE_START:
            lines.append(line)
            line = ch
        else:
            line += ch
    if line:
        lines.append(line)
    return lines


def fit(text, font_path, base_size, max_width, max_lines=2):
    """1行で収まるならそれを選び、無理なら切れ目のよい2行を探す。"""
    for size in range(base_size, ONE_LINE_FLOOR - 1, -2):
        font = ImageFont.truetype(str(font_path), size)
        if font.getlength(text) <= max_width:
            return font, [text]

    fallback = None
    for size in range(base_size, TWO_LINE_FLOOR - 1, -2):
        font = ImageFont.truetype(str(font_path), size)
        candidate = best_two_lines(text, font, max_width)
        if candidate is None:
            continue
        _, lines, good = candidate
        if good:
            return font, lines
        fallback = fallback or (font, lines)
    if fallback:
        return fallback

    font = ImageFont.truetype(str(font_path), base_size)
    return font, char_wrap(text, font, max_width)


class Hook:
    """冒頭に出す大きな一言。字幕と同じ縁取りで、色だけ変える。"""

    def __init__(self, lines, font_path, size, color):
        self.font = ImageFont.truetype(str(font_path), size)
        self.line_height = int(size * LINE_SPACING)
        stroke = round(OUTLINE_WIDTH * size / FONT_SIZE)
        pad = stroke * 2 + 6
        width = int(max(self.font.getlength(l) for l in lines)) + pad * 2
        height = self.line_height * len(lines) + pad * 2

        self.layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(self.layer)
        for i, line in enumerate(lines):
            x = pad + (width - pad * 2 - self.font.getlength(line)) / 2
            draw.text((x, pad + i * self.line_height), line, font=self.font,
                      fill=color, stroke_width=stroke, stroke_fill=OUTLINE_COLOR)


class Caption:
    """1つの字幕。白文字と金文字の2枚を作り置きし、境界で切り替えて描く。"""

    def __init__(self, text, font_path):
        self.font, self.lines = fit(text, font_path, FONT_SIZE,
                                    MAX_TEXT_WIDTH, MAX_LINES)
        self.line_height = int(self.font.size * LINE_SPACING)
        pad = OUTLINE_WIDTH * 2 + 6
        width = int(max(self.font.getlength(l) for l in self.lines)) + pad * 2
        height = self.line_height * len(self.lines) + pad * 2
        self.size = (width, height)

        self.base = self._layer(TEXT_COLOR, pad)
        self.spoken = self._layer(SPOKEN_COLOR, pad)

        # 行ごとの左端と、文字送りに使う累積幅。
        self.line_x = [pad + (width - pad * 2 - self.font.getlength(l)) / 2
                       for l in self.lines]
        self.line_y = [pad + i * self.line_height for i in range(len(self.lines))]
        self.char_x = [[self.font.getlength(l[:i]) for i in range(len(l) + 1)]
                       for l in self.lines]
        self.weights = [[cap_mod.char_weight(c) for c in l] for l in self.lines]
        self.total_weight = sum(sum(w) for w in self.weights) or 1.0

    def _layer(self, color, pad):
        layer = Image.new("RGBA", self.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer)
        width = self.size[0]
        for i, line in enumerate(self.lines):
            x = pad + (width - pad * 2 - self.font.getlength(line)) / 2
            draw.text((x, pad + i * self.line_height), line, font=self.font,
                      fill=color, stroke_width=OUTLINE_WIDTH,
                      stroke_fill=OUTLINE_COLOR)
        return layer

    def spoken_chars(self, progress):
        """読み終えた重み分だけ、行ごとに何文字目までかを返す。"""
        budget = progress * self.total_weight
        out = []
        for weights in self.weights:
            count = 0
            for w in weights:
                if budget <= 0 or budget < w:
                    break
                budget -= w
                count += 1
            out.append(count)
            if count < len(weights):
                budget = 0.0
        return out


def progress_at(items, elapsed):
    """無音の間は文字送りを止めたまま、発声時間の何割かを返す。"""
    speech = sum(d for kind, d in items if kind == "mora") or 1.0
    done = 0.0
    for kind, d in items:
        if elapsed <= 0:
            break
        take = min(elapsed, d)
        if kind == "mora":
            done += take
        elapsed -= d
    return min(done / speech, 1.0)


def ease_out_back(t):
    return 1 + 2.4 * (t - 1) ** 3 + 1.4 * (t - 1) ** 2


def render_frames(captions, layers, hook, hook_end, duration, out_pipe):
    background = Image.new("RGB", (WIDTH, HEIGHT), CHROMA)
    total_frames = int(round(duration * FPS))
    index = 0
    for frame_no in range(total_frames):
        t = frame_no / FPS
        while index + 1 < len(captions) and t >= captions[index + 1]["start"]:
            index += 1
        frame = background.copy()
        if t < hook_end:
            # フックだけを見せる。字幕と重ねない。
            _draw_hook(frame, hook, t)
        else:
            cap = captions[index]
            _draw_caption(frame, cap, layers[index], t - cap["start"])
        out_pipe.write(frame.tobytes())
        if frame_no % 300 == 0:
            print(f"  frame {frame_no}/{total_frames}", file=sys.stderr)
    return total_frames


def _draw_hook(frame, hook, t):
    layer = hook.layer
    scale = 1.0
    if t < POP_TIME:
        scale = POP_SCALE + (1 - POP_SCALE) * ease_out_back(t / POP_TIME)
    if scale != 1.0:
        layer = layer.resize((max(1, int(layer.width * scale)),
                              max(1, int(layer.height * scale))), Image.LANCZOS)
    frame.paste(layer, ((WIDTH - layer.width) // 2,
                        HOOK_CENTER_Y - layer.height // 2), layer)


def _draw_caption(frame, cap, layer, elapsed):
    width, height = layer.size
    anchor_x = (WIDTH - width) // 2
    anchor_y = TEXT_CENTER_Y - height // 2

    if elapsed < POP_TIME:
        # 出現の弾み。ここでは文字送りは出さない（まだ1文字分も進まない）。
        ratio = elapsed / POP_TIME
        scale = POP_SCALE + (1 - POP_SCALE) * ease_out_back(ratio)
        rise = int(POP_RISE * (1 - ease_out_back(ratio)))
        popped = layer.base.resize((max(1, int(width * scale)),
                                    max(1, int(height * scale))), Image.LANCZOS)
        frame.paste(popped, ((WIDTH - popped.width) // 2,
                             TEXT_CENTER_Y - popped.height // 2 + rise), popped)
        return

    frame.paste(layer.base, (anchor_x, anchor_y), layer.base)
    progress = progress_at(cap["items"], elapsed)
    for i, count in enumerate(layer.spoken_chars(progress)):
        if count <= 0:
            continue
        x0 = int(layer.line_x[i])
        # 文字の境目で切る。縁取りは白側と同じ色なので継ぎ目は見えない。
        x1 = int(layer.line_x[i] + layer.char_x[i][count])
        y0 = layer.line_y[i] - OUTLINE_WIDTH * 2
        y1 = layer.line_y[i] + layer.line_height + OUTLINE_WIDTH
        box = (max(0, x0 - OUTLINE_WIDTH * 2), max(0, y0),
               min(width, x1), min(height, y1))
        piece = layer.spoken.crop(box)
        frame.paste(piece, (anchor_x + box[0], anchor_y + box[1]), piece)


def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", type=Path, default=gn.DEFAULT_ASSETS)
    ap.add_argument("--font", type=Path,
                    default=gn.DEFAULT_ASSETS / "SourceHanSansJP-Heavy.otf")
    ap.add_argument("--out", type=Path, default=here / "zen-ghibli-tiktok.mp4")
    ap.add_argument("--audio", type=Path, default=here / "zen-ghibli-narration.wav")
    ap.add_argument("--srt", type=Path, default=here / "zen-ghibli-subtitles.srt")
    args = ap.parse_args()

    vv = gn.open_engine(args.assets)
    audio, params, spans = gn.render(vv)
    duration = gn.write_wav(args.audio, audio, params)
    print(f"audio: {args.audio} {duration:.2f}s", file=sys.stderr)

    caps = cap_mod.build_captions(lambda t: gn.query_for(vv, t),
                                  gn.SCRIPT, spans, duration)

    # フックは2枚目の字幕（同じ題名が本文に出てくる）に席を譲る。
    # 1枚目「京都で、」はフックの裏に隠れるので、画面には出さない。
    hook = Hook(HOOK_LINES, args.font, HOOK_SIZE, HOOK_COLOR)
    hook_end = caps[1]["start"]

    shown = [{"text": HOOK_TEXT, "start": 0.0, "show_until": hook_end}] + caps[1:]
    args.srt.write_text(cap_mod.to_srt(shown), encoding="utf-8")
    print(f"フック {hook_end:.2f}秒 / 字幕 {len(caps) - 1}枚 / 1枚あたり平均 "
          f"{sum(c['show_until'] - c['start'] for c in caps[1:]) / (len(caps) - 1):.2f}s",
          file=sys.stderr)

    layers = [Caption(c["text"], args.font) for c in caps]

    ffmpeg = gn.find_ffmpeg()
    if not ffmpeg:
        sys.exit("ffmpegが見つかりません。pip install imageio-ffmpeg を試してください。")
    command = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WIDTH}x{HEIGHT}",
        "-r", str(FPS), "-i", "-",
        "-i", str(args.audio),
        "-c:v", "libx264", "-preset", "medium", "-crf", "17",
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.0",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest",
        "-movflags", "+faststart", str(args.out),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        frames = render_frames(caps, layers, hook, hook_end,
                               duration, process.stdin)
    finally:
        process.stdin.close()
    if process.wait() != 0:
        sys.exit("ffmpegの書き出しに失敗しました。")

    print(f"\n{args.out}  {frames / FPS:.1f}s  {WIDTH}x{HEIGHT}/{FPS}fps  "
          f"背景 rgb{CHROMA}")
    print(f"{args.srt}  フック1枚＋字幕{len(caps) - 1}枚")


if __name__ == "__main__":
    main()
