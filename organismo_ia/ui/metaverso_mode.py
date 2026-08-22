"""ui/metaverso_mode — contrato JSON del modo Metaverso Nodal (agente Nodar, capa 1 del spec)."""
from ..memory import internal


def describe() -> dict:
    return {
        "mode": "metaverso_mode",
        "title": "Metaverso Nodal",
        "description": "Proyectos y nodos digitales (Nodar/Helion) desde memoria interna.",
        "projects": list(internal.load("projects").keys()),
        "actions": [{"id": "open_node", "label": "Abrir nodo"}],
    }
