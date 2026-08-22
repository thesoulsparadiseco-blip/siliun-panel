"""Almir — agente de Botánica (fórmulas, plantas, alquimia solar)."""
from .base import Agent, AgentContext


class Almir(Agent):
    name = "Almir"
    signature = "[Almir·Botánica]"
    mission = "fórmulas, plantas, alquimia solar"
    element = "Agua"

    def agent_actions(self, text: str, ctx: AgentContext) -> str:
        if ctx.classification == "detractor":
            return "Fórmula sugerida: infusión calmante (manzanilla/lavanda) y exposición solar breve al amanecer."
        return "Fórmula sugerida: agua solarizada y una planta de acompañamiento para sostener el estado actual."
