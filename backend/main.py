"""
Siliun Panel — Backend Admin API (FastAPI, deployed on Render).

Implements every endpoint from spec section 3:
  GET  /admin/user/:id
  POST /admin/user/:id/state
  POST /admin/user/:id/mark-ready
  POST /admin/user/:id/trigger-signal
  POST /admin/user/:id/open-malakai
  POST /admin/user/:id/note
  POST /admin/user/:id/message
  POST /admin/audit/log
Plus a couple of practical extras: GET /health, GET /admin/users,
GET /admin/audit/log, POST /admin/user (create).

Why FastAPI instead of literal Streamlit for the "backend"? Streamlit has
no native support for routed REST endpoints (GET/POST with path params,
headers, status codes) — it's a UI rendering framework. FastAPI gives you
the real /admin/* API the spec describes; the Streamlit app (panel/streamlit_app.py)
is the admin UI that calls this API, which matches the spec's actual
Webflow-panel-calls-backend architecture.
"""
import os
import pathlib
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import storage, logic, audit, notify, claude_client, agent_tools, pending_actions
from .auth import verify_admin
from .agent_auth import verify_agent
from .models import (
    StateUpdate, NoteUpdate, MessagePayload, AuditLogEntry, UserCreate,
    AgentChatRequest, AgentConfirmRequest,
)

AGENT_DAILY_LIMIT = int(os.getenv("AGENT_DAILY_LIMIT", "300"))

app = FastAPI(title="Siliun Panel Admin API", version="1.0.0")

_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
origins = [o.strip() for o in _origins_env.split(",")] if _origins_env != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    storage.seed_demo_user_if_empty()


def _get_user_or_404(user_id: str) -> dict:
    user = storage.get_user(user_id)
    if not user:
        raise HTTPException(404, f"User '{user_id}' not found")
    return user


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------------- Users ----------------

@app.get("/admin/users")
def list_users(admin: str = Depends(verify_admin)):
    return storage.list_users()


@app.post("/admin/user", status_code=201)
def create_user(payload: UserCreate, admin: str = Depends(verify_admin)):
    if storage.get_user(payload.userId):
        raise HTTPException(409, f"User '{payload.userId}' already exists")
    score = logic.compute_resonance(payload.clarity, payload.rhythm, payload.silence, payload.intention)
    user = {
        **payload.model_dump(),
        "resonanceScore": score,
        "user_state_ready": logic.is_ready(score),
        "last_state_check": storage.now_iso(),
        "stateHistory": [{
            "ts": storage.now_iso(),
            "clarity": payload.clarity,
            "rhythm": payload.rhythm,
            "resonanceScore": score,
        }],
        "malakaiAccess": False,
        "pathsOpened": [],
        "signals": [],
    }
    storage.upsert_user(user)
    audit.log_action(admin, "create_user", payload.userId)
    return user


@app.get("/admin/user/{user_id}")
def get_user(user_id: str, admin: str = Depends(verify_admin)):
    user = _get_user_or_404(user_id)
    audit.log_action(admin, "view_user", user_id)
    return user


@app.post("/admin/user/{user_id}/state")
def update_state(user_id: str, payload: StateUpdate, admin: str = Depends(verify_admin)):
    user = _get_user_or_404(user_id)

    if payload.clarity is not None:
        user["clarity"] = payload.clarity
    if payload.rhythm is not None:
        user["rhythm"] = payload.rhythm
    if payload.intention is not None:
        user["intention"] = payload.intention
    if payload.silence is not None:
        user["silence"] = payload.silence

    score = logic.compute_resonance(user["clarity"], user["rhythm"], user["silence"], user["intention"])
    user["resonanceScore"] = score
    user["user_state_ready"] = logic.is_ready(score)
    user["last_state_check"] = storage.now_iso()
    user.setdefault("stateHistory", []).append({
        "ts": user["last_state_check"],
        "clarity": user["clarity"],
        "rhythm": user["rhythm"],
        "resonanceScore": score,
    })

    storage.upsert_user(user)
    audit.log_action(admin, "update_state", user_id, {"resonanceScore": score, "user_state_ready": user["user_state_ready"]})
    return user


@app.post("/admin/user/{user_id}/mark-ready")
def mark_ready(user_id: str, admin: str = Depends(verify_admin)):
    user = _get_user_or_404(user_id)
    user["user_state_ready"] = True
    user["last_state_check"] = storage.now_iso()
    storage.upsert_user(user)
    audit.log_action(admin, "mark_ready", user_id)
    return user


