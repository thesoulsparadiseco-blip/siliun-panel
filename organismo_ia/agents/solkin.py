"""Solkin — agente de Cuerpo (movimiento, biomecánica, activaciones, salud integrativa)."""
from .base import Agent, AgentContext


class Solkin(Agent):
    name = "Solkin"
    signature = "[Solkin·Cuerpo]"
    mission = "movimiento, biomecánica, activaciones, salud integrativa"
    element = "Tierra"

    def agent_actions(self, text: str, ctx: AgentContext) -> str:
        if ctx.classification == "detractor":
            return ("Bajá al cuerpo: 3 respiraciones lentas, apoyo de pies en el piso, "
                    "y una activación breve (movilidad de cadera y hombros) antes de seguir.")
        return ("Sostené la energía con una activación corporal corta: postura erguida, "
                "respiración diafragmática y una caminata de 5-10 minutos para integrar.")
