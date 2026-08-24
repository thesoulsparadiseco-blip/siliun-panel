"""
Short-lived confirmation tickets for mutating agent tool calls.

In-memory only — this is a single-process, single-owner deployment (one
AGENT_TOKEN), so a ticket only needs to survive long enough for the owner
to see it in the chat UI and tap Confirmar/Cancelar. No need for the
persistence guarantees storage.py gives real user data.
"""
import threading
import time
import uuid
from typing import Any, Dict, Optional

TTL_SECONDS = 15 * 60

_lock = threading.Lock()
_pending: Dict[str, Dict[str, Any]] = {}


def _sweep_expired():
    now = time.time()
    for key in [k for k, v in _pending.items() if v["expires_at"] < now]:
        _pending.pop(key, None)


def create_pending_action(tool: str, tool_input: Dict[str, Any], description: str) -> Dict[str, Any]:
    with _lock:
        _sweep_expired()
        ticket_id = uuid.uuid4().hex[:12]
        ticket = {
            "id": ticket_id,
            "tool": tool,
            "input": tool_input,
            "description": description,
            "expires_at": time.time() + TTL_SECONDS,
        }
        _pending[ticket_id] = ticket
        return ticket


def pop_pending_action(ticket_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        _sweep_expired()
        return _pending.pop(ticket_id, None)
