"""Vitalion — agente de Energía (ritmo, estado interno, activaciones rápidas)."""
from .base import Agent, AgentContext


class Vitalion(Agent):
    name = "Vitalion"
    signature = "[Vitalion·Energía]"
    mission = "ritmo, estado interno, activaciones rápidas"
    element = "fire"

    def agent_actions(self, text: str, ctx: AgentContext) -> str:
        t = self.texts(ctx)
        tmpl = t["detractor_tmpl"] if ctx.classification == "detractor" else t["default_tmpl"]
        return tmpl.format(gate=ctx.tesla_gate)
