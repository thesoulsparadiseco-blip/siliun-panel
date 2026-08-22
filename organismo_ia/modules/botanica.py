"""
module_botanica — capa 4.2 del spec.

A diferencia de voice/vision/movement, este módulo no depende de
hardware: expone consultas de fórmulas/plantas contra la memoria interna
(memory/internal.py, doc "formulas"), que sí corre completo en servidor.
"""
from ..memory import internal


def list_formulas() -> dict:
    return internal.load("formulas")


def save_formula(name: str, formula: dict) -> dict:
    data = internal.load("formulas")
    data[name] = formula
    internal.save("formulas", data)
    return data