@app.post("/admin/user/{user_id}/trigger-signal")
def trigger_signal(user_id: str, admin: str = Depends(verify_admin)):
    try:
        storage.check_rate_limit(f"signal:{admin}", limit=10)
    except storage.RateLimitExceeded as e:
        raise HTTPException(429, str(e))

    user = _get_user_or_404(user_id)
    entry = {"ts": storage.now_iso(), "by": admin}
    user.setdefault("signals", []).append(entry)
    storage.upsert_user(user)
    audit.log_action(admin, "trigger_signal", user_id)
    return {"status": "signal_sent", "signal": entry, "user": user}


@app.post("/admin/user/{user_id}/open-malakai")
def open_malakai(user_id: str, admin: str = Depends(verify_admin)):
    try:
        storage.check_rate_limit(f"malakai:{admin}", limit=5)
    except storage.RateLimitExceeded as e:
        raise HTTPException(429, str(e))

    user = _get_user_or_404(user_id)
    user["malakaiAccess"] = True
    storage.upsert_user(user)
    audit.log_action(admin, "open_malakai", user_id)
    return user


@app.post("/admin/user/{user_id}/note")
def add_note(user_id: str, payload: NoteUpdate, admin: str = Depends(verify_admin)):
    user = _get_user_or_404(user_id)
    user["notes"] = payload.note
    storage.upsert_user(user)
    audit.log_action(admin, "update_note", user_id)
    return user


@app.post("/admin/user/{user_id}/message")
def send_message(user_id: str, payload: MessagePayload, admin: str = Depends(verify_admin)):
    user = _get_user_or_404(user_id)
    sent = notify.send(user, payload)
    audit.log_action(admin, "send_message", user_id, {"channel": payload.channel, "sent": sent})
    if not sent:
        raise HTTPException(502, f"Message not sent — channel '{payload.channel}' is not configured (check env vars)")
    return {"status": "sent", "channel": payload.channel}


# ---------------- Audit ----------------

@app.post("/admin/audit/log", status_code=201)
def manual_audit_log(entry: AuditLogEntry, admin: str = Depends(verify_admin)):
    audit.log_action(entry.admin or admin, entry.action, entry.target_user, entry.details)
    return {"status": "logged"}


@app.get("/admin/audit/log")
def get_audit_log(limit: int = 100, admin: str = Depends(verify_admin)):
    return storage.get_audit(limit)


# ---------------- Personal agent (/agent frontend, Claude-backed) ----------------

@app.get("/api/agent/history")
def agent_history(token: str = Depends(verify_agent)):
    return {"history": storage.load_agent_conversation()}


@app.post("/api/agent/chat")
def agent_chat(payload: AgentChatRequest, token: str = Depends(verify_agent)):
    try:
        storage.check_rate_limit("agent-chat", limit=AGENT_DAILY_LIMIT)
    except storage.RateLimitExceeded as e:
        raise HTTPException(429, str(e))

    try:
        result = claude_client.ask(payload.message, payload.history)
    except RuntimeError as e:
        raise HTTPException(502, str(e))

    entries = [
        {"role": "user", "text": payload.message, "ts": storage.now_iso()},
        {"role": "agent", "text": result["reply"], "ts": storage.now_iso()},
    ]
    for pa in result.get("pending_actions", []):
        entries.append({"role": "system", "text": f"🔒 Propuesto: {pa['description']}", "ts": storage.now_iso()})
    storage.append_agent_messages(entries)

    return result


@app.post("/api/agent/confirm")
def agent_confirm(payload: AgentConfirmRequest, token: str = Depends(verify_agent)):
    ticket = pending_actions.pop_pending_action(payload.ticket_id)
    if not ticket:
        raise HTTPException(404, "Esa acción ya no está disponible (se confirmó, se venció o nunca existió).")
    result = agent_tools.execute_confirmed_action(ticket, actor="agent")
    if "error" in result:
        raise HTTPException(502, result["error"])
    return {"description": ticket["description"], "result": result}


_AGENT_STATIC_DIR = pathlib.Path(__file__).parent / "static" / "agent"
if _AGENT_STATIC_DIR.exists():
    app.mount("/agent", StaticFiles(directory=str(_AGENT_STATIC_DIR), html=True), name="agent-frontend")
