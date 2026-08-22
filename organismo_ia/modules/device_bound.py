"""
Base común para los módulos ligados a hardware del dispositivo
(voice, vision, movement, botanica-sensor, energy-sensor — capa 4.2 del
spec). Ninguno de estos puede ejecutarse en un backend de servidor: STT
real necesita micrófono, visión necesita cámara, movimiento/energía
pueden necesitar sensores del móvil (acelerómetro, wearables). Por eso
cada uno expone la interfaz esperada por `core/synthesis_engine.py` pero
levanta `NotImplementedError` con instrucciones de dónde implementarlo
(cliente móvil, sección 4.1: Flutter/React Native + Kotlin/Swift nativo).
"""


class DeviceBoundModule:
    module_name = "device_bound"
    requires = "hardware del dispositivo"

    def capture(self, *args, **kwargs) -> str:
        raise NotImplementedError(
            f"module_{self.module_name}: requiere {self.requires}, no disponible en "
            "este backend de servidor. Implementar en el cliente móvil "
            "(sección 4.1 del spec) y enviar el resultado ya transcripto/"
            "clasificado a core/synthesis_engine.run()."
        )
