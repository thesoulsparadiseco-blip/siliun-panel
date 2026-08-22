"""detractor_filter — capa 5.1 del spec: detecta señal limitante ("detractor")."""
from typing import List

DETRACTOR_KEYWORDS: List[str] = [
    "miedo", "duda", "escasez", "bloqueo", "no puedo", "estrés", "estres",
    "caos", "ansiedad", "culpa", "vergüenza", "verguenza", "no sirvo",
    "fracaso", "rechazo", "abandono", "no hay",
]


def matches(text: str) -> List[str]:
    lowered = text.lower()
    return [kw for kw in DETRACTOR_KEYWORDS if kw in lowered]


def score(text: str) -> int:
    return len(matches(text))
