"""Estados del sistema (sección 9) y los ocho primeros eventos (sección 7)."""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime

from .models import SignalReading


class SystemState(str, enum.Enum):
    HABITUAL = "HABITUAL"      # sin cambios relevantes
    CAMBIO = "CAMBIO"          # algo se aleja del patrón
    COMPROBAR = "COMPROBAR"    # la desviación persiste o coinciden varias señales
    ALERTA = "ALERTA"          # evento prioritario confirmado


class EventType(str, enum.Enum):
    GLUCOSE_RAPID_DROP = "glucose_rapid_drop"
    GLUCOSE_DROP_HR_UP = "glucose_drop_hr_up"
    HR_HIGH_AT_REST = "hr_high_at_rest"
    HR_LOW_VS_BASELINE = "hr_low_vs_baseline"
    THERMAL_LOAD_HIGH = "thermal_load_high"
    ABNORMAL_RECOVERY = "abnormal_recovery"
    FALL_IMMOBILITY = "fall_immobility"
    MULTISENSOR_ANOMALY = "multisensor_anomaly"


EVENT_LABELS: dict[EventType, str] = {
    EventType.GLUCOSE_RAPID_DROP: "Glucosa descendiendo rápidamente",
    EventType.GLUCOSE_DROP_HR_UP: "Glucosa descendiendo + FC aumentando",
    EventType.HR_HIGH_AT_REST: "FC inusualmente alta en reposo",
    EventType.HR_LOW_VS_BASELINE: "FC inusualmente baja respecto al patrón personal",
    EventType.THERMAL_LOAD_HIGH: "Carga térmica elevada",
    EventType.ABNORMAL_RECOVERY: "Recuperación inusual después de ejercicio",
    EventType.FALL_IMMOBILITY: "Caída + inmovilidad",
    EventType.MULTISENSOR_ANOMALY: "Anomalía multisensor no clasificada",
}

EVENT_DEFAULT_STATE: dict[EventType, SystemState] = {
    EventType.GLUCOSE_RAPID_DROP: SystemState.ALERTA,
    EventType.GLUCOSE_DROP_HR_UP: SystemState.ALERTA,
    EventType.HR_HIGH_AT_REST: SystemState.COMPROBAR,
    EventType.HR_LOW_VS_BASELINE: SystemState.COMPROBAR,
    EventType.THERMAL_LOAD_HIGH: SystemState.COMPROBAR,
    EventType.ABNORMAL_RECOVERY: SystemState.CAMBIO,
    EventType.FALL_IMMOBILITY: SystemState.ALERTA,
    EventType.MULTISENSOR_ANOMALY: SystemState.CAMBIO,
}


@dataclass
class Event:
    event_type: EventType
    timestamp: datetime
    state: SystemState
    message: str
    triggering_readings: list[SignalReading] = field(default_factory=list)

    @property
    def label(self) -> str:
        return EVENT_LABELS[self.event_type]
