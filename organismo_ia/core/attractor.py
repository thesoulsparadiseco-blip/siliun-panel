"""attractor_filter — capa 5.1 del spec: detecta señal expansiva ("atractor")."""
from typing import List

ATRACTOR_KEYWORDS: List[str] = [
    "expansión", "expansion", "gratitud", "abundancia", "amor", "crecimiento",
    "oportunidad", "confianza", "claridad", "alegría", "alegria", "sí puedo",
    "si puedo", "gracias", "logro", "avance", "apertura",
]


def matches(text: str) -> List[str]:
    lowered = text.lower()
    return [kw for kw in ATRACTOR_KEYWORDS if kw in lowered]


def score(text: str) -> int:
    return len(matches(text))
