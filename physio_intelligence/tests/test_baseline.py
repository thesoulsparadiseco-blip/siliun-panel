from datetime import datetime, timedelta

import pytest

from physio_sim.baseline import PersonalBaseline
from physio_sim.models import ActivityContext, SignalReading, SignalType


def _reading(value: float, minute: int, quality: float = 1.0) -> SignalReading:
    return SignalReading(
        timestamp=datetime(2026, 1, 1, 7, 0) + timedelta(minutes=minute),
        signal_type=SignalType.HEART_RATE,
        value=value,
        source="test",
        context=ActivityContext.RESTING,
        quality=quality,
    )


def test_baseline_needs_minimum_samples_before_scoring():
    baseline = PersonalBaseline()
    for i in range(5):
        baseline.observe(_reading(65, i))
    assert baseline.zscore(_reading(65, 5)) is None
    assert not baseline.has_baseline(SignalType.HEART_RATE, ActivityContext.RESTING)


def test_baseline_detects_deviation_after_warmup():
    baseline = PersonalBaseline()
    # ruido pequeño realista, no valores idénticos: con stdev == 0 el z-score
    # siempre da 0 (ver test_zero_variance_baseline_does_not_divide_by_zero),
    # lo que no ejercitaría la división real que este test quiere probar.
    for i in range(30):
        value = 65 + (i % 3) - 1  # oscila entre 64 y 66
        baseline.observe(_reading(value, i))
    assert baseline.has_baseline(SignalType.HEART_RATE, ActivityContext.RESTING)
    assert baseline.zscore(_reading(65, 30)) == pytest.approx(0.0, abs=0.5)
    assert baseline.zscore(_reading(120, 31)) > 5


def test_zero_variance_baseline_does_not_divide_by_zero():
    baseline = PersonalBaseline()
    for i in range(30):
        baseline.observe(_reading(65, i))  # siempre el mismo valor -> stdev == 0
    assert baseline.zscore(_reading(65, 30)) == 0.0
    assert baseline.zscore(_reading(120, 31)) == 0.0


def test_unreliable_readings_never_contaminate_the_baseline():
    baseline = PersonalBaseline()
    for i in range(30):
        baseline.observe(_reading(65, i, quality=0.1))
    assert not baseline.has_baseline(SignalType.HEART_RATE, ActivityContext.RESTING)


def test_baselines_are_kept_separate_per_context():
    baseline = PersonalBaseline()
    for i in range(30):
        baseline.observe(_reading(65, i))  # RESTING
        walking = _reading(95, i)
        walking.context = ActivityContext.WALKING
        baseline.observe(walking)

    assert baseline.mean(SignalType.HEART_RATE, ActivityContext.RESTING) == 65
    assert baseline.mean(SignalType.HEART_RATE, ActivityContext.WALKING) == 95
