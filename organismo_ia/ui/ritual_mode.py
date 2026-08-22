"""ui/ritual_mode — contrato JSON del modo de rituales guiados (capa 1 del spec)."""
from ..i18n import DEFAULT_LOCALE, get as get_locale
from ..memory import internal


def describe(locale: str = DEFAULT_LOCALE) -> dict:
    t = get_locale(locale)["ui"]["ritual_mode"]
    rituals = internal.load("rituals")
    return {
        "mode": "ritual_mode",
        "title": t["title"],
        "description": t["description"],
        "rituals": list(rituals.keys()),
        "actions": [{"id": "start_ritual", "label": t["action_label"]}],
    }
