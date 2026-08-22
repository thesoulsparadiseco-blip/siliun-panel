"""module_energy — estado energético vía sensores/wearables (capa 4.2 del spec). Ver device_bound.py."""
from .device_bound import DeviceBoundModule


class EnergyModule(DeviceBoundModule):
    module_name = "energy"
    requires = "sensor biométrico/wearable del dispositivo"

    def read_state(self) -> str:
        return self.capture()
