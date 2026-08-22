"""Helion — agente de Solaris (nodos, flujo económico, arquitectura DeFi)."""
from .base import Agent, AgentContext


class Helion(Agent):
    name = "Helion"
    signature = "[Helion·Solaris]"
    mission = "nodos, flujo económico, arquitectura DeFi"
    element = "earth"

    def agent_actions(self, text: str, ctx: AgentContext) -> str:
        t = self.texts(ctx)
        return t["detractor"] if ctx.classification == "detractor" else t["default"]
