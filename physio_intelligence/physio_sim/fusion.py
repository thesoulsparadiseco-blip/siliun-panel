"""Fusion Engine — sección 6 ('Fusion Agent') y sección 8 ('Flujo de decisión').

100% basado en reglas + estadística + baseline personal (sección 13: "sin
redes neuronales complejas"). Cada señal fiable pasa por:

    ¿ES FIABLE? -> CONTEXTO -> BASELINE -> DESVIACIÓN -> VELOCIDAD ->
    PERSISTENCIA -> OTRAS SEÑALES -> CONFIRMACIÓN -> EVENTO

La "persistencia" evita alertar por un único pico ruidoso: una condición
tiene que sostenerse varios ticks seguidos antes de confirmarse como evento.

Los dominios cardíaco (FC, HRV, IBI) y metabólico (glucosa) viven en
`agents.CardiacAgent` y `agents.MetabolicAgent`: el Fusion Engine los
consulta como a cualquier otro agente especializado (sección 6) y solo
añade las reglas que son genuinamente cross-dominio — glucosa+FC y la
anomalía multisensor, que por definición nadie más que el Fusion Agent
puede ver.
"""
from __future__ import annotations

from datetime import timedelta

from .agents import CardiacAgent, MetabolicAgent
from .baseline import PersonalBaseline
from .events import Event, EventType, make_event
from .history import SignalHistory
from .models import SignalReading, SignalType

# ---- Umbrales de las reglas (constantes ajustables, no aprendidas) ----
GLUCOSE_DROP_HR_COMBO_Z = 1.5      # FC z-score mínimo para la combinación con caída de glucosa
THERMAL_ZSCORE_HIGH = 2.0
THERMAL_AMBIENT_MIN = 30.0         # °C
THERMAL_HUMIDITY_MIN = 60.0        # %
FALL_IMPACT_G = 2.5
IMMOBILITY_WINDOW_MIN = 5
IMMOBILITY_THRESHOLD_G = 0.3
MULTISENSOR_MIN_SIGNALS = 3
MULTISENSOR_ZSCORE = 2.0
PERSISTENCE_TICKS = 3               # ticks consecutivos para confirmar un evento

# Eventos que el propio Fusion Engine posee (los cardíacos y el metabólico
# "puro" viven en sus agentes — ver agents/cardiac.py y agents/metabolic.py).
_FUSION_OWNED_EVENTS = (
    EventType.GLUCOSE_DROP_HR_UP,
    EventType.THERMAL_LOAD_HIGH,
    EventType.FALL_IMMOBILITY,
    EventType.MULTISENSOR_ANOMALY,
)


