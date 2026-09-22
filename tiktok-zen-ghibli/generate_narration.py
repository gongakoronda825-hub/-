#!/usr/bin/env python3
"""TikTok用の日本語ナレーション音声を VOICEVOX CORE で生成する。

声: 青山龍星「しっとり」(style_id=84) ― 低めで落ち着いた男性の声。
美術館・ドキュメンタリーのナレーションに近い、穏やかで少しミステリアスな
トーンを狙って speedScale / pitchScale / intonationScale を調整している。

素材(コア・ONNX Runtime・OpenJTalk辞書・音声モデル)は setup_assets.sh で用意する。
"""

import argparse
import array
import io
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vvcore import Voicevox  # noqa: E402

STYLE_ID = 84  # 青山龍星「しっとり」

# 読み上げる文章。(文, 直後に入れる無音の秒数)
SCRIPT = [
    ("京都で、「君たちはどう生きるか」の世界で禅に触れられるイベントがあります。", 0.55),
    ("それが、「禅とジブリ」京都展。", 0.60),
    ("10月3日から、京都市京セラ美術館で開催されます。", 0.50),
    ("ジブリの名作から、死生観や人生哲学などを禅的に読みとき、"
     "宮﨑駿・高畑勲両監督との映画制作の経験に照らして、禅を語ります。", 0.50),
    ("本展は、この「禅とジブリ」を原点として生まれました。", 0.45),
    ("「君たちはどう生きるか」の世界を通して、禅に触れられる体感型の展覧会です。", 0.50),
    ("ジブリ作品に込められた問いや、生き方についても、"
     "禅という新たな視点から楽しむことができます。", 0.50),
    ("さらに、鈴木敏夫さんと禅僧による対談をもとにした展示も。", 0.50),
    ("ただのジブリ展とは少し違う、「君たちはどう生きるか」を"
     "もう一度深く味わえるイベントです。", 0.55),
    ("開催は12月6日まで。", 0.50),
    ("ジブリ好きなら、ぜひチェックしてみてください。", 0.30),
]

# OpenJTalkが正しく読めない固有名詞。(表記, 読み, アクセント型)
USER_WORDS = [
    ("宮﨑駿", "ミヤザキハヤオ", 4),
    ("宮崎駿", "ミヤザキハヤオ", 4),
]

# 声の質感。落ち着いた低めの語りにする。
SPEED_SCALE = 0.95        # ゆっくりめ。ただし間延びしない程度
PITCH_SCALE = -0.02       # わずかに低く
INTONATION_SCALE = 0.95   # 抑揚を少し抑えて大げさにしない
VOLUME_SCALE = 1.0
PRE_PHONEME_LENGTH = 0.10
POST_PHONEME_LENGTH = 0.10
LEAD_IN = 0.35            # 冒頭の無音
TAIL = 0.60               # 末尾の無音
TARGET_PEAK_DBFS = -1.5   # TikTokで埋もれない音量にそろえる


def wav_params(wav_bytes):
    with wave.open(io.BytesIO(wav_bytes)) as w:
        return w.getparams()


def wav_frames(wav_bytes):
    with wave.open(io.BytesIO(wav_bytes)) as w:
        return w.readframes(w.getnframes())


def silence(params, seconds):
    return b"\x00" * (int(params.framerate * seconds) * params.sampwidth * params.nchannels)


def peak_amplitude(frames):
    samples = array.array("h")
    samples.frombytes(frames)
    return max(max(samples), -min(samples)) or 1


def synthesize_all(vv, volume_scale):
    """全文を合成して (WAVバイト列のリスト, waveのパラメータ) を返す。"""
    wavs = []
    for text, _ in SCRIPT:
        query = vv.audio_query(text, STYLE_ID)
        query.update(speedScale=SPEED_SCALE, pitchScale=PITCH_SCALE,
                     intonationScale=INTONATION_SCALE, volumeScale=volume_scale,
                     prePhonemeLength=PRE_PHONEME_LENGTH,
                     postPhonemeLength=POST_PHONEME_LENGTH)
        wavs.append(vv.synthesis(query, STYLE_ID))
        print(f"  ok: {text[:24]}…", file=sys.stderr)
    return wavs, wav_params(wavs[0])


