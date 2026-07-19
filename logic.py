"""
Resonance scoring rules (section 5 of the spec).

resonanceScore = 0.5*clarity + 0.3*rhythm + (silence ? 20 : 0) + (intention ? 10 : 0)
user_state_ready = resonanceScore >= threshold
"""
import os

DEFAULT_THRESHOLD = 70.0


def get_threshold() -> float:
    return float(os.getenv("RESONANCE_THRESHOLD", DEFAULT_THRESHOLD))


def compute_resonance(clarity: float, rhythm: float, silence: bool, intention: int) -> float:
    score = (
        0.5 * clarity
        + 0.3 * rhythm
        + (20 if silence else 0)
        + (10 if bool(intention) else 0)
    )
    return round(score, 2)


def is_ready(score: float, threshold: float = None) -> bool:
    t = threshold if threshold is not None else get_threshold()
    return score >= t
