"""ナレーション音声の合成。

使える手段を上から順に試す:
  a. VOICEVOX ENGINE (http://localhost:50021)
  b. OS 標準の日本語 TTS (mac: say -v Kyoko / Windows: SAPI / Linux: open_jtalk)
  c. どれも無理なら音声なし (字幕だけで成立させる)
"""

import json
import os
import platform
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import wave

VOICEVOX_URL = os.environ.get("VOICEVOX_URL", "http://localhost:50021")
VOICEVOX_SPEAKER = int(os.environ.get("VOICEVOX_SPEAKER", "3"))  # ずんだもん(ノーマル)

_HERE = os.path.dirname(os.path.abspath(__file__))

OPEN_JTALK_DIC_CANDIDATES = [
    "/var/lib/mecab/dic/open-jtalk/naist-jdic",
    "/usr/local/dic",
    "/opt/homebrew/opt/open-jtalk/dic",
    "/usr/local/opt/open-jtalk/dic",
]
# voices/ に置いた htsvoice を優先する (同梱の mei_normal は CC BY 3.0)
OPEN_JTALK_VOICE_CANDIDATES = [
    os.environ.get("OPEN_JTALK_VOICE", ""),
    os.path.join(_HERE, "voices", "mei_normal.htsvoice"),
    "/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice",
]

# 声の調整: -b=明瞭度(ポストフィルタ) / -fm=ピッチ / -g=音量 / -jf=抑揚の強さ
OPEN_JTALK_ARGS = ["-b", "0.3", "-fm", "-0.5", "-g", "-3.0", "-jf", "1.1"]


def _first_existing(paths):
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None


def open_jtalk_voice():
    return _first_existing(OPEN_JTALK_VOICE_CANDIDATES)


def open_jtalk_dic():
    return _first_existing(OPEN_JTALK_DIC_CANDIDATES)


# --- a. VOICEVOX ------------------------------------------------------------

def _voicevox_available():
    try:
        with urllib.request.urlopen(VOICEVOX_URL + "/version", timeout=3):
            return True
    except Exception:
        return False


def _voicevox_synth(text, out_path, rate):
    q = urllib.request.Request(
        "%s/audio_query?speaker=%d&text=%s"
        % (VOICEVOX_URL, VOICEVOX_SPEAKER, urllib.parse.quote(text)),
        method="POST",
    )
    with urllib.request.urlopen(q, timeout=30) as r:
        query = json.loads(r.read())
    query["speedScale"] = rate
    req = urllib.request.Request(
        "%s/synthesis?speaker=%d" % (VOICEVOX_URL, VOICEVOX_SPEAKER),
        data=json.dumps(query).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        wav = r.read()
    with open(out_path, "wb") as f:
        f.write(wav)


# --- b. OS 標準 TTS ---------------------------------------------------------

def _os_tts_kind():
    system = platform.system()
    if system == "Darwin" and shutil.which("say"):
        return "say"
    if system == "Windows":
        return "sapi"
    if shutil.which("open_jtalk") and open_jtalk_voice() and open_jtalk_dic():
        return "open_jtalk"
    return None


def _say_synth(text, out_path, rate):
    aiff = out_path + ".aiff"
    subprocess.run(
        ["say", "-v", "Kyoko", "-r", str(int(180 * rate)), "-o", aiff, text],
        check=True,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", aiff, "-ar", "48000", "-ac", "1", out_path],
        check=True,
    )
    os.remove(aiff)


def _sapi_synth(text, out_path, rate):
    ps = (
        "Add-Type -AssemblyName System.Speech;"
        "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer;"
        "$s.Rate = %d;"
        "$s.SetOutputToWaveFile('%s');"
        "$s.Speak([Console]::In.ReadToEnd());"
        "$s.Dispose()" % (int(round((rate - 1.0) * 10)), out_path)
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                   input=text, text=True, check=True)


def _open_jtalk_synth(text, out_path, rate):
    # open_jtalk の -r は speech rate 倍率 (大きいほど速い)
    subprocess.run(
        ["open_jtalk", "-x", open_jtalk_dic(), "-m", open_jtalk_voice(),
         "-r", "%.3f" % rate, "-ow", out_path] + OPEN_JTALK_ARGS,
        input=text.encode("utf-8"), check=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


# --- 公開 API ---------------------------------------------------------------

def pick_backend():
    """使える合成手段を決める。戻り値は ('voicevox'|'say'|'sapi'|'open_jtalk'|None, 表示名)"""
    if _voicevox_available():
        return "voicevox", "VOICEVOX ENGINE (localhost:50021)"
    kind = _os_tts_kind()
    if kind == "say":
        return "say", "macOS say -v Kyoko"
    if kind == "sapi":
        return "sapi", "Windows SAPI (System.Speech)"
    if kind == "open_jtalk":
        return "open_jtalk", "Open JTalk (%s)" % os.path.basename(open_jtalk_voice())
    return None, "音声なし (字幕のみ)"


_SYNTH = {
    "voicevox": _voicevox_synth,
    "say": _say_synth,
    "sapi": _sapi_synth,
    "open_jtalk": _open_jtalk_synth,
}


def synth(backend, text, out_path, rate=1.0):
    """1文を合成して out_path (wav) に書く。長さ(秒)を返す。"""
    _SYNTH[backend](text, out_path, rate)
    with wave.open(out_path, "rb") as w:
        return w.getnframes() / float(w.getframerate())
