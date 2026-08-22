"""
elemental_engine — capa 5.1 del spec (Tierra/Fuego/Agua/Aire/Éter).

Clasificador léxico determinista (sin modelo, sin red): cuenta
coincidencias de palabras clave por elemento —en el idioma detectado o
indicado— y devuelve el elemento dominante como clave canónica en
inglés (earth/fire/water/air/ether), que cada consumidor traduce al
mostrarlo (ver i18n.get(locale)["element_names"]). El punto de
extensión real es reemplazar `score()` por un embedding local (ver
memory/vector_db.py) cuando haya un modelo on-device disponible.
"""
import re
from dataclasses import dataclass
from typing import Dict

from ..i18n import DEFAULT_LOCALE, get as get_locale


@dataclass(frozen=True)
class ElementalReading:
    element: str  # clave canónica: earth/fire/water/air/ether
    scores: Dict[str, int]


def score(text: str, locale: str = DEFAULT_LOCALE) -> Dict[str, int]:
    lowered = text.lower()
    elements = get_locale(locale)["elements"]
    # \b evita falsos positivos por subcadena entre palabras clave parecidas.
    return {
        el: sum(len(re.findall(rf"\b{re.escape(kw)}\b", lowered)) for kw in kws)
        for el, kws in elements.items()
    }


def classify(text: str, locale: str = DEFAULT_LOCALE) -> ElementalReading:
    data = get_locale(locale)
    scores = score(text, locale)
    best = max(scores.items(), key=lambda kv: kv[1])
    element = best[0] if best[1] > 0 else data["default_element"]
    return ElementalReading(element=element, scores=scores)
