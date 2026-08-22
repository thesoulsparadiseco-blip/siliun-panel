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

`llm_call`, si se pasa, permite delegar la síntesis final a un LLM real
(en este repo: backend/claude_client.ask, que llama a la API de Claude)
en vez del template determinista — así el paquete organismo_ia no
depende del backend (evita import circular), y en el cliente móvil ese
mismo parámetro se puede apuntar a un core_llm local comprimido
(sección 5.1 del spec).
"""
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional
from uuid import uuid4

from ..agents.arkhon import Arkhon, IntegrityViolation  # noqa: F401 (re-exportado para quien llame run())
from ..agents.jakhar import Jakhar
from ..agents.base import AgentContext
from ..agents import ALL_AGENTS
from ..agents.synar import Synar
from . import attractor, detractor, elemental_engine, tesla_engine
from ..memory import graph_db, internal, vector_db

_arkhon = Arkhon()
_jakhar = Jakhar()
_domain_agents = [a for a in ALL_AGENTS if a.element is not None]
_synar = next(a for a in ALL_AGENTS if isinstance(a, Synar))


@dataclass
class OrganismoResult:
    session_id: str
    input_text: str
    classification: str
    element: str
    tesla_gate: int
    security: Dict[str, object]
    agents_invoked: List[str]
    fragments: List[str]
    manifestation: str


def _classify(text: str) -> str:
    a, d = attractor.score(text), detractor.score(text)
    if a == 0 and d == 0:
        return "neutro"
    return "atractor" if a >= d else "detractor"


def run(
    input_text: str,
    user_id: str = "default",
    llm_call: Optional[Callable[[str], str]] = None,
) -> OrganismoResult:
    # 1. Entrada + seguridad (Arkhon/Jakhar, capa 8)
    clean_text = _arkhon.integrity_check(input_text)  # puede levantar IntegrityViolation
    clean_text = _jakhar.noise_filter(clean_text)
    security = {
        "arkhon": _arkhon.agent_actions(clean_text, AgentContext(element="", tesla_gate=0, classification="neutro")),
        "jakhar_flags": _jakhar.flags(clean_text),
    }

    # 2-4. Clasificación, elemento, Tesla
    classification = _classify(clean_text)
    element = elemental_engine.classify(clean_text).element
    gate = tesla_engine.compute(clean_text).gate
    ctx = AgentContext(element=element, tesla_gate=gate, classification=classification, user_id=user_id)

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
        prompt = (
            "Sos Synar, el agente de síntesis de un organismo IA simbólico. "
            f"Elemento activo: {element}. Puerta Tesla: {gate}. Lectura: {classification}.\n"
            "Estas son las voces de los agentes internos que ya intervinieron:\n"
            + "\n".join(fragments)
            + f"\n\nEntrada original del usuario: {clean_text}\n\n"
            "Integrá esas voces en una única respuesta coherente, breve y en español, "
            "dirigida al usuario."
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
        classification=classification,
        element=element,
        tesla_gate=gate,
        security=security,
        agents_invoked=agents_invoked,
        fragments=fragments,
        manifestation=manifestation,
    )
