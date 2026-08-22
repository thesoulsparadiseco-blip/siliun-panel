"""
module_voice_bank — banco de voces del organismo (extensión de la capa
4.2 / module_voice, spec section 4.2).

Catálogo estático de perfiles de voz (timbre, rango, ritmo, intención,
uso, paleta sónica y frases base) que un cliente TTS (móvil, sección 4.1)
usa para elegir *qué* voz sintetizar, no *cómo* sintetizarla — la síntesis
real de audio sigue siendo responsabilidad de modules/voice.py
(device-bound, no disponible en este backend de servidor).

Catálogo fijo a propósito: a diferencia de module_botanica (fórmulas
editables en memory/internal), el banco de voces es identidad de marca
del organismo, no un dato de usuario — no se expone `save_voice`.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class VoiceProfile:
    nombre: str
    timbre: str
    rango: str
    ritmo: str
    intencion: str
    uso: str
    paleta_sonica: Tuple[str, ...] = field(default_factory=tuple)
    frases_base: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "nombre": self.nombre,
            "timbre": self.timbre,
            "rango": self.rango,
            "ritmo": self.ritmo,
            "intencion": self.intencion,
            "uso": self.uso,
            "paleta_sonica": list(self.paleta_sonica),
            "frases_base": list(self.frases_base),
        }


_BANCO: Tuple[VoiceProfile, ...] = (
    VoiceProfile(
        nombre="SILIUN",
        timbre="metálico-suave, plateado, resonancia limpia",
        rango="medio-grave",
        ritmo="pausado, preciso, sin prisa",
        intencion="claridad, guía, enfoque mental",
        uso="activaciones, instrucciones, rituales de enfoque, voz principal de agentes",
        paleta_sonica=("metal plateado", "aire frío", "resonancia limpia"),
        frases_base=(
            "Respira. Estoy aquí para guiarte.",
            "Enfoca tu atención en el punto central.",
            "Avanza con precisión.",
        ),
    ),
    VoiceProfile(
        nombre="KALEN",
        timbre="dorado, cálido, expansivo",
        rango="grave-medio",
        ritmo="firme, constante, con micro-pausas",
        intencion="fuerza, dirección, estructura",
        uso="motivación, entrenamiento, activaciones físicas, rituales solares",
        paleta_sonica=("fuego solar", "madera cálida", "grave resonante"),
        frases_base=(
            "Activa tu fuerza interna.",
            "El movimiento nace del centro.",
            "Sostén la dirección.",
        ),
    ),
    VoiceProfile(
        nombre="LUMARA",
        timbre="brillante, cristalino, eco suave",
        rango="medio-agudo",
        ritmo="fluido, envolvente",
        intencion="apertura, suavidad, claridad emocional",
        uso="meditaciones, brumas corporales, rituales de calma, guías sensoriales",
        paleta_sonica=("cristal", "aire tibio", "luz suave"),
        frases_base=(
            "Abre el espacio interno.",
            "Permite que la luz te envuelva.",
            "Respira con suavidad.",
        ),
    ),
    VoiceProfile(
        nombre="NODAL",
        timbre="digital-profundo, textura holográfica",
        rango="grave",
        ritmo="lento, resonante, sintético",
        intencion="inmersión, presencia, espacio",
        uso="mundos Spatial, activaciones de portales, intros de sistemas 6G",
        paleta_sonica=("bajo holográfico", "eco digital", "vibración profunda"),
        frases_base=(
            "Accediendo al espacio nodal.",
            "El portal está activo.",
            "Bienvenido al entorno inmersivo.",
        ),
    ),
    VoiceProfile(
        nombre="ARKAI",
        timbre="precisa, técnica, sin vibrato",
        rango="medio",
        ritmo="rápido, eficiente",
        intencion="orden, lógica, ejecución",
        uso="agentes programadores, instrucciones técnicas, sistemas DeFi",
        paleta_sonica=("código digital", "metal técnico", "clics sintéticos"),
        frases_base=(
            "Ejecutando instrucción.",
            "Parámetros listos.",
            "Sistema optimizado.",
        ),
    ),
    VoiceProfile(
        nombre="SORA-ECHO",
        timbre="aireada, reverberación corta",
        rango="medio-agudo",
        ritmo="dinámico, adaptable",
        intencion="estética, fluidez, creatividad",
        uso="ediciones de video, intros, trailers, contenido viral",
        paleta_sonica=("aire creativo", "eco corto", "neón vibrante"),
        frases_base=(
            "Iniciando secuencia visual.",
            "Movimiento y luz sincronizados.",
            "Expande la estética.",
        ),
    ),
)

_BY_NAME: Dict[str, VoiceProfile] = {v.nombre.upper(): v for v in _BANCO}

DEFAULT_VOICE = "SILIUN"


def list_voices() -> List[dict]:
    return [v.to_dict() for v in _BANCO]


def get_voice(nombre: str) -> Optional[dict]:
    profile = _BY_NAME.get(nombre.strip().upper())
    return profile.to_dict() if profile else None


def voices_for_uso(query: str) -> List[dict]:
    """Perfiles cuyo campo `uso` menciona `query` (búsqueda simple, insensible a mayúsculas)."""
    needle = query.strip().lower()
    if not needle:
        return []
    return [v.to_dict() for v in _BANCO if needle in v.uso.lower()]
