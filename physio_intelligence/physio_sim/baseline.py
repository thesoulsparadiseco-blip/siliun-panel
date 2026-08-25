"""Personal Baseline Model (documento maestro, sección 10).

El sistema no tiene una sola "normalidad": aprende media y desviación
estándar por separado para cada combinación (señal, contexto) — normal
durmiendo, normal caminando, normal después de comer, etc. — usando el
algoritmo online de Welford (streaming, sin guardar todo el historial).
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

from .models import ActivityContext, SignalReading, SignalType

MIN_SAMPLES_FOR_BASELINE = 20


@dataclass
class _Welford:
    n: int = 0
    mean: float = 0.0
    m2: float = 0.0

    def update(self, x: float) -> None:
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        delta2 = x - self.mean
        self.m2 += delta * delta2

    @property
    def variance(self) -> float:
        return self.m2 / self.n if self.n > 1 else 0.0

    @property
    def stdev(self) -> float:
        return math.sqrt(self.variance)


class PersonalBaseline:
    """Una media/desviación en streaming por cada (tipo de señal, contexto)."""

    def __init__(self) -> None:
        self._stats: dict[tuple[SignalType, ActivityContext], _Welford] = defaultdict(_Welford)

    def observe(self, reading: SignalReading) -> None:
        """Aprende de una lectura fiable. Las no fiables nunca contaminan el baseline."""
        if not reading.reliable:
            return
        key = (reading.signal_type, reading.context)
        self._stats[key].update(reading.value)

    def has_baseline(self, signal_type: SignalType, context: ActivityContext) -> bool:
        stats = self._stats.get((signal_type, context))
        return stats is not None and stats.n >= MIN_SAMPLES_FOR_BASELINE

    def mean(self, signal_type: SignalType, context: ActivityContext) -> float | None:
        stats = self._stats.get((signal_type, context))
        return stats.mean if stats and stats.n else None

    def zscore(self, reading: SignalReading) -> float | None:
        """Cuántas desviaciones estándar *personales* se aleja esta lectura de su propio patrón.

        Devuelve None mientras no haya suficientes muestras (evita "desviaciones"
        falsas antes de que exista un baseline real para ese contexto).
        """
        key = (reading.signal_type, reading.context)
        stats = self._stats.get(key)
        if stats is None or stats.n < MIN_SAMPLES_FOR_BASELINE:
            return None
        stdev = stats.stdev
        if stdev == 0:
            return 0.0
        return (reading.value - stats.mean) / stdev
