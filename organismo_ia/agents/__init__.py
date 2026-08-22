from .solkin import Solkin
from .vitalion import Vitalion
from .almir import Almir
from .nodar import Nodar
from .helion import Helion
from .paradion import Paradion
from .synar import Synar
from .arkhon import Arkhon
from .jakhar import Jakhar

ALL_AGENTS = [Solkin(), Vitalion(), Almir(), Nodar(), Helion(), Paradion(), Synar(), Arkhon(), Jakhar()]

__all__ = [
    "Solkin", "Vitalion", "Almir", "Nodar", "Helion", "Paradion", "Synar",
    "Arkhon", "Jakhar", "ALL_AGENTS",
]
