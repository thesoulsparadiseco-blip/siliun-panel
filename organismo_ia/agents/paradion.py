"""Paradion — agente de Expansión (viralidad, narrativa, experiencias)."""
from .base import Agent, AgentContext


class Paradion(Agent):
    name = "Paradion"
    signature = "[Paradion·Expansión]"
    mission = "viralidad, narrativa, experiencias"
    element = "ether"

    def agent_actions(self, text: str, ctx: AgentContext) -> str:
        return self.texts(ctx)["default"]
