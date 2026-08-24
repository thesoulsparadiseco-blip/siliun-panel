"""
Tools the personal agent (/agent) can call via the Anthropic API's tool-use
feature, so it can act on Siliun Panel data instead of only talking about it.

Read tools run immediately. Anything that mutates a user record goes through
pending_actions instead of executing straight away — the model can only
*propose* it; storage only actually changes once the owner taps Confirmar in
the chat UI, which calls execute_confirmed_action(). Every confirmed action
is written to the same audit log as a normal admin action, tagged as coming
from the agent.
"""
from types import SimpleNamespace
from typing import Any, Dict

from . import audit, notify, storage
from .pending_actions import create_pending_action

READ_TOOLS = {"list_users", "get_user", "get_audit_log"}
WRITE_TOOLS = {"add_note", "mark_ready", "trigger_signal", "open_malakai", "send_message"}

TOOL_SCHEMAS = [
    {
        "name": "list_users",
        "description": "Lista todas las personas del panel con su resonanceScore y si están listas (user_state_ready).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_user",
        "description": "Trae el registro completo de una persona: resonancia, notas, señales, historial de estado.",
        "input_schema": {
            "type": "object",
            "properties": {"user_id": {"type": "string", "description": "userId exacto, ej. u_12345"}},
            "required": ["user_id"],
        },
    },
    {
        "name": "get_audit_log",
        "description": "Trae las últimas acciones registradas en el audit log del panel.",
        "input_schema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "description": "Cuántas entradas traer (default 20)"}},
        },
    },
    {
        "name": "add_note",
        "description": (
            "Reemplaza la nota de una persona. Acción sensible: no se aplica sola, queda "
            "pendiente de confirmación explícita del dueño en la interfaz."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"user_id": {"type": "string"}, "note": {"type": "string"}},
            "required": ["user_id", "note"],
        },
    },
    {
        "name": "mark_ready",
        "description": "Marca a una persona como lista (user_state_ready = true). Acción sensible: pendiente de confirmación.",
        "input_schema": {
            "type": "object",
            "properties": {"user_id": {"type": "string"}},
            "required": ["user_id"],
        },
    },
    {
        "name": "trigger_signal",
        "description": "Dispara una señal para una persona. Acción sensible: pendiente de confirmación.",
        "input_schema": {
            "type": "object",
            "properties": {"user_id": {"type": "string"}},
            "required": ["user_id"],
        },
    },
    {
        "name": "open_malakai",
        "description": "Abre el acceso a Malakai para una persona (malakaiAccess = true). Acción sensible: pendiente de confirmación.",
        "input_schema": {
            "type": "object",
            "properties": {"user_id": {"type": "string"}},
            "required": ["user_id"],
        },
    },
    {
        "name": "send_message",
        "description": "Manda un mensaje a una persona por Discord o email. Acción sensible: pendiente de confirmación.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "body": {"type": "string"},
                "subject": {"type": "string"},
                "channel": {"type": "string", "enum": ["discord", "email"], "description": "default: discord"},
            },
            "required": ["user_id", "body"],
        },
    },
]


def _describe(name: str, tool_input: Dict[str, Any]) -> str:
    user_id = tool_input.get("user_id", "?")
    if name == "add_note":
        return f'Actualizar la nota de {user_id} a: "{tool_input.get("note", "")}"'
    if name == "mark_ready":
        return f"Marcar a {user_id} como listo (user_state_ready = true)"
    if name == "trigger_signal":
        return f"Disparar una señal para {user_id}"
    if name == "open_malakai":
        return f"Abrir el acceso a Malakai para {user_id}"
    if name == "send_message":
        channel = tool_input.get("channel", "discord")
        return f'Mandarle un mensaje por {channel} a {user_id}: "{tool_input.get("body", "")}"'
    return f"{name}({tool_input})"


def run_read_tool(name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    if name == "list_users":
        return {
            "users": [
                {
                    "userId": u.get("userId"),
                    "name": u.get("name"),
                    "resonanceScore": u.get("resonanceScore"),
                    "user_state_ready": u.get("user_state_ready"),
                    "malakaiAccess": u.get("malakaiAccess"),
                }
                for u in storage.list_users()
            ]
        }
    if name == "get_user":
        user = storage.get_user(tool_input.get("user_id", ""))
        if not user:
            return {"error": f"No existe el usuario '{tool_input.get('user_id')}'"}
        return user
    if name == "get_audit_log":
        limit = int(tool_input.get("limit") or 20)
        return {"entries": storage.get_audit(limit)}
    raise ValueError(f"Unknown read tool: {name}")


def queue_write_tool(name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
    if name not in WRITE_TOOLS:
        raise ValueError(f"Unknown write tool: {name}")
    user_id = tool_input.get("user_id")
    if not user_id or not storage.get_user(user_id):
        return {"error": f"No existe el usuario '{user_id}', no se puede proponer la acción."}
    ticket = create_pending_action(name, tool_input, _describe(name, tool_input))
    return {
        "status": "pending_confirmation",
        "ticket_id": ticket["id"],
        "description": ticket["description"],
        "note_to_model": (
            "Todavía no se ejecutó nada. Contale al dueño qué acción proponés y que la va a ver "
            "como una tarjeta con botones Confirmar/Cancelar — no digas que ya está hecha."
        ),
    }


def execute_confirmed_action(ticket: Dict[str, Any], actor: str = "agent") -> Dict[str, Any]:
    name = ticket["tool"]
    tool_input = ticket["input"]
    user_id = tool_input.get("user_id")
    user = storage.get_user(user_id)
    if not user:
        return {"error": f"'{user_id}' ya no existe"}

    if name == "add_note":
        user["notes"] = tool_input.get("note", "")
        storage.upsert_user(user)
        audit.log_action(actor, "update_note", user_id, {"via": "agent"})
        return {"status": "done"}

    if name == "mark_ready":
        user["user_state_ready"] = True
        user["last_state_check"] = storage.now_iso()
        storage.upsert_user(user)
        audit.log_action(actor, "mark_ready", user_id, {"via": "agent"})
        return {"status": "done"}

    if name == "trigger_signal":
        try:
            storage.check_rate_limit(f"signal:{actor}", limit=10)
        except storage.RateLimitExceeded as e:
            return {"error": str(e)}
        entry = {"ts": storage.now_iso(), "by": actor}
        user.setdefault("signals", []).append(entry)
        storage.upsert_user(user)
        audit.log_action(actor, "trigger_signal", user_id, {"via": "agent"})
        return {"status": "signal_sent"}

    if name == "open_malakai":
        try:
            storage.check_rate_limit(f"malakai:{actor}", limit=5)
        except storage.RateLimitExceeded as e:
            return {"error": str(e)}
        user["malakaiAccess"] = True
        storage.upsert_user(user)
        audit.log_action(actor, "open_malakai", user_id, {"via": "agent"})
        return {"status": "done"}

    if name == "send_message":
        payload = SimpleNamespace(
            subject=tool_input.get("subject"),
            body=tool_input.get("body", ""),
            channel=tool_input.get("channel", "discord"),
        )
        sent = notify.send(user, payload)
        audit.log_action(actor, "send_message", user_id, {"channel": payload.channel, "sent": sent, "via": "agent"})
        if not sent:
            return {"error": f"No se pudo mandar: el canal '{payload.channel}' no está configurado"}
        return {"status": "sent", "channel": payload.channel}

    return {"error": f"Acción desconocida: {name}"}
