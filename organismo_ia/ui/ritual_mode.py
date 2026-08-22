"""ui/ritual_mode — contrato JSON del modo de rituales guiados (capa 1 del spec)."""
from ..memory import internal


def describe() -> dict:
    rituals = internal.load("rituals")
    return {
        "mode": "ritual_mode",
        "title": "Rituales",
        "description": "Protocolos corporales y rituales guiados almacenados en memoria interna.",
        "rituals": list(rituals.keys()),
        "actions": [{"id": "start_ritual", "label": "Iniciar ritual"}],
    }
