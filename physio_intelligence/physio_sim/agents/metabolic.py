"""Metabolic Agent (documento maestro, sección 6).

    "Glucosa, tendencias, comidas y ejercicio."

Analiza únicamente el dominio metabólico: nivel de glucosa y su pendiente
(tendencia) contra el Personal Baseline. El contexto de comidas y ejercicio
ya lo captura `ActivityContext.AFTER_MEAL` / `EXERCISING` en cada lectura —
el Personal Baseline (sección 10) es quien mantiene un patrón de glucosa
distinto por contexto, así que este agente no duplica esa lógica.

Al igual que el Cardiac Agent, solo posee el evento que es puramente suyo
(glucosa cayendo rápido). La combinación "glucosa cae + FC sube" (evento 2,
sección 7) sigue siendo del Fusion Engine: es la definición misma de un
evento cross-dominio — ningún agente individual puede verla por sí solo
(sección 6, "Fusion Agent: integra todo").
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..baseline import PersonalBaseline
from ..events import Event, EventType, make_event
from ..history import SignalHistory
from ..models import SignalReading, SignalType

GLUCOSE_RAPID_DROP_RATE = -2.0     # mg/dL por minuto
SLOPE_WINDOW_MIN = 15.0
PERSISTENCE_TICKS = 3               # ticks consecutivos para confirmar el evento


@dataclass
class MetabolicAssessment:
    """Lectura metabólica de este tick: nivel de glucosa y su pendiente reciente."""

    glucose: SignalReading | None = None
    glucose_slope: float | None = None   # mg/dL por minuto, ventana de 15 min
    dropping_rapidly: bool = False


class MetabolicAgent:
    """Glucosa y su tendencia contra el patrón personal (sección 6, 'Metabolic Agent')."""

    def __init__(self, baseline: PersonalBaseline) -> None:
        self.baseline = baseline
        self._history = SignalHistory()
        self._persistence: dict[EventType, int] = {EventType.GLUCOSE_RAPID_DROP: 0}

    def observe(self, by_type: dict) -> None:
        """Añade la glucosa de este tick al historial. Llamar antes de `assess`."""
        glucose = by_type.get(SignalType.GLUCOSE)
        if glucose is not None and glucose.reliable:
            self._history.add(glucose)

    def assess(self, by_type: dict) -> MetabolicAssessment:
        """Calcula la pendiente actual, sin mutar ningún estado de persistencia."""
        glucose = by_type.get(SignalType.GLUCOSE)
        if glucose is None:
            return MetabolicAssessment()
        slope = self._history.slope_per_minute(SLOPE_WINDOW_MIN)
        dropping = slope is not None and slope <= GLUCOSE_RAPID_DROP_RATE
        return MetabolicAssessment(glucose=glucose, glucose_slope=slope, dropping_rapidly=dropping)

    def check_events(self, assessment: MetabolicAssessment, timestamp: datetime) -> list[Event]:
        """Evento propio del dominio metabólico: glucosa descendiendo rápidamente."""
        if assessment.glucose is None:
            self._persistence[EventType.GLUCOSE_RAPID_DROP] = 0
            return []

        self._persistence[EventType.GLUCOSE_RAPID_DROP] = (
            self._persistence[EventType.GLUCOSE_RAPID_DROP] + 1 if assessment.dropping_rapidly else 0
        )
        if self._persistence[EventType.GLUCOSE_RAPID_DROP] >= PERSISTENCE_TICKS:
            self._persistence[EventType.GLUCOSE_RAPID_DROP] = 0
            return [make_event(
                EventType.GLUCOSE_RAPID_DROP, timestamp,
                f"Glucosa descendiendo a {assessment.glucose_slope:.1f} mg/dL/min de forma sostenida.",
                [assessment.glucose],
            )]
        return []

    def reset_rapid_drop_persistence(self) -> None:
        """Llamado por el Fusion Engine cuando el evento cross-dominio (glucosa+FC) ya
        explica esta misma caída, para no alertar dos veces por el mismo episodio."""
        self._persistence[EventType.GLUCOSE_RAPID_DROP] = 0
