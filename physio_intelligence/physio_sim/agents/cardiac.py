"""Cardiac Agent (documento maestro, sección 6).

    "FC, HRV, IBI, PPG y ECG puntual cuando esté disponible."

Este agente analiza únicamente el dominio cardiovascular contra el Personal
Baseline y expone una lectura estructurada (`CardiacAssessment`) que el
Fusion Engine combina con el resto de agentes (sección 8, "OTRAS SEÑALES").
El agente en sí nunca decide una alerta global — solo confirma o no sus
propios eventos (los que pertenecen exclusivamente al dominio cardíaco);
una combinación cross-dominio como "glucosa cae + FC sube" sigue siendo
responsabilidad del Fusion Engine, que es quien conoce ambos agentes.

PPG bruto y ECG bajo demanda quedan fuera de este simulador V1 a propósito
(sección 14, V2): son señales de forma de onda, no un escalar por tick como
el resto del modelo de datos (sección 19), y el propio roadmap los ubica en
V2. FC, IBI y HRV sí encajan en el modelo escalar y se implementan aquí.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from ..baseline import PersonalBaseline
from ..events import Event, EventType, make_event
from ..models import ActivityContext, SignalReading, SignalType

HR_ZSCORE_HIGH = 2.5
HR_ZSCORE_LOW = -2.5
RECOVERY_WINDOW_MIN = 10
RECOVERY_HR_MARGIN = 15.0  # bpm por encima del baseline en reposo pre-ejercicio
PERSISTENCE_TICKS = 3       # ticks consecutivos para confirmar un evento


@dataclass
class CardiacAssessment:
    """Lectura cardíaca de este tick, ya contextualizada contra el baseline personal."""

    heart_rate: SignalReading | None = None
    heart_rate_zscore: float | None = None
    hrv: SignalReading | None = None
    hrv_zscore: float | None = None
    ibi: SignalReading | None = None
    ibi_zscore: float | None = None


class CardiacAgent:
    """FC, IBI y HRV contra el patrón personal (sección 6, 'Cardiac Agent')."""

    def __init__(self, baseline: PersonalBaseline) -> None:
        self.baseline = baseline
        self._persistence: dict[EventType, int] = {
            EventType.HR_HIGH_AT_REST: 0,
            EventType.HR_LOW_VS_BASELINE: 0,
            EventType.ABNORMAL_RECOVERY: 0,
        }
        self._exercise_end_hr_baseline: float | None = None
        self._exercise_end_time: datetime | None = None
        self._prev_context: ActivityContext | None = None

    def assess(self, by_type: dict) -> CardiacAssessment:
        """Calcula los z-scores del tick actual, sin mutar ningún estado interno."""
        hr = by_type.get(SignalType.HEART_RATE)
        hrv = by_type.get(SignalType.HRV)
        ibi = by_type.get(SignalType.IBI)
        return CardiacAssessment(
            heart_rate=hr,
            heart_rate_zscore=self.baseline.zscore(hr) if hr else None,
            hrv=hrv,
            hrv_zscore=self.baseline.zscore(hrv) if hrv else None,
            ibi=ibi,
            ibi_zscore=self.baseline.zscore(ibi) if ibi else None,
        )

    def check_events(self, by_type: dict, timestamp: datetime) -> list[Event]:
        """Eventos propios del dominio cardíaco: FC alta/baja en reposo y recuperación anómala."""
        hr = by_type.get(SignalType.HEART_RATE)
        if hr is None:
            self._persistence[EventType.HR_HIGH_AT_REST] = 0
            self._persistence[EventType.HR_LOW_VS_BASELINE] = 0
            return []

        events = self._check_high_low(hr, timestamp)
        events += self._check_recovery(hr, timestamp)
        return events

    def _check_high_low(self, hr: SignalReading, timestamp: datetime) -> list[Event]:
        z = self.baseline.zscore(hr)
        if z is None:
            return []

        high_at_rest = hr.context == ActivityContext.RESTING and z >= HR_ZSCORE_HIGH
        self._persistence[EventType.HR_HIGH_AT_REST] = (
            self._persistence[EventType.HR_HIGH_AT_REST] + 1 if high_at_rest else 0
        )
        low = z <= HR_ZSCORE_LOW
        self._persistence[EventType.HR_LOW_VS_BASELINE] = (
            self._persistence[EventType.HR_LOW_VS_BASELINE] + 1 if low else 0
        )

        if self._persistence[EventType.HR_HIGH_AT_REST] >= PERSISTENCE_TICKS:
            self._persistence[EventType.HR_HIGH_AT_REST] = 0
            return [make_event(
                EventType.HR_HIGH_AT_REST, timestamp,
                f"FC en reposo {hr.value:.0f} bpm, {z:+.1f} DE por encima de tu patrón habitual.",
                [hr],
            )]
        if self._persistence[EventType.HR_LOW_VS_BASELINE] >= PERSISTENCE_TICKS:
            self._persistence[EventType.HR_LOW_VS_BASELINE] = 0
            return [make_event(
                EventType.HR_LOW_VS_BASELINE, timestamp,
                f"FC {hr.value:.0f} bpm, {z:+.1f} DE por debajo de tu patrón habitual.",
                [hr],
            )]
        return []

    def _check_recovery(self, hr: SignalReading, timestamp: datetime) -> list[Event]:
        if self._prev_context == ActivityContext.EXERCISING and hr.context != ActivityContext.EXERCISING:
            self._exercise_end_hr_baseline = self.baseline.mean(SignalType.HEART_RATE, ActivityContext.RESTING)
            self._exercise_end_time = timestamp
            self._persistence[EventType.ABNORMAL_RECOVERY] = 0
        self._prev_context = hr.context

        if self._exercise_end_time is None:
            return []

        elapsed = (timestamp - self._exercise_end_time).total_seconds() / 60.0
        if elapsed > RECOVERY_WINDOW_MIN:
            self._exercise_end_time = None
            self._persistence[EventType.ABNORMAL_RECOVERY] = 0
            return []

        baseline_hr = self._exercise_end_hr_baseline
        not_recovered = (
            baseline_hr is not None
            and hr.context != ActivityContext.EXERCISING
            and hr.value >= baseline_hr + RECOVERY_HR_MARGIN
        )
        self._persistence[EventType.ABNORMAL_RECOVERY] = (
            self._persistence[EventType.ABNORMAL_RECOVERY] + 1 if not_recovered else 0
        )

        if self._persistence[EventType.ABNORMAL_RECOVERY] >= PERSISTENCE_TICKS:
            self._persistence[EventType.ABNORMAL_RECOVERY] = 0
            self._exercise_end_time = None
            return [make_event(
                EventType.ABNORMAL_RECOVERY, timestamp,
                f"FC sigue en {hr.value:.0f} bpm {elapsed:.0f} min después de terminar el ejercicio "
                f"(patrón en reposo: {baseline_hr:.0f} bpm).",
                [hr],
            )]
        return []
