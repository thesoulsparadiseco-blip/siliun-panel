"""
base — estructura común de agente (capa 7 del spec).

Cada agente concreto define, tal como pide la sección 7:
  agent_core       -> name, signature, mission (identidad)
  agent_element    -> afinidad elemental (Tierra/Fuego/Agua/Aire/Éter/None)
  agent_rules      -> should_activate(context): cuándo interviene
  agent_actions    -> manifest(text, context): qué produce
  agent_memory     -> memory_tags(): qué etiquetas usa al guardar en memoria
  agent_signature  -> firma corta que se antepone a su manifestación
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AgentContext:
    """Lo que Synar le pasa a cada agente durante el flujo de ejecución."""
    element: str
    tesla_gate: int
    classification: str  # "atractor" | "detractor" | "neutro"
    user_id: str = "default"


class Agent:
    name: str = "agent"
    signature: str = "•"
    mission: str = ""
    element: Optional[str] = None  # None = agnóstico de elemento (ej. Synar, Arkhon, Jakhar)

    def agent_core(self) -> Dict[str, str]:
        return {"name": self.name, "signature": self.signature, "mission": self.mission}

    def agent_element(self) -> Optional[str]:
        return self.element

    def agent_rules(self, ctx: AgentContext) -> bool:
        """Regla por defecto: interviene si su elemento coincide con el activo."""
        return self.element is None or self.element == ctx.element

    def agent_memory(self) -> List[str]:
        tags = [self.name]
        if self.element:
            tags.append(self.element)
        return tags

    def agent_actions(self, text: str, ctx: AgentContext) -> str:
        raise NotImplementedError

    def manifest(self, text: str, ctx: AgentContext) -> str:
        return f"{self.signature} {self.agent_actions(text, ctx)}"
