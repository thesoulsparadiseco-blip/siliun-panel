"""
ui/portal — capa 1/4 del spec: contrato JSON del modo de entrada
principal. Este backend no renderiza UI (eso es Flutter/React Native,
sección 4.1); expone la estructura que un frontend usa para dibujar la
pantalla, consistente con cómo backend/main.py ya sirve un frontend
estático propio en /agent.
"""
from ..i18n import DEFAULT_LOCALE, get as get_locale


def describe(locale: str = DEFAULT_LOCALE) -> dict:
    t = get_locale(locale)["ui"]["portal"]
    return {
        "mode": "portal",
        "title": t["title"],
        "description": t["description"],
        "inputs": ["text", "voice", "camera", "file"],
        "actions": [{"id": "invoke", "label": t["action_label"]}],
    }
