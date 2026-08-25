"""Escenarios sintéticos — el Simulador Fisiológico de la sección 23.

Sin sensores reales: cada escenario es una lista de 'fases' (contexto +
valores base) que se convierte en lecturas minuto a minuto de las seis
señales núcleo de V1 (glucosa, FC, temperatura cutánea, movimiento,
temperatura ambiente, humedad). Sirven para probar baseline, cambio,
persistencia, fusión, evento y alerta sin esperar a tener hardware.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta

from .models import ActivityContext, SignalReading, SignalType

TICK_MINUTES = 1


@dataclass
class Phase:
    duration_min: int
    context: ActivityContext = ActivityContext.RESTING
    glucose_slope: float = 0.0          # mg/dL por minuto, respecto al valor acumulado
    heart_rate: float = 65.0
    skin_temp: float = 33.0
    ambient_temp: float = 22.0
    humidity: float = 45.0
    movement: float = 0.05
    movement_spike_at: int | None = None  # minuto (dentro de la fase) donde inyectar un pico de caída
    fall_spike_g: float = 3.5


def render(phases: list[Phase], start: datetime, seed: int = 0, glucose_start: float = 95.0) -> list[list[SignalReading]]:
    """Convierte una lista de fases en lecturas minuto a minuto de las seis señales."""
    rng = random.Random(seed)
    ticks: list[list[SignalReading]] = []
    t = start
    glucose = glucose_start

    for phase in phases:
        for minute in range(phase.duration_min):
            glucose += phase.glucose_slope + rng.uniform(-0.4, 0.4)
            hr = phase.heart_rate + rng.uniform(-2.5, 2.5)
            skin = phase.skin_temp + rng.uniform(-0.15, 0.15)
            ambient = phase.ambient_temp + rng.uniform(-0.3, 0.3)
            humidity = phase.humidity + rng.uniform(-1.5, 1.5)
            movement = max(0.0, phase.movement + rng.uniform(-0.03, 0.03))
            if phase.movement_spike_at == minute:
                movement = phase.fall_spike_g

            readings = [
                SignalReading(t, SignalType.GLUCOSE, round(glucose, 1), source="sim.cgm", context=phase.context),
                SignalReading(t, SignalType.HEART_RATE, round(hr, 1), source="sim.watch", context=phase.context),
                SignalReading(t, SignalType.SKIN_TEMP, round(skin, 2), source="sim.watch", context=phase.context),
                SignalReading(t, SignalType.AMBIENT_TEMP, round(ambient, 1), source="sim.ble_env", context=phase.context),
                SignalReading(t, SignalType.HUMIDITY, round(humidity, 1), source="sim.ble_env", context=phase.context),
                SignalReading(t, SignalType.MOVEMENT, round(movement, 2), source="sim.watch", context=phase.context),
            ]
            ticks.append(readings)
            t += timedelta(minutes=TICK_MINUTES)
    return ticks


def _resting(minutes: int, **kw) -> Phase:
    return Phase(duration_min=minutes, context=ActivityContext.RESTING, **kw)


# ---- 0. Día normal, sin anomalías — control para probar que no hay falsos positivos ----
def normal_day() -> list[Phase]:
    return [
        _resting(180),
        Phase(60, context=ActivityContext.WALKING, heart_rate=85, movement=0.6),
        _resting(120),
    ]


# ---- 1. Glucosa descendiendo rápidamente ----
def glucose_rapid_drop() -> list[Phase]:
    return [
        _resting(60),
        _resting(20, glucose_slope=-3.0),
        _resting(20),
    ]


# ---- 2. Glucosa descendiendo + FC aumentando ----
def glucose_drop_hr_up() -> list[Phase]:
    return [
        _resting(60),
        _resting(20, glucose_slope=-2.5, heart_rate=95),
        _resting(20, heart_rate=95),
    ]


# ---- 3. FC inusualmente alta en reposo ----
def hr_high_at_rest() -> list[Phase]:
    return [
        _resting(90),
        _resting(20, heart_rate=115),
    ]


# ---- 4. FC inusualmente baja respecto al patrón personal ----
def hr_low_vs_baseline() -> list[Phase]:
    return [
        _resting(90),
        _resting(20, heart_rate=38),
    ]


# ---- 5. Carga térmica elevada ----
def thermal_load_high() -> list[Phase]:
    return [
        _resting(60),
        _resting(20, skin_temp=35.2, ambient_temp=33, humidity=75),
    ]


# ---- 6. Recuperación inusual después de ejercicio ----
def abnormal_recovery() -> list[Phase]:
    return [
        _resting(60),
        Phase(30, context=ActivityContext.EXERCISING, heart_rate=140, movement=1.2),
        _resting(10, heart_rate=118),
    ]


# ---- 7. Caída + inmovilidad ----
def fall_immobility() -> list[Phase]:
    return [
        Phase(60, context=ActivityContext.WALKING, heart_rate=80, movement=0.6),
        Phase(1, context=ActivityContext.WALKING, heart_rate=82, movement=0.6, movement_spike_at=0),
        _resting(10, heart_rate=78, movement=0.02),
    ]


# ---- 8. Anomalía multisensor no clasificada ----
def multisensor_anomaly() -> list[Phase]:
    return [
        Phase(60, context=ActivityContext.AFTER_MEAL, heart_rate=72, skin_temp=33.2,
              ambient_temp=23, humidity=48, movement=0.1),
        Phase(20, context=ActivityContext.AFTER_MEAL, heart_rate=92, skin_temp=34.3,
              ambient_temp=26, humidity=58, movement=0.1),
    ]


SCENARIOS = {
    "normal_day": normal_day,
    "glucose_rapid_drop": glucose_rapid_drop,
    "glucose_drop_hr_up": glucose_drop_hr_up,
    "hr_high_at_rest": hr_high_at_rest,
    "hr_low_vs_baseline": hr_low_vs_baseline,
    "thermal_load_high": thermal_load_high,
    "abnormal_recovery": abnormal_recovery,
    "fall_immobility": fall_immobility,
    "multisensor_anomaly": multisensor_anomaly,
}
