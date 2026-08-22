"""Nodar — agente de Metaverso (mundos, estética, arquitectura digital)."""
from .base import Agent, AgentContext


class Nodar(Agent):
    name = "Nodar"
    signature = "[Nodar·Metaverso]"
    mission = "mundos, estética, arquitectura digital"
    element = "Aire"

    def agent_actions(self, text: str, ctx: AgentContext) -> str:
        return ("Traducible a arquitectura digital: este contenido podría materializarse como "
                "un nodo/escena dentro del ecosistema (Metaverso Nodal) coherente con el elemento activo.")
