"""ui/lab_mode — contrato JSON del modo laboratorio (fórmulas/arquitecturas, capa 1 del spec)."""
from ..memory import internal


def describe() -> dict:
    return {
        "mode": "lab_mode",
        "title": "Laboratorio",
        "description": "Fórmulas (Almir) y arquitecturas (Nodar/Helion) en construcción.",
        "formulas": list(internal.load("formulas").keys()),
        "architectures": list(internal.load("architectures").keys()),
        "actions": [{"id": "save_formula", "label": "Guardar fórmula"}],
    }
