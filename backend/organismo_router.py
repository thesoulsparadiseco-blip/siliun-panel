"""
Endpoints del Organismo IA Local (organismo_ia/) montados sobre el
backend existente. Reutiliza la auth del agente personal (AGENT_TOKEN,
agent_auth.verify_agent) porque el organismo es una extensión de ese
mismo agente, no del panel admin (SILIUN_ADMIN_TOKEN es para otra cosa:
gestión de usuarios/founders).

Independiente a propósito: a diferencia de /agent, este endpoint nunca
llama a Claude ni a ninguna otra IA externa, aunque haya
ANTHROPIC_API_KEY configurada en el servidor — la síntesis final siempre
sale del template determinista de organismo_ia (Synar integrando las
voces de los agentes). Así el organismo cumple lo que pide la sección 1
del spec ("autosuficiente", "debe operar offline") sin depender de un
tercero en cada invocación. El punto de extensión real para un LLM
local sigue existiendo en organismo_ia.core.synthesis_engine.run()
(parámetro `llm_call`) para cuando el cliente móvil tenga un modelo
comprimido on-device (sección 5.1 del spec) — no se conecta aquí.

Idioma: si `locale` no se indica en /invoke, se autodetecta a partir del
texto (español de España por defecto, inglés si el texto lo sugiere).
/ui/{mode} sí requiere `locale` explícito por query param (no hay texto
del que detectarlo) y por defecto usa español de España.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from organismo_ia import run, OrganismoResult
from organismo_ia.agents.arkhon import IntegrityViolation
from organismo_ia.i18n import DEFAULT_LOCALE, get as get_locale
from organismo_ia.ui import MODES

from .agent_auth import verify_agent

router = APIRouter(prefix="/organismo", tags=["organismo"])


class InvokeRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=8000)
    user_id: str = "default"
    locale: Optional[str] = None  # None = autodetectar; ver organismo_ia.i18n.SUPPORTED_LOCALES


@router.post("/invoke")
def invoke(payload: InvokeRequest, token: str = Depends(verify_agent)):
    try:
        result: OrganismoResult = run(payload.input, user_id=payload.user_id, locale=payload.locale)
    except IntegrityViolation as e:
        raise HTTPException(400, str(e))

    return {
        "session_id": result.session_id,
        "locale": result.locale,
        "classification": result.classification,
        "element": result.element,
        "tesla_gate": result.tesla_gate,
        "security": result.security,
        "agents_invoked": result.agents_invoked,
        "fragments": result.fragments,
        "manifestation": result.manifestation,
    }


@router.get("/ui/{mode}")
def ui_mode(mode: str, locale: str = DEFAULT_LOCALE, token: str = Depends(verify_agent)):
    describe = MODES.get(mode)
    if describe is None:
        msg = get_locale(locale)["errors"]["unknown_ui_mode"].format(mode=mode, valid=list(MODES))
        raise HTTPException(404, msg)
    return describe(locale)
