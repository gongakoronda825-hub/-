"""VOICEVOX CORE 0.16 の C API を ctypes から最小限だけ使うラッパー。

音声モデル・ONNX Runtime・OpenJTalk 辞書のパスは呼び出し側から渡す。
"""

import ctypes
import json
from pathlib import Path


class VoicevoxError(RuntimeError):
    pass


class LoadOnnxruntimeOptions(ctypes.Structure):
    _fields_ = [("filename", ctypes.c_char_p)]


class InitializeOptions(ctypes.Structure):
    _fields_ = [("acceleration_mode", ctypes.c_int32),
                ("cpu_num_threads", ctypes.c_uint16)]


class SynthesisOptions(ctypes.Structure):
    _fields_ = [("enable_interrogative_upspeak", ctypes.c_bool)]


class UserDictWord(ctypes.Structure):
    _fields_ = [("surface", ctypes.c_char_p),
                ("pronunciation", ctypes.c_char_p),
                ("accent_type", ctypes.c_size_t),
                ("word_type", ctypes.c_int32),
                ("priority", ctypes.c_uint32)]


class Voicevox:
    def __init__(self, core_lib, onnxruntime_lib, dict_dir, cpu_num_threads=0,
                 user_words=()):
        self._lib = ctypes.CDLL(str(core_lib))
        self._bind()

        ort = ctypes.c_void_p()
        self._check(self._lib.voicevox_onnxruntime_load_once(
            LoadOnnxruntimeOptions(filename=str(onnxruntime_lib).encode()),
            ctypes.byref(ort)))

        open_jtalk = ctypes.c_void_p()
        self._check(self._lib.voicevox_open_jtalk_rc_new(
            str(dict_dir).encode(), ctypes.byref(open_jtalk)))
        self._open_jtalk = open_jtalk
        if user_words:
            self._use_user_dict(user_words)

        synth = ctypes.c_void_p()
        self._check(self._lib.voicevox_synthesizer_new(
            ort, open_jtalk,
            InitializeOptions(acceleration_mode=1, cpu_num_threads=cpu_num_threads),
            ctypes.byref(synth)))
        self._synth = synth

    def _bind(self):
        lib = self._lib
        lib.voicevox_onnxruntime_load_once.argtypes = [LoadOnnxruntimeOptions,
                                                       ctypes.POINTER(ctypes.c_void_p)]
        lib.voicevox_onnxruntime_load_once.restype = ctypes.c_int32
        lib.voicevox_open_jtalk_rc_new.argtypes = [ctypes.c_char_p,
                                                   ctypes.POINTER(ctypes.c_void_p)]
        lib.voicevox_open_jtalk_rc_new.restype = ctypes.c_int32
        lib.voicevox_synthesizer_new.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                                                 InitializeOptions,
                                                 ctypes.POINTER(ctypes.c_void_p)]
        lib.voicevox_synthesizer_new.restype = ctypes.c_int32
        lib.voicevox_voice_model_file_open.argtypes = [ctypes.c_char_p,
                                                       ctypes.POINTER(ctypes.c_void_p)]
        lib.voicevox_voice_model_file_open.restype = ctypes.c_int32
        lib.voicevox_synthesizer_load_voice_model.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        lib.voicevox_synthesizer_load_voice_model.restype = ctypes.c_int32
        lib.voicevox_voice_model_file_delete.argtypes = [ctypes.c_void_p]
        lib.voicevox_voice_model_file_delete.restype = None
        lib.voicevox_voice_model_file_create_metas_json.argtypes = [ctypes.c_void_p]
        lib.voicevox_voice_model_file_create_metas_json.restype = ctypes.c_void_p
        lib.voicevox_synthesizer_create_audio_query.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_void_p)]
        lib.voicevox_synthesizer_create_audio_query.restype = ctypes.c_int32
        lib.voicevox_synthesizer_synthesis.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.c_uint32, SynthesisOptions,
            ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.POINTER(ctypes.c_uint8))]
        lib.voicevox_synthesizer_synthesis.restype = ctypes.c_int32
        lib.voicevox_json_free.argtypes = [ctypes.c_void_p]
        lib.voicevox_json_free.restype = None
        lib.voicevox_wav_free.argtypes = [ctypes.POINTER(ctypes.c_uint8)]
        lib.voicevox_wav_free.restype = None
        lib.voicevox_error_result_to_message.argtypes = [ctypes.c_int32]
        lib.voicevox_error_result_to_message.restype = ctypes.c_char_p
        lib.voicevox_user_dict_new.argtypes = []
        lib.voicevox_user_dict_new.restype = ctypes.c_void_p
        lib.voicevox_user_dict_word_make.argtypes = [ctypes.c_char_p, ctypes.c_char_p,
                                                     ctypes.c_size_t]
        lib.voicevox_user_dict_word_make.restype = UserDictWord
        lib.voicevox_user_dict_add_word.argtypes = [ctypes.c_void_p,
                                                    ctypes.POINTER(UserDictWord),
                                                    ctypes.POINTER(ctypes.c_uint8 * 16)]
        lib.voicevox_user_dict_add_word.restype = ctypes.c_int32
        lib.voicevox_open_jtalk_rc_use_user_dict.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        lib.voicevox_open_jtalk_rc_use_user_dict.restype = ctypes.c_int32

    def _use_user_dict(self, user_words):
        """(表記, 読みのカタカナ, アクセント型) の並びを固有名詞として登録する。"""
        user_dict = ctypes.c_void_p(self._lib.voicevox_user_dict_new())
        for surface, pronunciation, accent_type in user_words:
            # voicevox_user_dict_word_make の戻り値は引数の文字列をそのまま指すため、
            # Python側の一時バッファが解放されないよう構造体を直接組み立てる。
            word = UserDictWord(surface=surface.encode(),
                                pronunciation=pronunciation.encode(),
                                accent_type=accent_type,
                                word_type=0,  # 固有名詞
                                priority=8)
            uuid = (ctypes.c_uint8 * 16)()
            self._check(self._lib.voicevox_user_dict_add_word(
                user_dict, ctypes.byref(word), ctypes.byref(uuid)))
        self._check(self._lib.voicevox_open_jtalk_rc_use_user_dict(
            self._open_jtalk, user_dict))

    def _check(self, code):
        if code != 0:
            msg = self._lib.voicevox_error_result_to_message(code) or b""
            raise VoicevoxError(f"[{code}] {msg.decode('utf-8', 'replace')}")

    def _take_json(self, ptr):
        text = ctypes.cast(ptr, ctypes.c_char_p).value.decode("utf-8")
        self._lib.voicevox_json_free(ptr)
        return json.loads(text)

    def load_model(self, vvm_path):
        model = ctypes.c_void_p()
        self._check(self._lib.voicevox_voice_model_file_open(
            str(vvm_path).encode(), ctypes.byref(model)))
        try:
            self._check(self._lib.voicevox_synthesizer_load_voice_model(self._synth, model))
            return self._take_json(self._lib.voicevox_voice_model_file_create_metas_json(model))
        finally:
            self._lib.voicevox_voice_model_file_delete(model)

    def audio_query(self, text, style_id):
        out = ctypes.c_void_p()
        self._check(self._lib.voicevox_synthesizer_create_audio_query(
            self._synth, text.encode(), style_id, ctypes.byref(out)))
        return self._take_json(out)

    def synthesis(self, query, style_id, enable_interrogative_upspeak=True):
        length = ctypes.c_size_t()
        wav = ctypes.POINTER(ctypes.c_uint8)()
        self._check(self._lib.voicevox_synthesizer_synthesis(
            self._synth, json.dumps(query, ensure_ascii=False).encode(), style_id,
            SynthesisOptions(enable_interrogative_upspeak=enable_interrogative_upspeak),
            ctypes.byref(length), ctypes.byref(wav)))
        try:
            return bytes(bytearray(ctypes.cast(
                wav, ctypes.POINTER(ctypes.c_uint8 * length.value)).contents))
        finally:
            self._lib.voicevox_wav_free(wav)
