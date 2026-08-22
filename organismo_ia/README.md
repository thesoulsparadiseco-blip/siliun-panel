# Organismo IA Local — implementación

Implementación ejecutable del documento técnico *Organismo IA Local ·
Arquitectura Ejecutable* (v1.0, 22/08/2026), acotada a lo que puede
correr en un backend de servidor (este repo es un panel + agente cloud,
no una app móvil nativa). Montado en el backend existente en
`/organismo/*` (ver `backend/organismo_router.py`).

## Qué corre completo acá vs. qué queda como interfaz

El spec pide un organismo que vive **en el móvil** (Flutter/React
Native + Kotlin/Swift, LLM comprimido on-device, STT/TTS, cámara,
sensores). Este repo es un backend Python en la nube — así que:

| Capa del spec | Implementado acá | Estado |
|---|---|---|
| 5. IA local (Tesla, elemental, atractor/detractor, síntesis) | `core/` | ✅ funcional |
| 7. Agentes internos (Solkin…Jakhar) | `agents/` | ✅ funcional |
| 6. Memoria (interna, vector DB, grafo) | `memory/` | ✅ funcional (sqlite, sin deps nuevas) |
| 8. Seguridad (Arkhon/Jakhar) | `agents/arkhon.py`, `agents/jakhar.py` | ✅ funcional (higiene de entrada; sandbox/cifrado de disco son de la capa de despliegue, fuera de este paquete) |
| 4.2 module_text | `modules/text.py` | ✅ funcional |
| 4.2 module_botanica (fórmulas) | `modules/botanica.py` | ✅ funcional (memoria, no hardware) |
| 4.2 module_voice / module_vision / module_movement / module_energy | `modules/voice.py`, `vision.py`, `movement.py`, `energy.py` | ⏳ interfaz documentada — requieren micrófono/cámara/sensores, se implementan en el cliente móvil (sección 4.1) |
| 1/4 UI (portal, ritual, lab, metaverso) | `ui/` | ✅ contratos JSON — el render real es del frontend (Flutter o el panel Streamlit existente) |
| 5.1 core_llm | — | delegado: `backend/claude_client.ask` (Claude real) si hay `ANTHROPIC_API_KEY`, si no, template determinista de `synthesis_engine` |

## Flujo (sección 9 del spec)

`core/synthesis_engine.run(input_text, user_id, llm_call=None)`:

1. **Entrada + seguridad** — Arkhon valida integridad (rechaza vacío,
   recorta tamaños absurdos), Jakhar filtra ruido/patrones de
   interferencia.
2. **Clasificación** atractor/detractor (`core/attractor.py`,
   `core/detractor.py`).
3. **Elemento activo** (`core/elemental_engine.py`): Tierra/Fuego/Agua/
   Aire/Éter por conteo de palabras clave.
4. **Tesla 3-6-9** (`core/tesla_engine.py`): raíz digital del texto,
   mapeada a la puerta 3/6/9 más cercana.
5. **Llamada a agentes**: Synar coordina siempre; los agentes de
   dominio (Solkin, Vitalion, Almir, Nodar, Helion, Paradion) se activan
   si su elemento coincide con el elemento activo.
6. **Manifestación**: se unen las voces de los agentes; si se pasa
   `llm_call` (en el backend, Claude), se le pide una síntesis final
   coherente en vez del join literal.
7. **Memoria**: la interacción se guarda en `memory/vector_db.py`
   (embeddings locales por hashing) y `memory/graph_db.py` (nodos
   sesión/agente), y se actualiza `memory/internal.py` (`identity.json`).

## Nota de honestidad

Igual que `backend/claude_client.py`, esto es contenido
simbólico/reflexivo (numerología 3-6-9, elementos, agentes) — no ciencia
verificada. Los engines son heurísticas deterministas y auditables, no
modelos entrenados ni predicciones de nada.
