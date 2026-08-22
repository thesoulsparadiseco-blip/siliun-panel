"""Vitalion — agente de Energía (ritmo, estado interno, activaciones rápidas)."""
from .base import Agent, AgentContext


class Vitalion(Agent):
    name = "Vitalion"
    signature = "[Vitalion·Energía]"
    mission = "ritmo, estado interno, activaciones rápidas"
    element = "Fuego"

    def agent_actions(self, text: str, ctx: AgentContext) -> str:
        gate = ctx.tesla_gate
        if ctx.classification == "detractor":
            return f"Ritmo bajo — puerta {gate}: pausá el impulso, no actúes desde la urgencia."
        return f"Ritmo alto — puerta {gate}: es momento de actuar, el impulso está a favor."
