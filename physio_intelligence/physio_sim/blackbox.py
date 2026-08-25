"""Caja negra fisiológica (documento maestro, sección 11).

Ante cada evento guarda automáticamente 60 minutos antes, el evento, y 60
minutos después — con todas las señales disponibles — para poder
reconstruir lo ocurrido y, más adelante, detectar precursores.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import timedelta

from .events import Event
from .models import SignalReading

WINDOW = timedelta(minutes=60)


@dataclass
class Episode:
    event: Event
    before: list[SignalReading] = field(default_factory=list)
    after: list[SignalReading] = field(default_factory=list)
    feedback: str | None = None  # sección 12: respuesta humana post-evento

    @property
    def closed(self) -> bool:
        if not self.after:
            return False
        return (self.after[-1].timestamp - self.event.timestamp) >= WINDOW


class BlackBox:
    """Buffer continuo de lecturas; recorta un episodio ±60 min por cada evento."""

    def __init__(self) -> None:
        self._recent: deque[SignalReading] = deque()
        self._open_episodes: list[Episode] = []
        self.episodes: list[Episode] = []

    def record(self, readings: list[SignalReading]) -> None:
        if not readings:
            return
        self._recent.extend(readings)
        cutoff = readings[-1].timestamp - WINDOW
        while self._recent and self._recent[0].timestamp < cutoff:
            self._recent.popleft()

        for episode in list(self._open_episodes):
            episode.after.extend(readings)
            if episode.closed:
                self._open_episodes.remove(episode)
                self.episodes.append(episode)

    def open_episode(self, event: Event) -> Episode:
        before = [r for r in self._recent if r.timestamp <= event.timestamp]
        episode = Episode(event=event, before=before)
        self._open_episodes.append(episode)
        return episode

    def flush(self) -> None:
        """Cierra episodios que sigan abiertos al terminar la simulación (ventana 'after' parcial)."""
        self.episodes.extend(self._open_episodes)
        self._open_episodes.clear()

    def add_feedback(self, episode: Episode, feedback: str) -> None:
        episode.feedback = feedback
