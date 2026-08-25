"""Historial deslizante de una señal: lo usan el Fusion Engine y cualquier
agente que necesite calcular una pendiente o mirar hacia atrás en el tiempo
(Cardiac Agent no lo necesita — sus reglas solo miran el tick actual y la
media del baseline; Metabolic Agent sí, para la pendiente de glucosa).
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import timedelta

from .models import SignalReading

DEFAULT_WINDOW = timedelta(minutes=30)


@dataclass
class SignalHistory:
    window: timedelta = DEFAULT_WINDOW
    readings: deque[SignalReading] = field(default_factory=deque)

    def add(self, reading: SignalReading) -> None:
        self.readings.append(reading)
        cutoff = reading.timestamp - self.window
        while self.readings and self.readings[0].timestamp < cutoff:
            self.readings.popleft()

    def slope_per_minute(self, minutes: float) -> float | None:
        """Tasa de cambio promedio en los últimos `minutes`, en unidades/minuto."""
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
