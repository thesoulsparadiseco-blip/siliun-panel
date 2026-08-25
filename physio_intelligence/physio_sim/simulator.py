"""Orquestación de punta a punta: escenario -> Personal Baseline -> Fusion Engine ->
Action Engine -> Black Box.

Este es el núcleo ejecutable del 'Simulador Fisiológico' (sección 23): sin
sensores reales, pero con el mismo pipeline que correrá el producto real
sobre datos en vivo — incluyendo la entrega al reloj (sección 3, paso 9 de
la sección 30).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .action_engine import ActionEngine, WatchAlert, WatchChannel
from .baseline import PersonalBaseline
from .blackbox import BlackBox, Episode
from .events import Event
from .fusion import FusionEngine
from .models import SignalReading
from .scenarios import Phase, render


@dataclass
class TickResult:
    timestamp: datetime
    readings: list[SignalReading]
    events: list[Event] = field(default_factory=list)


@dataclass
class SimulationResult:
    ticks: list[TickResult]
    events: list[Event]
    episodes: list[Episode]
    watch_alerts: list[WatchAlert]

    def summary(self) -> str:
        lines = [f"Ticks simulados: {len(self.ticks)}", f"Eventos detectados: {len(self.events)}"]
        for e in self.events:
            lines.append(f"  [{e.timestamp:%H:%M}] {e.state.value:<10} {e.label} — {e.message}")
        if self.watch_alerts:
            lines.append(f"Alertas entregadas al reloj: {len(self.watch_alerts)}")
            first = self.watch_alerts[0]
            options = ", ".join(first.feedback_options)
            lines.append(f"  ej.: {first.icon} \"{first.title}\" — feedback: [{options}]")
        return "\n".join(lines)


def run_scenario(phases: list[Phase], start: datetime, seed: int = 0) -> SimulationResult:
    baseline = PersonalBaseline()
    engine = FusionEngine(baseline)
    blackbox = BlackBox()
    action_engine = ActionEngine()
    watch = WatchChannel()

    ticks: list[TickResult] = []
    all_events: list[Event] = []

    for readings in render(phases, start, seed):
        events = engine.ingest(readings)
        blackbox.record(readings)
        for event in events:
            blackbox.open_episode(event)
            watch.send(action_engine.build_alert(event))
        ticks.append(TickResult(timestamp=readings[0].timestamp, readings=readings, events=events))
        all_events.extend(events)

    blackbox.flush()
    return SimulationResult(
        ticks=ticks, events=all_events, episodes=blackbox.episodes, watch_alerts=watch.delivered
    )
