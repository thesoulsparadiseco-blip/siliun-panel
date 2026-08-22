"""
tesla_engine — capa 5.1 del spec ("Tesla 3-6-9").

Nota de honestidad (misma postura que backend/claude_client.py): la
numerología 3-6-9 es contenido simbólico/reflexivo, no una ley física
verificada. Aquí se implementa como una heurística determinista de
"raíz digital" (digital root), técnica real de aritmética modular, para
asignarle a cada entrada una de las tres "puertas" (3, 6 o 9) que el
resto del organismo usa como parámetro de ritmo/intensidad — no como
predicción de nada.

Regla:
  1. seed = suma de los códigos unicode de los caracteres de `text`.
  2. root = raíz digital de seed (1-9; 0 solo si seed == 0).
  3. si root está en {3, 6, 9} -> esa es la puerta.
  4. si no, se asigna la puerta {3, 6, 9} más cercana en el círculo 1-9.
"""
from dataclasses import dataclass

GATES = (3, 6, 9)


def digital_root(n: int) -> int:
    if n == 0:
        return 0
    r = n % 9
    return 9 if r == 0 else r


def _nearest_gate(root: int) -> int:
    return min(GATES, key=lambda g: min(abs(g - root), 9 - abs(g - root)))


@dataclass(frozen=True)
class TeslaPhase:
    seed: int
    root: int
    gate: int

    @property
    def intensity(self) -> float:
        """0.0-1.0: qué tan directa fue la puerta (root ya era 3/6/9) vs. aproximada."""
        return 1.0 if self.root in GATES else 0.5


def compute(text: str) -> TeslaPhase:
    seed = sum(ord(c) for c in text) or 1
    root = digital_root(seed)
    gate = root if root in GATES else _nearest_gate(root)
    return TeslaPhase(seed=seed, root=root, gate=gate)
