"""
Endpoints del Organismo IA Local (organismo_ia/) montados sobre el
backend existente. Reutiliza la auth del agente personal (AGENT_TOKEN,
agent_auth.verify_agent) porque el organismo es una extensión de ese
mismo agente, no del panel admin (SILIUN_ADMIN_TOKEN es para otra cosa:
gestión de usuarios/founders).

La síntesis final puede delegarse a Claude (claude_client.ask) cuando
ANTHROPIC_API_KEY está configurada; si no, cae al template determinista
de organismo_ia (mismo comportamiento de fallback que ya tiene /agent
cuando falta el token — ver README sección 6).
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from organismo_ia import run, OrganismoResult
from organismo_ia.agents.arkhon import IntegrityViolation
from organismo_ia.ui import MODES

from . import claude_client
from .agent_auth import verify_agent

router = APIRouter(prefix="/organismo", tags=["organismo"])


class InvokeRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=8000)
    user_id: str = "default"
    use_llm: bool = True


def _llm_bridge(prompt: str) -> str:
    return claude_client.ask(prompt, history=[])


@router.post("/invoke")
def invoke(payload: InvokeRequest, token: str = Depends(verify_agent)):
    llm_call = None
    if payload.use_llm and claude_client.ANTHROPIC_API_KEY:
        llm_call = _llm_bridge

    try:
        result: OrganismoResult = run(payload.input, user_id=payload.user_id, llm_call=llm_call)
    except IntegrityViolation as e:
        raise HTTPException(400, str(e))
    except RuntimeError as e:
        raise HTTPException(502, str(e))

    return {
        "session_id": result.session_id,
        "classification": result.classification,
        "element": result.element,
        "tesla_gate": result.tesla_gate,
        "security": result.security,
        "agents_invoked": result.agents_invoked,
        "fragments": result.fragments,
        "manifestation": result.manifestation,
    }


@router.get("/ui/{mode}")
def ui_mode(mode: str, token: str = Depends(verify_agent)):
    describe = MODES.get(mode)
    if describe is None:
        raise HTTPException(404, f"Modo de UI desconocido: '{mode}'. Válidos: {list(MODES)}")
    return describe()
