"""Almir — agente de Botánica (fórmulas, plantas, alquimia solar)."""
from .base import Agent, AgentContext


class Almir(Agent):
    name = "Almir"
    signature = "[Almir·Botánica]"
    mission = "fórmulas, plantas, alquimia solar"
    element = "water"

    def agent_actions(self, text: str, ctx: AgentContext) -> str:
        t = self.texts(ctx)
        return t["detractor"] if ctx.classification == "detractor" else t["default"]
