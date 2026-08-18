"""
Thin proxy to the Anthropic Messages API for the personal agent (/agent).

Kept as a plain `requests` call (already a dependency) instead of the
`anthropic` SDK to avoid adding a new dependency for a single endpoint.
The API key lives only here, server-side — the frontend never sees it.
"""
import os
import requests

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

MAX_HISTORY_MESSAGES = 20
MAX_TOKENS = 1024

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
te escriban en otro idioma, con calidez pero sin relleno innecesario."""


def ask(message: str, history: list) -> str:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY no está configurada en el servidor")

    messages = []
    for entry in history[-MAX_HISTORY_MESSAGES:]:
        role = "assistant" if entry.role == "agent" else "user"
        messages.append({"role": role, "content": entry.text})
    messages.append({"role": "user", "content": message})

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
        },
        timeout=30,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"Anthropic API error {resp.status_code}: {resp.text[:300]}")

    data = resp.json()
    text = "".join(
        part.get("text", "") for part in data.get("content", []) if part.get("type") == "text"
    )
    return text or "(el modelo no devolvió texto)"
