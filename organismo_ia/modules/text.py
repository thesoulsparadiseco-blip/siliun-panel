"""module_text — capa 4.2 del spec. El único módulo de entrada/salida que
corre completo en un backend de servidor (los demás dependen de hardware
del dispositivo — ver voice.py/vision.py/movement.py)."""


def normalize(raw: str) -> str:
    return raw.strip()


def format_output(manifestation: str) -> str:
    return manifestation.strip()
