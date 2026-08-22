"""module_vision — visión local vía cámara (capa 4.2 del spec). Ver device_bound.py."""
from .device_bound import DeviceBoundModule


class VisionModule(DeviceBoundModule):
    module_name = "vision"
    requires = "cámara del dispositivo"

    def analyze(self, image_bytes: bytes) -> str:
        return self.capture(image_bytes)
