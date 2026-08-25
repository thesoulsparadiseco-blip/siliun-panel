from datetime import datetime

import pytest

from physio_sim.events import EventType
from physio_sim.scenarios import SCENARIOS
from physio_sim.simulator import run_scenario

START = datetime(2026, 1, 1, 7, 0, 0)

EXPECTED_EVENT = {
    "glucose_rapid_drop": EventType.GLUCOSE_RAPID_DROP,
    "glucose_drop_hr_up": EventType.GLUCOSE_DROP_HR_UP,
    "hr_high_at_rest": EventType.HR_HIGH_AT_REST,
    "hr_low_vs_baseline": EventType.HR_LOW_VS_BASELINE,
    "thermal_load_high": EventType.THERMAL_LOAD_HIGH,
    "abnormal_recovery": EventType.ABNORMAL_RECOVERY,
    "fall_immobility": EventType.FALL_IMMOBILITY,
    "multisensor_anomaly": EventType.MULTISENSOR_ANOMALY,
}


@pytest.mark.parametrize("scenario_name,expected_event", EXPECTED_EVENT.items())
def test_scenario_triggers_its_target_event(scenario_name, expected_event):
    phases = SCENARIOS[scenario_name]()
    result = run_scenario(phases, START)
    fired = {e.event_type for e in result.events}
    assert expected_event in fired, f"{scenario_name}: esperaba {expected_event}, obtuve {fired}"


def test_normal_day_produces_no_false_positives():
    phases = SCENARIOS["normal_day"]()
    result = run_scenario(phases, START)
    assert result.events == []


def test_blackbox_opens_an_episode_with_a_before_window_for_every_event():
    phases = SCENARIOS["hr_high_at_rest"]()
    result = run_scenario(phases, START)
    assert result.episodes
    first_episode = result.episodes[0]
    assert len(first_episode.before) > 0
    assert first_episode.event.event_type == EventType.HR_HIGH_AT_REST


def test_events_carry_a_human_readable_label_and_message():
    phases = SCENARIOS["fall_immobility"]()
    result = run_scenario(phases, START)
    assert result.events
    event = result.events[0]
    assert event.label
    assert event.message
    assert event.triggering_readings
