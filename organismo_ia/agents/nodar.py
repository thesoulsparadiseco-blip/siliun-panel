"""Nodar — agente de Metaverso (mundos, estética, arquitectura digital)."""
from .base import Agent, AgentContext


class Nodar(Agent):
    name = "Nodar"
    signature = "[Nodar·Metaverso]"
    mission = "mundos, estética, arquitectura digital"
    element = "air"

    def agent_actions(self, text: str, ctx: AgentContext) -> str:
        return self.texts(ctx)["default"]
