"""ui/metaverso_mode — contrato JSON del modo Metaverso Nodal (agente Nodar, capa 1 del spec)."""
from ..i18n import DEFAULT_LOCALE, get as get_locale
from ..memory import internal


def describe(locale: str = DEFAULT_LOCALE) -> dict:
    t = get_locale(locale)["ui"]["metaverso_mode"]
    return {
        "mode": "metaverso_mode",
        "title": t["title"],
        "description": t["description"],
        "projects": list(internal.load("projects").keys()),
        "actions": [{"id": "open_node", "label": t["action_label"]}],
    }
