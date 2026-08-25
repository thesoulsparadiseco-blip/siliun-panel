"""Tests del Action Engine (sección 3 y paso 9 de la sección 30, 'primera alerta en reloj')."""
from datetime import datetime

import pytest

from physio_sim.action_engine import ActionEngine, WatchChannel, feedback_options_for
from physio_sim.events import EventType, SystemState, make_event
from physio_sim.scenarios import SCENARIOS
from physio_sim.simulator import run_scenario

TIMESTAMP = datetime(2026, 1, 1, 8, 0, 0)
START = datetime(2026, 1, 1, 7, 0, 0)


def _event(event_type: EventType):
    return make_event(event_type, TIMESTAMP, "mensaje de prueba", [])


@pytest.mark.parametrize("event_type", list(EventType))
def test_every_event_type_has_feedback_options(event_type):
    options = feedback_options_for(event_type)
    assert options[0] == "Estoy bien"
    assert options[-1] == "Otro"
    assert len(options) == len(set(options))  # sin duplicados


def test_alert_icon_matches_the_event_state():
    engine = ActionEngine()
    alert = engine.build_alert(_event(EventType.FALL_IMMOBILITY))
    assert alert.event.state == SystemState.ALERTA
    assert alert.icon == "🔴"


def test_alert_never_upgrades_the_message_to_a_diagnosis():
    """El mensaje que llega al reloj es el que redactó el propio evento — el
    Action Engine no debe reescribirlo ni añadirle nada (sección 17: medición
    + inferencia, nunca diagnóstico)."""
    engine = ActionEngine()
    event = _event(EventType.HR_HIGH_AT_REST)
    alert = engine.build_alert(event)
    assert alert.message == event.message
    assert alert.title == event.label


def test_watch_channel_collects_alerts_in_order():
    engine = ActionEngine()
    channel = WatchChannel()
    for event_type in (EventType.HR_HIGH_AT_REST, EventType.THERMAL_LOAD_HIGH):
        channel.send(engine.build_alert(_event(event_type)))

    assert len(channel.delivered) == 2
    assert channel.delivered[0].event.event_type == EventType.HR_HIGH_AT_REST
    assert channel.delivered[1].event.event_type == EventType.THERMAL_LOAD_HIGH


def test_every_detected_event_reaches_the_watch_in_a_full_run():
    result = run_scenario(SCENARIOS["hr_high_at_rest"](), START)
    assert result.events  # el escenario efectivamente dispara algo
    assert len(result.watch_alerts) == len(result.events)
    assert [a.event for a in result.watch_alerts] == result.events


def test_normal_day_delivers_no_watch_alerts():
    result = run_scenario(SCENARIOS["normal_day"](), START)
    assert result.watch_alerts == []
