"""detractor_filter — capa 5.1 del spec: detecta señal limitante ("detractor"), por idioma."""
import re
from typing import List

from ..i18n import DEFAULT_LOCALE, get as get_locale


def matches(text: str, locale: str = DEFAULT_LOCALE) -> List[str]:
    lowered = text.lower()
    keywords = get_locale(locale)["detractor_keywords"]
    # \b evita falsos positivos por subcadena entre palabras clave parecidas.
    return [kw for kw in keywords if re.search(rf"\b{re.escape(kw)}\b", lowered)]


def score(text: str, locale: str = DEFAULT_LOCALE) -> int:
    return len(matches(text, locale))
