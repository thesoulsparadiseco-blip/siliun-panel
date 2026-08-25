"""Physio Intelligence Platform — Simulador Fisiológico (V1, MVP en 7 días).

Motor de referencia sin sensores reales: genera señales sintéticas y las
hace pasar por el mismo pipeline que usará el producto real (Personal
Baseline -> Fusion Engine -> Black Box) para demostrar que baseline,
cambio, persistencia, fusión, evento y alerta funcionan de punta a punta.
"""
from .events import Event, EventType, SystemState
from .models import ActivityContext, MeasurementType, SignalReading, SignalType
from .simulator import SimulationResult, run_scenario

__all__ = [
    "Event",
    "EventType",
    "SystemState",
    "ActivityContext",
    "MeasurementType",
    "SignalReading",
    "SignalType",
    "SimulationResult",
    "run_scenario",
]
