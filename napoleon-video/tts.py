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

OPEN_JTALK_DIC = "/var/lib/mecab/dic/open-jtalk/naist-jdic"
OPEN_JTALK_VOICE = "/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice"


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
    if shutil.which("open_jtalk") and os.path.exists(OPEN_JTALK_VOICE):
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
    # open_jtalk の -r は「大きいほど遅い」のではなく speech rate 倍率
    subprocess.run(
        ["open_jtalk", "-x", OPEN_JTALK_DIC, "-m", OPEN_JTALK_VOICE,
         "-r", "%.3f" % rate, "-ow", out_path],
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
        return "open_jtalk", "Open JTalk (nitech-jp-atr503-m001)"
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
