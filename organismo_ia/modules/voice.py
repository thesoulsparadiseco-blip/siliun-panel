"""module_voice — STT/TTS local (capa 4.2 del spec). Ver device_bound.py.

La selección de *qué* voz usar (banco de voces: SILIUN, KALEN, LUMARA,
NODAL, ARKAI, SORA-ECHO) vive en voice_bank.py y sí corre en servidor —
solo la síntesis de audio en sí queda device-bound.
"""
from .device_bound import DeviceBoundModule
from . import voice_bank


class VoiceModule(DeviceBoundModule):
    module_name = "voice"
    requires = "micrófono (STT) y salida de audio (TTS) del dispositivo"

    def transcribe(self, audio_bytes: bytes) -> str:
        return self.capture(audio_bytes)

    def synthesize(self, text: str, voice: str = voice_bank.DEFAULT_VOICE) -> bytes:
        profile = voice_bank.get_voice(voice)
        if profile is None:
            known = [v["nombre"] for v in voice_bank.list_voices()]
            raise ValueError(f"Voz desconocida: '{voice}'. Válidas: {known}")
        return self.capture(text, voice=profile["nombre"])
