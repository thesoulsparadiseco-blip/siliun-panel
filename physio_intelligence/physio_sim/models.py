"""Modelo de datos común para cada señal (documento maestro, sección 19).

Cada lectura guarda como mínimo: timestamp, tipo, valor, unidad, fuente,
tipo de medición y contexto — así nunca se confunde una medición directa
con una inferencia derivada.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime


class SignalType(str, enum.Enum):
    GLUCOSE = "glucose"
    HEART_RATE = "heart_rate"
    IBI = "ibi"    # intervalo entre latidos (Cardiac Agent, sección 6)
    HRV = "hrv"    # variabilidad de FC, rmssd (Cardiac Agent, sección 6)
    SKIN_TEMP = "skin_temp"
    MOVEMENT = "movement"
    AMBIENT_TEMP = "ambient_temp"
    HUMIDITY = "humidity"


class MeasurementType(str, enum.Enum):
    DIRECT = "DIRECT"
    DERIVED = "DERIVED"
    PREDICTED = "PREDICTED"
    USER_REPORTED = "USER_REPORTED"
    IMPORTED = "IMPORTED"


class ActivityContext(str, enum.Enum):
    """No existe una sola normalidad — cada contexto tiene su propio baseline (sección 10)."""

    SLEEPING = "sleeping"
    RESTING = "resting"
    WALKING = "walking"
    EXERCISING = "exercising"
    AFTER_MEAL = "after_meal"
    DEFAULT = "default"


UNITS: dict[SignalType, str] = {
    SignalType.GLUCOSE: "mg/dL",
    SignalType.HEART_RATE: "bpm",
    SignalType.IBI: "ms",
    SignalType.HRV: "ms",
    SignalType.SKIN_TEMP: "°C",
    SignalType.MOVEMENT: "g",
    SignalType.AMBIENT_TEMP: "°C",
    SignalType.HUMIDITY: "%",
}


@dataclass
class SignalReading:
    timestamp: datetime
    signal_type: SignalType
    value: float
    source: str
    measurement_type: MeasurementType = MeasurementType.DIRECT
    quality: float = 1.0  # 0..1 — fiabilidad de la lectura (sección 8, "¿ES FIABLE?")
    context: ActivityContext = ActivityContext.DEFAULT
    unit: str = ""

    def __post_init__(self) -> None:
        if not self.unit:
            self.unit = UNITS[self.signal_type]

    @property
    def reliable(self) -> bool:
        return self.quality >= 0.5
