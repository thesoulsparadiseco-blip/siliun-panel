"""
memory/internal — capa 6.1 del spec: identity.json, projects.json,
rituals.json, formulas.json, architectures.json.

Mismo patrón que backend/storage.py (JSON plano + lock), a propósito:
si este paquete termina viviendo dentro del mismo backend, comparte
convenciones de persistencia con el resto del proyecto.
"""
import json
import os
import threading
from typing import Any, Dict

from . import DATA_DIR

_INTERNAL_DIR = os.path.join(DATA_DIR, "internal")
_lock = threading.Lock()

DOCS = ("identity", "projects", "rituals", "formulas", "architectures")


def _path(doc: str) -> str:
    if doc not in DOCS:
        raise ValueError(f"Documento de memoria interna desconocido: '{doc}'. Válidos: {DOCS}")
    return os.path.join(_INTERNAL_DIR, f"{doc}.json")


def load(doc: str) -> Dict[str, Any]:
    with _lock:
        path = _path(doc)
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return json.loads(content) if content else {}


def save(doc: str, data: Dict[str, Any]) -> None:
    with _lock:
        path = _path(doc)
        os.makedirs(_INTERNAL_DIR, exist_ok=True)
        tmp = f"{path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)


def update(doc: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    data = load(doc)
    data.update(patch)
    save(doc, data)
    return data
