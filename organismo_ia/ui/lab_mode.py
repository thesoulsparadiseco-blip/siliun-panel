"""ui/lab_mode — contrato JSON del modo laboratorio (fórmulas/arquitecturas, capa 1 del spec)."""
from ..i18n import DEFAULT_LOCALE, get as get_locale
from ..memory import internal


def describe(locale: str = DEFAULT_LOCALE) -> dict:
    t = get_locale(locale)["ui"]["lab_mode"]
    return {
        "mode": "lab_mode",
        "title": t["title"],
        "description": t["description"],
        "formulas": list(internal.load("formulas").keys()),
        "architectures": list(internal.load("architectures").keys()),
        "actions": [{"id": "save_formula", "label": t["action_label"]}],
    }
