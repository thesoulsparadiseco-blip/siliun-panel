"""Solkin — agente de Cuerpo (movimiento, biomecánica, activaciones, salud integrativa)."""
from .base import Agent, AgentContext


class Solkin(Agent):
    name = "Solkin"
    signature = "[Solkin·Cuerpo]"
    mission = "movimiento, biomecánica, activaciones, salud integrativa"
    element = "earth"

    def agent_actions(self, text: str, ctx: AgentContext) -> str:
        t = self.texts(ctx)
        return t["detractor"] if ctx.classification == "detractor" else t["default"]
