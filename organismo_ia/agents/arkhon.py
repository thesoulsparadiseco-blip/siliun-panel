"""
Arkhon — agente de Guardia (capa 8.1: integrity_checker, memory_cleaner,
agent_supervisor, flow_guard).

Arkhon no "manifiesta" contenido de dominio: corre antes del resto del
flujo como filtro de integridad. `integrity_check` rechaza entradas
vacías/degeneradas y recorta longitudes absurdas (protección básica de
recursos, capa 10.3 del spec).
"""
from ..i18n import DEFAULT_LOCALE, get as get_locale
from .base import Agent, AgentContext

MAX_INPUT_CHARS = 8000


class IntegrityViolation(Exception):
    pass


class Arkhon(Agent):
    name = "Arkhon"
    signature = "[Arkhon·Guardia]"
    mission = "protección interna, filtrado, depuración"
    element = None

    def agent_rules(self, ctx: AgentContext) -> bool:
        return True

    def integrity_check(self, text: str, locale: str = DEFAULT_LOCALE) -> str:
        """flow_guard + integrity_checker: valida y normaliza la entrada."""
        cleaned = text.strip()
        if not cleaned:
            raise IntegrityViolation(get_locale(locale)["agents"]["Arkhon"]["empty_error"])
        if len(cleaned) > MAX_INPUT_CHARS:
            cleaned = cleaned[:MAX_INPUT_CHARS]
        return cleaned

    def agent_actions(self, text: str, ctx: AgentContext) -> str:
        return self.texts(ctx)["ok"]
