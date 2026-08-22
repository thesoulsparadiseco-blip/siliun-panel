from .portal import describe as portal
from .ritual_mode import describe as ritual_mode
from .lab_mode import describe as lab_mode
from .metaverso_mode import describe as metaverso_mode

MODES = {
    "portal": portal,
    "ritual_mode": ritual_mode,
    "lab_mode": lab_mode,
    "metaverso_mode": metaverso_mode,
}
