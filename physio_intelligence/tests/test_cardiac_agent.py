"""Tests del Cardiac Agent en aislamiento (sección 6, 'Cardiac Agent').

A diferencia de tests/test_fusion_events.py (que prueba el pipeline
completo escenario -> baseline -> Fusion Engine), estos ejercitan
`CardiacAgent` directamente, sin pasar por el Fusion Engine ni por los
escenarios sintéticos.
"""
from datetime import datetime, timedelta

from physio_sim.agents import CardiacAgent
from physio_sim.baseline import PersonalBaseline
from physio_sim.events import EventType
from physio_sim.models import ActivityContext, SignalReading, SignalType

START = datetime(2026, 1, 1, 7, 0, 0)


def _hr(value: float, minute: int, context=ActivityContext.RESTING) -> SignalReading:
    return SignalReading(
        timestamp=START + timedelta(minutes=minute),
        signal_type=SignalType.HEART_RATE,
        value=value,
        source="test",
        context=context,
    )


def _hrv(value: float, minute: int, context=ActivityContext.RESTING) -> SignalReading:
    return SignalReading(
        timestamp=START + timedelta(minutes=minute),
        signal_type=SignalType.HRV,
        value=value,
        source="test",
        context=context,
    )


def test_assess_returns_none_zscore_before_baseline_warmup():
    baseline = PersonalBaseline()
    agent = CardiacAgent(baseline)
    assessment = agent.assess({SignalType.HEART_RATE: _hr(65, 0)})
    assert assessment.heart_rate_zscore is None


def test_assess_scores_heart_rate_and_hrv_independently():
    baseline = PersonalBaseline()
    agent = CardiacAgent(baseline)
    for i in range(30):
        baseline.observe(_hr(65 + (i % 3) - 1, i))
        baseline.observe(_hrv(45 + (i % 3) - 1, i))

    assessment = agent.assess({
        SignalType.HEART_RATE: _hr(110, 30),
        SignalType.HRV: _hrv(45, 30),
    })
    assert assessment.heart_rate_zscore > 5
    assert abs(assessment.hrv_zscore) < 1  # HRV sigue en su patrón, no debería marcar nada


def test_hr_high_at_rest_fires_after_persistence_window():
    baseline = PersonalBaseline()
    agent = CardiacAgent(baseline)
    for i in range(30):
        r = _hr(65 + (i % 3) - 1, i)
        baseline.observe(r)

    events = []
    for i in range(30, 36):
        reading = _hr(115, i)
        by_type = {SignalType.HEART_RATE: reading}
        agent.assess(by_type)
        events += agent.check_events(by_type, reading.timestamp)
        baseline.observe(reading)

    fired = {e.event_type for e in events}
    assert EventType.HR_HIGH_AT_REST in fired


def test_hr_high_while_walking_does_not_fire_the_at_rest_event():
    """La regla es específicamente 'alta en reposo' — no debe dispararse caminando."""
    baseline = PersonalBaseline()
    agent = CardiacAgent(baseline)
    for i in range(30):
        baseline.observe(_hr(65 + (i % 3) - 1, i, context=ActivityContext.WALKING))

    events = []
    for i in range(30, 36):
        reading = _hr(115, i, context=ActivityContext.WALKING)
        by_type = {SignalType.HEART_RATE: reading}
        agent.assess(by_type)
        events += agent.check_events(by_type, reading.timestamp)
        baseline.observe(reading)

    assert events == []


def test_recovery_tracks_exercise_to_resting_transition():
    baseline = PersonalBaseline()
    agent = CardiacAgent(baseline)
    events = []

    def _tick(value: float, minute: int, context: ActivityContext) -> None:
        reading = _hr(value, minute, context=context)
        by_type = {SignalType.HEART_RATE: reading}
        agent.assess(by_type)
        events.extend(agent.check_events(by_type, reading.timestamp))
        baseline.observe(reading)

    # baseline en reposo normal
    for i in range(30):
        _tick(65 + (i % 3) - 1, i, ActivityContext.RESTING)
    # sesión de ejercicio — el agente registra la transición él mismo, vía check_events
    for i in range(30, 45):
        _tick(140, i, ActivityContext.EXERCISING)
    # vuelve a reposo pero sin recuperar la FC
    for i in range(45, 51):
        _tick(118, i, ActivityContext.RESTING)

    fired = {e.event_type for e in events}
    assert EventType.ABNORMAL_RECOVERY in fired
