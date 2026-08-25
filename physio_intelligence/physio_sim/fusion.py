"""Fusion Engine — sección 6 ('Fusion Agent') y sección 8 ('Flujo de decisión').

100% basado en reglas + estadística + baseline personal (sección 13: "sin
redes neuronales complejas"). Cada señal fiable pasa por:

    ¿ES FIABLE? -> CONTEXTO -> BASELINE -> DESVIACIÓN -> VELOCIDAD ->
    PERSISTENCIA -> OTRAS SEÑALES -> CONFIRMACIÓN -> EVENTO

La "persistencia" evita alertar por un único pico ruidoso: una condición
tiene que sostenerse varios ticks seguidos antes de confirmarse como evento.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .baseline import PersonalBaseline
from .events import EVENT_DEFAULT_STATE, Event, EventType
from .models import ActivityContext, SignalReading, SignalType

# ---- Umbrales de las reglas (constantes ajustables, no aprendidas) ----
GLUCOSE_RAPID_DROP_RATE = -2.0     # mg/dL por minuto
GLUCOSE_DROP_HR_COMBO_Z = 1.5      # FC z-score mínimo para la combinación con caída de glucosa
HR_ZSCORE_HIGH = 2.5
HR_ZSCORE_LOW = -2.5
THERMAL_ZSCORE_HIGH = 2.0
THERMAL_AMBIENT_MIN = 30.0         # °C
THERMAL_HUMIDITY_MIN = 60.0        # %
RECOVERY_WINDOW_MIN = 10
RECOVERY_HR_MARGIN = 15.0          # bpm por encima del baseline en reposo pre-ejercicio
FALL_IMPACT_G = 2.5
IMMOBILITY_WINDOW_MIN = 5
IMMOBILITY_THRESHOLD_G = 0.3
MULTISENSOR_MIN_SIGNALS = 3
MULTISENSOR_ZSCORE = 2.0
PERSISTENCE_TICKS = 3               # ticks consecutivos para confirmar un evento

_HISTORY_WINDOW = timedelta(minutes=30)


@dataclass
class _SignalHistory:
    readings: deque[SignalReading] = field(default_factory=deque)

    def add(self, reading: SignalReading) -> None:
        self.readings.append(reading)
        cutoff = reading.timestamp - _HISTORY_WINDOW
        while self.readings and self.readings[0].timestamp < cutoff:
            self.readings.popleft()

    def slope_per_minute(self, minutes: float) -> float | None:
        if len(self.readings) < 2:
            return None
        latest = self.readings[-1]
        cutoff = latest.timestamp - timedelta(minutes=minutes)
        window = [r for r in self.readings if r.timestamp >= cutoff]
        if len(window) < 2:
            return None
        first, last = window[0], window[-1]
        dt = (last.timestamp - first.timestamp).total_seconds() / 60.0
        if dt <= 0:
            return None
        return (last.value - first.value) / dt


class FusionEngine:
    def __init__(self, baseline: PersonalBaseline | None = None) -> None:
        self.baseline = baseline or PersonalBaseline()
        self._history: dict[SignalType, _SignalHistory] = {s: _SignalHistory() for s in SignalType}
        self._persistence: dict[EventType, int] = {e: 0 for e in EventType}
        self._exercise_end_hr_baseline: float | None = None
        self._exercise_end_time: datetime | None = None
        self._prev_context: ActivityContext | None = None

    def ingest(self, readings: list[SignalReading]) -> list[Event]:
        """Procesa un tick (una lectura por señal disponible). Devuelve los eventos confirmados."""
        if not readings:
            return []
        reliable = [r for r in readings if r.reliable]
        for r in reliable:
            self._history[r.signal_type].add(r)

        by_type = {r.signal_type: r for r in reliable}
        timestamp = readings[0].timestamp

        events: list[Event] = []
        events += self._check_glucose(by_type, timestamp)
        events += self._check_heart_rate(by_type, timestamp)
        events += self._check_thermal(by_type, timestamp)
        events += self._check_recovery(by_type, timestamp)
        events += self._check_fall(by_type, timestamp)
        events += self._check_multisensor_anomaly(
            by_type, timestamp, already_explained=bool(events)
        )

        # El baseline aprende *después* de evaluar, para que una lectura nunca
        # se confirme a sí misma como su propio patrón.
        for r in reliable:
            self.baseline.observe(r)

        return events

    def _make_event(
        self, event_type: EventType, timestamp: datetime, message: str, readings: list[SignalReading]
    ) -> Event:
        return Event(
            event_type=event_type,
            timestamp=timestamp,
            state=EVENT_DEFAULT_STATE[event_type],
            message=message,
            triggering_readings=list(readings),
        )

    # ---- 1 y 2: glucosa ----
    def _check_glucose(self, by_type: dict, timestamp: datetime) -> list[Event]:
        glucose = by_type.get(SignalType.GLUCOSE)
        if glucose is None:
            self._persistence[EventType.GLUCOSE_RAPID_DROP] = 0
            self._persistence[EventType.GLUCOSE_DROP_HR_UP] = 0
            return []

        slope = self._history[SignalType.GLUCOSE].slope_per_minute(15)
        dropping = slope is not None and slope <= GLUCOSE_RAPID_DROP_RATE
        self._persistence[EventType.GLUCOSE_RAPID_DROP] = (
            self._persistence[EventType.GLUCOSE_RAPID_DROP] + 1 if dropping else 0
        )

        hr = by_type.get(SignalType.HEART_RATE)
        hr_z = self.baseline.zscore(hr) if hr else None
        combo = dropping and hr_z is not None and hr_z >= GLUCOSE_DROP_HR_COMBO_Z
        self._persistence[EventType.GLUCOSE_DROP_HR_UP] = (
            self._persistence[EventType.GLUCOSE_DROP_HR_UP] + 1 if combo else 0
        )

        if self._persistence[EventType.GLUCOSE_DROP_HR_UP] >= PERSISTENCE_TICKS:
            self._persistence[EventType.GLUCOSE_DROP_HR_UP] = 0
            self._persistence[EventType.GLUCOSE_RAPID_DROP] = 0
            return [self._make_event(
                EventType.GLUCOSE_DROP_HR_UP, timestamp,
                f"Glucosa cae {slope:.1f} mg/dL/min con FC {hr_z:+.1f} DE por encima de tu patrón.",
                [glucose, hr],
            )]
        if self._persistence[EventType.GLUCOSE_RAPID_DROP] >= PERSISTENCE_TICKS:
            self._persistence[EventType.GLUCOSE_RAPID_DROP] = 0
            return [self._make_event(
                EventType.GLUCOSE_RAPID_DROP, timestamp,
                f"Glucosa descendiendo a {slope:.1f} mg/dL/min de forma sostenida.",
                [glucose],
            )]
        return []

    # ---- 3 y 4: frecuencia cardíaca ----
    def _check_heart_rate(self, by_type: dict, timestamp: datetime) -> list[Event]:
        hr = by_type.get(SignalType.HEART_RATE)
        if hr is None:
            self._persistence[EventType.HR_HIGH_AT_REST] = 0
            self._persistence[EventType.HR_LOW_VS_BASELINE] = 0
            return []

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
            return [self._make_event(
                EventType.HR_HIGH_AT_REST, timestamp,
                f"FC en reposo {hr.value:.0f} bpm, {z:+.1f} DE por encima de tu patrón habitual.",
                [hr],
            )]
        if self._persistence[EventType.HR_LOW_VS_BASELINE] >= PERSISTENCE_TICKS:
            self._persistence[EventType.HR_LOW_VS_BASELINE] = 0
            return [self._make_event(
                EventType.HR_LOW_VS_BASELINE, timestamp,
                f"FC {hr.value:.0f} bpm, {z:+.1f} DE por debajo de tu patrón habitual.",
                [hr],
            )]
        return []

    # ---- 5: carga térmica ----
    def _check_thermal(self, by_type: dict, timestamp: datetime) -> list[Event]:
        skin = by_type.get(SignalType.SKIN_TEMP)
        ambient = by_type.get(SignalType.AMBIENT_TEMP)
        humidity = by_type.get(SignalType.HUMIDITY)
        if skin is None:
            self._persistence[EventType.THERMAL_LOAD_HIGH] = 0
            return []

        skin_z = self.baseline.zscore(skin)
        heat_index_high = (
            ambient is not None and ambient.value >= THERMAL_AMBIENT_MIN
            and humidity is not None and humidity.value >= THERMAL_HUMIDITY_MIN
        )
        elevated = skin_z is not None and skin_z >= THERMAL_ZSCORE_HIGH and heat_index_high
        self._persistence[EventType.THERMAL_LOAD_HIGH] = (
            self._persistence[EventType.THERMAL_LOAD_HIGH] + 1 if elevated else 0
        )

        if self._persistence[EventType.THERMAL_LOAD_HIGH] >= PERSISTENCE_TICKS:
            self._persistence[EventType.THERMAL_LOAD_HIGH] = 0
            return [self._make_event(
                EventType.THERMAL_LOAD_HIGH, timestamp,
                f"Temperatura cutánea {skin_z:+.1f} DE por encima de tu patrón, con ambiente "
                f"{ambient.value:.0f}°C / {humidity.value:.0f}% humedad.",
                [r for r in (skin, ambient, humidity) if r is not None],
            )]
        return []

    # ---- 6: recuperación tras ejercicio ----
    def _check_recovery(self, by_type: dict, timestamp: datetime) -> list[Event]:
        hr = by_type.get(SignalType.HEART_RATE)
        if hr is None:
            return []

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
            return [self._make_event(
                EventType.ABNORMAL_RECOVERY, timestamp,
                f"FC sigue en {hr.value:.0f} bpm {elapsed:.0f} min después de terminar el ejercicio "
                f"(patrón en reposo: {baseline_hr:.0f} bpm).",
                [hr],
            )]
        return []

    # ---- 7: caída + inmovilidad ----
    def _check_fall(self, by_type: dict, timestamp: datetime) -> list[Event]:
        movement = by_type.get(SignalType.MOVEMENT)
        if movement is None:
            return []

        history = self._history[SignalType.MOVEMENT].readings
        cutoff = timestamp - timedelta(minutes=IMMOBILITY_WINDOW_MIN + 2)
        recent = [r for r in history if r.timestamp >= cutoff]
        impact = next((r for r in recent if r.value >= FALL_IMPACT_G), None)
        if impact is None:
            return []

        since_impact = [r for r in recent if r.timestamp > impact.timestamp]
        elapsed = (timestamp - impact.timestamp).total_seconds() / 60.0
        immobile = bool(since_impact) and all(r.value < IMMOBILITY_THRESHOLD_G for r in since_impact)

        if elapsed >= IMMOBILITY_WINDOW_MIN and immobile:
            return [self._make_event(
                EventType.FALL_IMMOBILITY, timestamp,
                f"Impacto de {impact.value:.1f}g seguido de {elapsed:.0f} min sin movimiento.",
                [impact, movement],
            )]
        return []

    # ---- 8: anomalía multisensor no clasificada ----
    def _check_multisensor_anomaly(
        self, by_type: dict, timestamp: datetime, already_explained: bool
    ) -> list[Event]:
        deviating: list[tuple[SignalType, SignalReading, float]] = []
        for signal_type, reading in by_type.items():
            if signal_type == SignalType.MOVEMENT:
                continue  # el movimiento ya lo cubre la regla de caída, no aporta z-score útil aquí
            z = self.baseline.zscore(reading)
            if z is not None and abs(z) >= MULTISENSOR_ZSCORE:
                deviating.append((signal_type, reading, z))

        qualifies = len(deviating) >= MULTISENSOR_MIN_SIGNALS
        self._persistence[EventType.MULTISENSOR_ANOMALY] = (
            self._persistence[EventType.MULTISENSOR_ANOMALY] + 1 if qualifies else 0
        )

        if self._persistence[EventType.MULTISENSOR_ANOMALY] >= PERSISTENCE_TICKS and not already_explained:
            self._persistence[EventType.MULTISENSOR_ANOMALY] = 0
            signals_str = ", ".join(f"{s.value} ({z:+.1f} DE)" for s, _, z in deviating)
            return [self._make_event(
                EventType.MULTISENSOR_ANOMALY, timestamp,
                f"Varias señales se alejan de tu patrón a la vez: {signals_str}.",
                [r for _, r, _ in deviating],
            )]
        return []