def build(vv, out_wav, target_peak_dbfs=TARGET_PEAK_DBFS):
    # 1回目は素の音量で合成し、全体のピークから音量係数を決めてから合成し直す。
    # エンジン側で音量をかけるので、16bit化のあとで増幅するより劣化が少ない。
    wavs, params = synthesize_all(vv, VOLUME_SCALE)
    peak = max(peak_amplitude(wav_frames(w)) for w in wavs)
    volume_scale = VOLUME_SCALE * (10 ** (target_peak_dbfs / 20) * 32767 / peak)
    print(f"  volumeScale={volume_scale:.2f} "
          f"(peak {peak} -> {target_peak_dbfs} dBFS)", file=sys.stderr)
    wavs, params = synthesize_all(vv, volume_scale)

    chunks = [silence(params, LEAD_IN)]
    for wav, (_, pause) in zip(wavs, SCRIPT):
        chunks.append(wav_frames(wav))
        chunks.append(silence(params, pause))
    chunks.append(silence(params, TAIL))

    audio = b"".join(chunks)
    with wave.open(str(out_wav), "wb") as w:
        w.setnchannels(params.nchannels)
        w.setsampwidth(params.sampwidth)
        w.setframerate(params.framerate)
        w.writeframes(audio)
    seconds = len(audio) / (params.framerate * params.sampwidth * params.nchannels)
    return seconds, params


def find_ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def to_mp3(wav_path, mp3_path):
    """ffmpegがあればMP3も書き出す。無ければWAVのみ。"""
    exe = find_ffmpeg()
    if not exe:
        print("ffmpegが見つからないためMP3は作りません。", file=sys.stderr)
        return None
    subprocess.run([exe, "-hide_banner", "-loglevel", "error", "-y",
                    "-i", str(wav_path), "-codec:a", "libmp3lame",
                    "-b:a", "192k", "-ar", "44100", "-ac", "1", str(mp3_path)],
                   check=True)
    return mp3_path


def main():
    assets = Path(os.environ.get("VV_ASSETS", Path(__file__).resolve().parent / "assets"))
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", type=Path, default=assets,
                    help="setup_assets.sh が展開した素材ディレクトリ")
    ap.add_argument("--out", type=Path,
                    default=Path(__file__).resolve().parent / "zen-ghibli-narration.wav")
    args = ap.parse_args()

    core = next(args.assets.glob("voicevox_core-*/lib/libvoicevox_core.so"))
    ort = next(args.assets.glob("voicevox_onnxruntime-*/lib/libvoicevox_onnxruntime.so.*"))
    dic = next(args.assets.glob("open_jtalk_dic_utf_8-*"))
    vvm = next(args.assets.glob("**/15.vvm"))

    vv = Voicevox(core, ort, dic, user_words=USER_WORDS)
    metas = vv.load_model(vvm)
    style = next((c["name"], s["name"]) for c in metas for s in c["styles"]
                 if s["id"] == STYLE_ID)
    print(f"voice: {style[0]}（{style[1]}） style_id={STYLE_ID}", file=sys.stderr)

    seconds, params = build(vv, args.out)
    print(f"\n{args.out}  {seconds:.1f}s  "
          f"{params.framerate}Hz/{params.sampwidth * 8}bit/"
          f"{'mono' if params.nchannels == 1 else 'stereo'}")
    mp3 = to_mp3(args.out, args.out.with_suffix(".mp3"))
    if mp3:
        print(f"{mp3}  {seconds:.1f}s  44100Hz/192kbps/mono")


if __name__ == "__main__":
    main()
