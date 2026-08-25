"""Action Engine (documento maestro, sección 3) — el paso 9 del roadmap
("primera alerta en reloj", sección 30).

    FUSION ENGINE -> PHYSIOLOGICAL RADAR -> ACTION ENGINE -> RELOJ / MÓVIL / ENTORNO -> USUARIO

Traduce cada `Event` del Fusion Engine en lo que llegaría al reloj: un
`WatchAlert` con el mensaje ya redactado por el propio evento (medición +
inferencia, nunca diagnóstico — sección 17: "tu FC está por encima de tu
patrón", no "tienes una arritmia") y las opciones de feedback humano
relevantes para ese evento (sección 12).

No hay reloj real todavía (eso son los pasos 2–4 del roadmap: hardware,
Android/Wear OS). `WatchChannel` es un canal en memoria que solo colecciona
lo que se hubiera entregado — permite probar el contrato de la alerta de
punta a punta, igual que el resto del simulador prueba el resto del
pipeline sin sensores reales. Los canales de MÓVIL y ENTORNO (sección 3)
quedan fuera de este paso a propósito: el roadmap solo pide "primera
alerta en reloj".
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .events import Event, EventType, SystemState

STATE_ICON: dict[SystemState, str] = {
    SystemState.HABITUAL: "🟢",
    SystemState.CAMBIO: "🟡",
    SystemState.COMPROBAR: "🟠",
    SystemState.ALERTA: "🔴",
}

# Opciones de feedback de la sección 12, priorizadas por relevancia para
# cada evento. "Estoy bien" y "Otro" se añaden siempre (primera y última).
_ALWAYS_FIRST = "Estoy bien"
_ALWAYS_LAST = "Otro"

_EVENT_FEEDBACK_OPTIONS: dict[EventType, list[str]] = {
    EventType.GLUCOSE_RAPID_DROP: ["Mareo", "Sed", "Palpitaciones"],
    EventType.GLUCOSE_DROP_HR_UP: ["Mareo", "Palpitaciones", "Sed"],
    EventType.HR_HIGH_AT_REST: ["Palpitaciones", "Estrés", "Falta de aire"],
    EventType.HR_LOW_VS_BASELINE: ["Mareo", "Falta de aire"],
    EventType.THERMAL_LOAD_HIGH: ["Calor", "Sed", "Mareo"],
    EventType.ABNORMAL_RECOVERY: ["Falta de aire", "Palpitaciones"],
    EventType.FALL_IMMOBILITY: ["Dolor", "Mareo"],
    EventType.MULTISENSOR_ANOMALY: [
        "Mareo", "Palpitaciones", "Calor", "Sed", "Falta de aire", "Dolor", "Estrés",
    ],
}


def feedback_options_for(event_type: EventType) -> list[str]:
    specific = _EVENT_FEEDBACK_OPTIONS[event_type]
    return [_ALWAYS_FIRST, *specific, _ALWAYS_LAST]


@dataclass
class WatchAlert:
    """Lo que llegaría a la pantalla del reloj por un evento."""

    event: Event
    icon: str
    title: str
    message: str
    feedback_options: list[str] = field(default_factory=list)


class ActionEngine:
    """Sección 3, 'ACTION ENGINE': el único traductor de Event -> alerta entregable."""

    def build_alert(self, event: Event) -> WatchAlert:
        return WatchAlert(
            event=event,
            icon=STATE_ICON[event.state],
            title=event.label,
            message=event.message,
            feedback_options=feedback_options_for(event.event_type),
        )


class WatchChannel:
    """Canal de entrega simulado (sección 3: RELOJ). Sin hardware real —
    solo colecciona lo que se hubiera enviado, en orden de llegada."""

    def __init__(self) -> None:
        self.delivered: list[WatchAlert] = []

    def send(self, alert: WatchAlert) -> None:
        self.delivered.append(alert)
