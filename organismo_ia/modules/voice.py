"""module_voice — STT/TTS local (capa 4.2 del spec). Ver device_bound.py."""
from .device_bound import DeviceBoundModule


class VoiceModule(DeviceBoundModule):
    module_name = "voice"
    requires = "micrófono (STT) y salida de audio (TTS) del dispositivo"

    def transcribe(self, audio_bytes: bytes) -> str:
        return self.capture(audio_bytes)

    def synthesize(self, text: str) -> bytes:
        return self.capture(text)
