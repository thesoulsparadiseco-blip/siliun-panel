"""
i18n — registro de idiomas del organismo.

Añadir un idioma nuevo es: crear `<código>.py` con el mismo dict `DATA`
que `es.py`/`en.py` (mismas claves), importarlo aquí y sumarlo a
`LOCALES`. Nada del resto del paquete (core/, agents/, ui/) necesita
tocarse — todos leen el contenido a través de `get(locale)`.
"""
import re
from typing import Dict

from . import es, en

LOCALES: Dict[str, dict] = {"es": es.DATA, "en": en.DATA}
DEFAULT_LOCALE = "es"
SUPPORTED_LOCALES = tuple(LOCALES)

_WORD_RE = re.compile(r"[a-záéíóúñü']+")

# Detección de idioma por solapamiento de stopwords — heurística liviana a
# propósito (sin dependencias nuevas tipo langdetect/fasttext). Alcanza para
# distinguir español/inglés en mensajes cortos; añadir un idioma nuevo aquí
# también activa la autodetección para ese idioma.
_STOPWORDS: Dict[str, set] = {
    "es": {
        "de", "la", "que", "el", "en", "y", "a", "los", "se", "del", "las", "un",
        "por", "con", "no", "una", "su", "para", "es", "al", "lo", "como", "más",
        "pero", "sus", "le", "ya", "este", "sí", "porque", "esta", "entre",
        "cuando", "muy", "sin", "sobre", "también", "me", "hasta", "hay",
        "donde", "quien", "desde", "todo", "nos", "durante", "todos", "les",
        "mi", "tú", "te", "tu", "tus", "quiero", "puedo", "siento", "estoy",
    },
    "en": {
        "the", "is", "are", "and", "to", "of", "in", "that", "it", "for", "on",
        "with", "as", "was", "at", "by", "an", "be", "this", "have", "from",
        "or", "one", "had", "but", "not", "what", "all", "were", "we", "when",
        "your", "can", "there", "each", "which", "she", "do", "how", "their",
        "if", "will", "up", "other", "about", "my", "i", "you", "want", "feel",
    },
}


def detect_locale(text: str) -> str:
    words = _WORD_RE.findall(text.lower())
    if not words:
        return DEFAULT_LOCALE
    scores = {
        locale: sum(1 for w in words if w in stopwords)
        for locale, stopwords in _STOPWORDS.items()
    }
    best_locale, best_score = max(scores.items(), key=lambda kv: kv[1])
    return best_locale if best_score > 0 else DEFAULT_LOCALE


def get(locale: str) -> dict:
    return LOCALES.get(locale, LOCALES[DEFAULT_LOCALE])
