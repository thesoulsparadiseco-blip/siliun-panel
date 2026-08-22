"""
Synar — agente de Síntesis (integración total, coherencia, coordinación).

A diferencia de los demás agentes de dominio, Synar no tiene afinidad
elemental fija (agnóstico): su rol es el que describe la sección 9 del
spec — decidir qué agentes intervienen y tejer la manifestación final.
La orquestación real vive en core/synthesis_engine.py; esta clase es la
"voz" de Synar dentro de esa orquestación (el fragmento de cierre que
integra lo que dijeron los demás agentes).
"""
from .base import Agent, AgentContext


class Synar(Agent):
    name = "Synar"
    signature = "[Synar·Síntesis]"
    mission = "integración total, coherencia, coordinación"
    element = None

    def agent_rules(self, ctx: AgentContext) -> bool:
        return True  # Synar siempre interviene: coordina, no compite por elemento.

    def agent_actions(self, text: str, ctx: AgentContext) -> str:
        return (f"Elemento activo: {ctx.element} · Puerta Tesla: {ctx.tesla_gate} · "
                f"Lectura: {ctx.classification}. Integrando las voces anteriores en una sola dirección.")