class FusionEngine:
    def __init__(self, baseline: PersonalBaseline | None = None) -> None:
        self.baseline = baseline or PersonalBaseline()
        self.cardiac = CardiacAgent(self.baseline)
        self.metabolic = MetabolicAgent(self.baseline)
        self._movement_history = SignalHistory()
        self._persistence: dict[EventType, int] = {e: 0 for e in _FUSION_OWNED_EVENTS}

    def ingest(self, readings: list[SignalReading]) -> list[Event]:
        """Procesa un tick (una lectura por señal disponible). Devuelve los eventos confirmados."""
        if not readings:
            return []
        reliable = [r for r in readings if r.reliable]
        for r in reliable:
            if r.signal_type == SignalType.MOVEMENT:
                self._movement_history.add(r)

        by_type = {r.signal_type: r for r in reliable}
        timestamp = readings[0].timestamp

        self.metabolic.observe(by_type)
        cardiac = self.cardiac.assess(by_type)
        metabolic = self.metabolic.assess(by_type)

        events: list[Event] = []
        combo = self._check_glucose_hr_combo(metabolic, cardiac, timestamp)
        events += combo
        if combo:
            # el evento cross-dominio ya explica esta caída: no alertar dos veces
            self.metabolic.reset_rapid_drop_persistence()
        else:
            events += self.metabolic.check_events(metabolic, timestamp)
        events += self.cardiac.check_events(by_type, timestamp)
        events += self._check_thermal(by_type, timestamp)
        events += self._check_fall(by_type, timestamp)
        events += self._check_multisensor_anomaly(
            by_type, timestamp, already_explained=bool(events)
        )

        # El baseline aprende *después* de evaluar, para que una lectura nunca
        # se confirme a sí misma como su propio patrón.
        for r in reliable:
            self.baseline.observe(r)

        return events

    # ---- 2: glucosa + FC (cross-dominio) ----
    def _check_glucose_hr_combo(self, metabolic, cardiac, timestamp) -> list[Event]:
        hr_z = cardiac.heart_rate_zscore
        combo = metabolic.dropping_rapidly and hr_z is not None and hr_z >= GLUCOSE_DROP_HR_COMBO_Z
        self._persistence[EventType.GLUCOSE_DROP_HR_UP] = (
            self._persistence[EventType.GLUCOSE_DROP_HR_UP] + 1 if combo else 0
        )

        if self._persistence[EventType.GLUCOSE_DROP_HR_UP] >= PERSISTENCE_TICKS:
            self._persistence[EventType.GLUCOSE_DROP_HR_UP] = 0
            return [make_event(
                EventType.GLUCOSE_DROP_HR_UP, timestamp,
                f"Glucosa cae {metabolic.glucose_slope:.1f} mg/dL/min con FC {hr_z:+.1f} DE por encima de tu patrón.",
                [metabolic.glucose, cardiac.heart_rate],
            )]
        return []

    # ---- 5: carga térmica ----
    def _check_thermal(self, by_type: dict, timestamp) -> list[Event]:
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
            return [make_event(
                EventType.THERMAL_LOAD_HIGH, timestamp,
                f"Temperatura cutánea {skin_z:+.1f} DE por encima de tu patrón, con ambiente "
                f"{ambient.value:.0f}°C / {humidity.value:.0f}% humedad.",
                [r for r in (skin, ambient, humidity) if r is not None],
            )]
        return []

    # ---- 7: caída + inmovilidad ----
    def _check_fall(self, by_type: dict, timestamp) -> list[Event]:
        movement = by_type.get(SignalType.MOVEMENT)
        if movement is None:
            return []

        cutoff = timestamp - timedelta(minutes=IMMOBILITY_WINDOW_MIN + 2)
        recent = [r for r in self._movement_history.readings if r.timestamp >= cutoff]
        impact = next((r for r in recent if r.value >= FALL_IMPACT_G), None)
        if impact is None:
            return []

        since_impact = [r for r in recent if r.timestamp > impact.timestamp]
        elapsed = (timestamp - impact.timestamp).total_seconds() / 60.0
        immobile = bool(since_impact) and all(r.value < IMMOBILITY_THRESHOLD_G for r in since_impact)

        if elapsed >= IMMOBILITY_WINDOW_MIN and immobile:
            return [make_event(
                EventType.FALL_IMMOBILITY, timestamp,
                f"Impacto de {impact.value:.1f}g seguido de {elapsed:.0f} min sin movimiento.",
                [impact, movement],
            )]
        return []

    # ---- 8: anomalía multisensor no clasificada ----
    def _check_multisensor_anomaly(
        self, by_type: dict, timestamp, already_explained: bool
    ) -> list[Event]:
        deviating: list[tuple[SignalType, SignalReading, float]] = []
        for signal_type, reading in by_type.items():
            if signal_type == SignalType.MOVEMENT:
                continue  # el movimiento ya lo cubre la regla de caída, no aporta z-score útil aquí
            if signal_type == SignalType.IBI:
                continue  # mismo canal cardíaco que heart_rate (IBI = 60000/FC) — contarlo aparte
                          # infla artificialmente el conteo de "señales independientes"
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
            return [make_event(
                EventType.MULTISENSOR_ANOMALY, timestamp,
                f"Varias señales se alejan de tu patrón a la vez: {signals_str}.",
                [r for _, r, _ in deviating],
            )]
        return []
