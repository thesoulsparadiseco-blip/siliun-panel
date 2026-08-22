"""
synthesis_engine — capa 5.2 del spec: el flujo interno completo.

    1. Entrada
    2. Clasificación (atractor/detractor)
    3. Elemento activo
    4. Tesla 3-6-9
    5. Llamada a agentes
    6. Manifestación
    7. Actualización de memoria

Esto es lo que la sección 7 llama "Synar" en su rol coordinador — la
clase Synar en agents/synar.py es la *voz* de ese agente dentro de la
manifestación; la orquestación (esta función) es intencionalmente una
función de módulo, no un método de esa clase, para no acoplar "cómo se
corre el flujo" con "qué dice un agente en particular".

Idioma: si no se pasa `locale`, se detecta automáticamente a partir del
texto de entrada (ver organismo_ia/i18n.detect_locale) — español de
España por defecto, inglés si el texto lo sugiere. Añadir un idioma
nuevo es cuestión de sumar un módulo en organismo_ia/i18n/, no de tocar
este archivo (ver organismo_ia/i18n/__init__.py).

`llm_call`, si se pasa, permite delegar la síntesis final a un LLM en
vez del template determinista. Deliberadamente no hay ningún llamador
por defecto ni en este paquete ni en backend/organismo_router.py: el
organismo es autosuficiente y no depende de ninguna IA externa (sección
1 del spec) — el template determinista es el comportamiento real, no
un fallback. El punto de extensión existe para el día en que el cliente
móvil tenga un core_llm local comprimido corriendo on-device (sección
5.1 del spec); conectarlo ahí nunca implica una llamada de red a un
tercero.
"""
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional
from uuid import uuid4

from ..agents import ALL_AGENTS
from ..agents.arkhon import Arkhon, IntegrityViolation  # noqa: F401 (re-exportado para quien llame run())
from ..agents.base import AgentContext
from ..agents.jakhar import Jakhar
from ..agents.synar import Synar
from ..i18n import DEFAULT_LOCALE, detect_locale, get as get_locale
from ..memory import graph_db, internal, vector_db
from . import attractor, detractor, elemental_engine, tesla_engine

_arkhon = Arkhon()
_jakhar = Jakhar()
_domain_agents = [a for a in ALL_AGENTS if a.element is not None]
_synar = next(a for a in ALL_AGENTS if isinstance(a, Synar))


@dataclass
class OrganismoResult:
    session_id: str
    input_text: str
    locale: str
    classification: str
    element: str
    tesla_gate: int
    security: Dict[str, object]
    agents_invoked: List[str]
    fragments: List[str]
    manifestation: str


def _classify(text: str, locale: str) -> str:
    a, d = attractor.score(text, locale), detractor.score(text, locale)
    if a == 0 and d == 0:
        return "neutral"
    return "attractor" if a >= d else "detractor"


def run(
    input_text: str,
    user_id: str = "default",
    locale: Optional[str] = None,
    llm_call: Optional[Callable[[str], str]] = None,
) -> OrganismoResult:
    locale = locale or detect_locale(input_text)

    # 1. Entrada + seguridad (Arkhon/Jakhar, capa 8)
    clean_text = _arkhon.integrity_check(input_text, locale)  # puede levantar IntegrityViolation
    clean_text = _jakhar.noise_filter(clean_text)

    # 2-4. Clasificación, elemento, Tesla
    classification = _classify(clean_text, locale)
    element = elemental_engine.classify(clean_text, locale).element
    gate = tesla_engine.compute(clean_text).gate
    ctx = AgentContext(element=element, tesla_gate=gate, classification=classification,
                        user_id=user_id, locale=locale)

    security = {
        "arkhon": _arkhon.agent_actions(clean_text, ctx),
        "jakhar_flags": _jakhar.flags(clean_text),
    }

    # 5. Llamada a agentes: Synar coordina, luego los agentes de dominio cuya
    # regla se active para este contexto.
    fragments = [_synar.manifest(clean_text, ctx)]
    agents_invoked = [_synar.name]
    for agent in _domain_agents:
        if agent.agent_rules(ctx):
            fragments.append(agent.manifest(clean_text, ctx))
            agents_invoked.append(agent.name)

    # 6. Manifestación
    if llm_call is not None:
        data = get_locale(locale)
        element_label = data["element_names"].get(element, element)
        classification_label = data["classification_names"].get(classification, classification)
        prompt = data["llm_prompt"].format(
            element=element_label, gate=gate, classification=classification_label,
            fragments="\n".join(fragments), text=clean_text,
        )
        manifestation = llm_call(prompt)
    else:
        manifestation = "\n".join(fragments)

    # 7. Actualización de memoria
    session_id = str(uuid4())
    vector_db.add(user_id, clean_text)
    graph_db.add_node(session_id, "session", clean_text[:80])
    for name in agents_invoked:
        graph_db.add_node(name, "agent", name)
        graph_db.add_edge(session_id, name, "invoked")
    sessions = internal.load("identity").get("session_count", 0)
    internal.update("identity", {"session_count": sessions + 1, "last_element": element})

    return OrganismoResult(
        session_id=session_id,
        input_text=clean_text,
        locale=locale,
        classification=classification,
        element=element,
        tesla_gate=gate,
        security=security,
        agents_invoked=agents_invoked,
        fragments=fragments,
        manifestation=manifestation,
    )
