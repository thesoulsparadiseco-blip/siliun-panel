"""
Synar — agente de Síntesis (integración total, coherencia, coordinación).

A diferencia de los demás agentes de dominio, Synar no tiene afinidad
elemental fija (agnóstico): su rol es el que describe la sección 9 del
spec — decidir qué agentes intervienen y tejer la manifestación final.
La orquestación real vive en core/synthesis_engine.py; esta clase es la
"voz" de Synar dentro de esa orquestación (el fragmento de cierre que
integra lo que dijeron los demás agentes).
"""
from ..i18n import get as get_locale
from .base import Agent, AgentContext


class Synar(Agent):
    name = "Synar"
    signature = "[Synar·Síntesis]"
    mission = "integración total, coherencia, coordinación"
    element = None

    def agent_rules(self, ctx: AgentContext) -> bool:
        return True  # Synar siempre interviene: coordina, no compite por elemento.

    def agent_actions(self, text: str, ctx: AgentContext) -> str:
        data = get_locale(ctx.locale)
        element_label = data["element_names"].get(ctx.element, ctx.element)
        classification_label = data["classification_names"].get(ctx.classification, ctx.classification)
        return self.texts(ctx)["tmpl"].format(
            element=element_label, gate=ctx.tesla_gate, classification=classification_label,
        )
