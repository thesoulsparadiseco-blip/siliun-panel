"""
elemental_engine — capa 5.1 del spec (Tierra/Fuego/Agua/Aire/Éter).

Clasificador léxico determinista (sin modelo, sin red): cuenta
coincidencias de palabras clave en español por elemento y devuelve el
elemento dominante. Es una heurística simple a propósito — el punto de
extensión real es reemplazar `score()` por un embedding local (ver
memory/vector_db.py) cuando haya un modelo on-device disponible.
"""
from dataclasses import dataclass
from typing import Dict

ELEMENTOS: Dict[str, list] = {
    "Tierra": ["cuerpo", "dinero", "trabajo", "estabilidad", "salud", "hogar",
               "seguridad", "material", "constancia", "raíz", "raiz", "sostén", "sosten"],
    "Fuego": ["pasión", "pasion", "acción", "accion", "voluntad", "energía", "energia",
              "transformación", "transformacion", "ira", "impulso", "coraje", "deseo"],
    "Agua": ["emoción", "emocion", "intuición", "intuicion", "sueños", "suenos",
             "sanación", "sanacion", "fluidez", "sentir", "duelo", "vínculo", "vinculo"],
    "Aire": ["mente", "ideas", "comunicación", "comunicacion", "claridad", "estrategia",
             "pensar", "análisis", "analisis", "palabra", "plan"],
    "Éter": ["espíritu", "espiritu", "propósito", "proposito", "conexión", "conexion",
             "sincronía", "sincronia", "alma", "trascender", "unidad", "silencio"],
}

DEFAULT_ELEMENT = "Aire"


@dataclass(frozen=True)
class ElementalReading:
    element: str
    scores: Dict[str, int]


def score(text: str) -> Dict[str, int]:
    lowered = text.lower()
    return {el: sum(lowered.count(kw) for kw in kws) for el, kws in ELEMENTOS.items()}


def classify(text: str) -> ElementalReading:
    scores = score(text)
    best = max(scores.items(), key=lambda kv: kv[1])
    element = best[0] if best[1] > 0 else DEFAULT_ELEMENT
    return ElementalReading(element=element, scores=scores)
