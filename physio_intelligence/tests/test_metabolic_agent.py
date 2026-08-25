"""Tests del Metabolic Agent en aislamiento (sección 6, 'Metabolic Agent').

A diferencia de tests/test_fusion_events.py (que prueba el pipeline
completo escenario -> baseline -> Fusion Engine), estos ejercitan
`MetabolicAgent` directamente, sin Fusion Engine ni escenarios sintéticos.
"""
from datetime import datetime, timedelta

from physio_sim.agents import MetabolicAgent
from physio_sim.baseline import PersonalBaseline
from physio_sim.events import EventType
from physio_sim.models import ActivityContext, SignalReading, SignalType

START = datetime(2026, 1, 1, 7, 0, 0)


def _glucose(value: float, minute: int) -> SignalReading:
    return SignalReading(
        timestamp=START + timedelta(minutes=minute),
        signal_type=SignalType.GLUCOSE,
        value=value,
        source="test",
        context=ActivityContext.RESTING,
    )


def _tick(agent: MetabolicAgent, value: float, minute: int) -> list:
    reading = _glucose(value, minute)
    by_type = {SignalType.GLUCOSE: reading}
    agent.observe(by_type)
    assessment = agent.assess(by_type)
    return agent.check_events(assessment, reading.timestamp)


def test_no_slope_without_at_least_two_readings():
    agent = MetabolicAgent(PersonalBaseline())
    by_type = {SignalType.GLUCOSE: _glucose(95, 0)}
    agent.observe(by_type)
    assessment = agent.assess(by_type)
    assert assessment.glucose_slope is None
    assert assessment.dropping_rapidly is False


def test_flat_glucose_never_fires_rapid_drop():
    agent = MetabolicAgent(PersonalBaseline())
    events = []
    for minute in range(20):
        events += _tick(agent, 95 + (minute % 2), minute)
    assert events == []


def test_sustained_drop_fires_after_persistence_window():
    agent = MetabolicAgent(PersonalBaseline())
    events = []
    glucose = 95.0
    for minute in range(20):
        glucose -= 2.5  # mg/dL/min, por encima del umbral de -2.0
        events += _tick(agent, glucose, minute)

    fired = {e.event_type for e in events}
    assert EventType.GLUCOSE_RAPID_DROP in fired


def test_reset_rapid_drop_persistence_suppresses_a_pending_event():
    """El Fusion Engine llama a esto cuando el combo glucosa+FC ya explica la caída."""
    agent = MetabolicAgent(PersonalBaseline())
    glucose = 95.0
    for minute in range(2):
        glucose -= 2.5
        _tick(agent, glucose, minute)  # dos ticks acumulados de persistencia, todavía sin disparar

    agent.reset_rapid_drop_persistence()

    glucose -= 2.5
    events = _tick(agent, glucose, 2)  # un solo tick tras el reset: no alcanza el umbral de persistencia
    assert events == []


def test_missing_glucose_resets_persistence():
    agent = MetabolicAgent(PersonalBaseline())
    glucose = 95.0
    for minute in range(2):
        glucose -= 2.5
        _tick(agent, glucose, minute)

    # un tick sin lectura de glucosa (sensor desconectado) reinicia la persistencia
    events = agent.check_events(agent.assess({}), START + timedelta(minutes=2))
    assert events == []

    glucose -= 2.5
    events = _tick(agent, glucose, 3)
    assert events == []  # la persistencia se reinició; un solo tick no alcanza el umbral
