"""Helion — agente de Solaris (nodos, flujo económico, arquitectura DeFi)."""
from .base import Agent, AgentContext


class Helion(Agent):
    name = "Helion"
    signature = "[Helion·Solaris]"
    mission = "nodos, flujo económico, arquitectura DeFi"
    element = "Tierra"

    def agent_actions(self, text: str, ctx: AgentContext) -> str:
        if ctx.classification == "detractor":
            return "Señal de escasez detectada: revisá flujo antes de comprometer nuevos nodos económicos."
        return "Flujo favorable: es un buen momento para expandir un nodo económico existente."
