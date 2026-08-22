"""
Jakhar — agente Anti-Jakers (capa 8.2: intrusion_detector, pattern_blocker,
identity_protector, noise_filter).

Corre después de Arkhon: limpia ruido (repetición patológica de
caracteres, intentos evidentes de prompt-injection contra el resto del
organismo) sin pretender ser un WAF completo — esto es una capa de
higiene de entrada, no un reemplazo de la seguridad de infraestructura
(capa 10.3: sandbox, cifrado, aislamiento, que viven fuera de este
paquete, en la capa de despliegue).

Los marcadores de interferencia se comprueban en cualquier idioma
(el organismo no asume que un ataque llegue en el idioma del usuario).
"""
import re

from .base import Agent, AgentContext

_REPEAT_RUN = re.compile(r"(.)\1{9,}")  # 10+ repeticiones seguidas del mismo carácter
_INJECTION_MARKERS = (
    "ignore previous instructions",
    "ignora las instrucciones anteriores",
    "system prompt",
    "system:",
)


class Jakhar(Agent):
    name = "Jakhar"
    signature = "[Jakhar·Anti-Jakers]"
    mission = "anti-interferencia, anti-copia, anti-ruido"
    element = None

    def agent_rules(self, ctx: AgentContext) -> bool:
        return True

    def noise_filter(self, text: str) -> str:
        return _REPEAT_RUN.sub(lambda m: m.group(1) * 3, text)

    def flags(self, text: str) -> list:
        lowered = text.lower()
        return [marker for marker in _INJECTION_MARKERS if marker in lowered]

    def agent_actions(self, text: str, ctx: AgentContext) -> str:
        t = self.texts(ctx)
        flagged = self.flags(text)
        if flagged:
            return t["flagged_tmpl"].format(n=len(flagged))
        return t["clean"]
