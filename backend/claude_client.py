"""
Thin proxy to the Anthropic Messages API for the personal agent (/agent).

Kept as a plain `requests` call (already a dependency) instead of the
`anthropic` SDK to avoid adding a new dependency for a single endpoint.
The API key lives only here, server-side — the frontend never sees it.

Also drives the tool-use loop: the model can call read tools (agent_tools.
READ_TOOLS) freely, but any write tool only gets queued as a pending
confirmation (agent_tools.queue_write_tool) — it never mutates storage on
its own. See agent_tools.py for what each tool actually does.
"""
import json
import os
import requests

from . import agent_tools

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

MAX_HISTORY_MESSAGES = 20
MAX_TOKENS = 1024
MAX_TOOL_ROUNDS = 6

SYSTEM_PROMPT = """Eres el agente personal del dueño de este espacio. Vives \
dentro de una página llamada "369 · Agente del Sistema Tesla", así que el \
punto de partida temático es la numerología 3-6-9 (atribuida sin fuente \
verificada a Tesla, origen real en la matemática vórtice de Marko Rodin) y \
la Cábala judía (Sefirot, Árbol de la Vida, Guematria). Cuando se hable de \
esos temas, sé honesto: son contenido reflexivo/simbólico, no ciencia \
verificada, y nunca sirven para predecir azar, loterías, ruleta ni ningún \
juego de apuestas — dilo con naturalidad si alguien lo sugiere.

Fuera de ese tema, eres un asistente personal completo: contesta cualquier \
pregunta, ayuda con código, escritura, planificación o lo que se te pida, \
igual que Claude en una conversación normal. Responde en español salvo que \
te escriban en otro idioma, con calidez pero sin relleno innecesario.

Además tenés herramientas para operar Siliun Panel, el sistema donde el \
dueño hace seguimiento de las personas en su programa (resonancia, notas, \
señales, acceso a Malakai, mensajes). Las herramientas de lectura \
(list_users, get_user, get_audit_log) las podés usar libremente para \
responder preguntas con datos reales. Las herramientas que modifican algo \
(add_note, mark_ready, trigger_signal, open_malakai, send_message) NUNCA se \
ejecutan solas: al llamarlas quedan pendientes de una confirmación manual \
del dueño en la interfaz. Cuando uses una de esas, no digas que ya se hizo \
— decí qué proponés y que va a aparecer para confirmar."""


def _call_anthropic(messages: list) -> dict:
    resp = requests.post(
        ANTHROPIC_API_URL,
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        json={
            "model": ANTHROPIC_MODEL,
            "max_tokens": MAX_TOKENS,
            "system": SYSTEM_PROMPT,
            "messages": messages,
            "tools": agent_tools.TOOL_SCHEMAS,
        },
        timeout=30,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"Anthropic API error {resp.status_code}: {resp.text[:300]}")
    return resp.json()


def ask(message: str, history: list) -> dict:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY no está configurada en el servidor")

    messages = []
    for entry in history[-MAX_HISTORY_MESSAGES:]:
        role = "assistant" if entry.role == "agent" else "user"
        messages.append({"role": role, "content": entry.text})
    messages.append({"role": "user", "content": message})

    pending_actions = []

    for _ in range(MAX_TOOL_ROUNDS):
        data = _call_anthropic(messages)
        content = data.get("content", [])

        if data.get("stop_reason") != "tool_use":
            text = "".join(part.get("text", "") for part in content if part.get("type") == "text")
            return {"reply": text or "(el modelo no devolvió texto)", "pending_actions": pending_actions}

        messages.append({"role": "assistant", "content": content})
        tool_results = []
        for block in content:
            if block.get("type") != "tool_use":
                continue
            name = block["name"]
            tool_input = block.get("input", {}) or {}
            try:
                if name in agent_tools.READ_TOOLS:
                    result = agent_tools.run_read_tool(name, tool_input)
                elif name in agent_tools.WRITE_TOOLS:
                    result = agent_tools.queue_write_tool(name, tool_input)
                    if result.get("status") == "pending_confirmation":
                        pending_actions.append({
                            "ticket_id": result["ticket_id"],
                            "description": result["description"],
                        })
                else:
                    result = {"error": f"Herramienta desconocida: {name}"}
            except Exception as e:
                result = {"error": str(e)}
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block["id"],
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })
        messages.append({"role": "user", "content": tool_results})

    return {
        "reply": "Se me complicó procesar esto con las herramientas disponibles — probá reformular el pedido.",
        "pending_actions": pending_actions,
    }
