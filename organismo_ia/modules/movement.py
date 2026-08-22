"""module_movement — biomecánica/activaciones vía sensores (capa 4.2 del spec). Ver device_bound.py."""
from .device_bound import DeviceBoundModule


class MovementModule(DeviceBoundModule):
    module_name = "movement"
    requires = "acelerómetro/giroscopio u otro sensor de movimiento del dispositivo"

    def read_activity(self) -> str:
        return self.capture()
