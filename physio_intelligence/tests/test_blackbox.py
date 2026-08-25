"""Tests de la caja negra fisiológica (sección 11) y el feedback humano (sección 12)."""
from datetime import datetime, timedelta

from physio_sim.blackbox import BlackBox
from physio_sim.events import EventType, make_event
from physio_sim.models import ActivityContext, SignalReading, SignalType

START = datetime(2026, 1, 1, 7, 0, 0)


def _reading(minute: int) -> SignalReading:
    return SignalReading(
        timestamp=START + timedelta(minutes=minute),
        signal_type=SignalType.HEART_RATE,
        value=70,
        source="test",
        context=ActivityContext.RESTING,
    )


def test_episode_stays_open_until_60_minutes_of_after_readings():
    blackbox = BlackBox()
    for minute in range(30):
        blackbox.record([_reading(minute)])

    event = make_event(EventType.HR_HIGH_AT_REST, START + timedelta(minutes=30), "msg", [])
    episode = blackbox.open_episode(event)
    assert len(episode.before) == 30

    for minute in range(31, 89):  # 58 minutos después del evento — todavía no cierra
        blackbox.record([_reading(minute)])
    assert episode not in blackbox.episodes

    blackbox.record([_reading(90)])  # 60 min después del evento — ahora sí
    assert episode in blackbox.episodes


def test_flush_closes_episodes_left_open_at_the_end_of_the_simulation():
    blackbox = BlackBox()
    event = make_event(EventType.FALL_IMMOBILITY, START, "msg", [])
    episode = blackbox.open_episode(event)
    blackbox.record([_reading(1)])  # solo 1 min de ventana 'after', muy lejos de los 60

    assert episode not in blackbox.episodes
    blackbox.flush()
    assert episode in blackbox.episodes


def test_add_feedback_attaches_the_human_response_to_its_own_episode():
    blackbox = BlackBox()
    event_a = make_event(EventType.HR_HIGH_AT_REST, START, "msg a", [])
    event_b = make_event(EventType.THERMAL_LOAD_HIGH, START + timedelta(minutes=1), "msg b", [])
    episode_a = blackbox.open_episode(event_a)
    episode_b = blackbox.open_episode(event_b)

    blackbox.add_feedback(episode_a, "Palpitaciones")

    assert episode_a.feedback == "Palpitaciones"
    assert episode_b.feedback is None  # el feedback no se filtra a otros episodios
