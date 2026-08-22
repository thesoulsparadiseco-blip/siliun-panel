"""
memory/vector_db — capa 6.1 del spec: "Vector DB local: sqlite + embeddings".

Usa sólo la librería estándar (sqlite3) — nada de numpy/faiss/modelos de
embeddings, que no están disponibles en este entorno de servidor. El
"embedding" es un hashing trick determinista (bag-of-words -> vector de
dimensión fija, técnica real y liviana) que alcanza para similitud
aproximada por palabras compartidas; es un placeholder documentado para
cuando el cliente móvil tenga un modelo local de embeddings real
(sección 5 del spec) — swap del `embed()` de abajo sin tocar el resto.
"""
import hashlib
import json
import math
import os
import re
import sqlite3
from datetime import datetime, timezone
from typing import List, Tuple

from . import DATA_DIR

DB_PATH = os.path.join(DATA_DIR, "vector_db.sqlite3")
DIM = 128
_WORD_RE = re.compile(r"[a-záéíóúñü0-9]+", re.IGNORECASE)


def _connect() -> sqlite3.Connection:
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memory_vectors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            text TEXT NOT NULL,
            embedding TEXT NOT NULL,
            ts TEXT NOT NULL
        )
    """)
    return conn


def _stable_hash(word: str) -> int:
    """int(hash) determinista entre procesos (a diferencia de hash() built-in,
    que Python aleatoriza por seguridad salvo PYTHONHASHSEED fijo) — necesario
    porque los embeddings se persisten en sqlite y se comparan entre runs."""
    digest = hashlib.md5(word.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def embed(text: str) -> List[float]:
    """Hashing-trick bag-of-words -> vector normalizado de dimensión DIM."""
    vec = [0.0] * DIM
    for word in _WORD_RE.findall(text.lower()):
        h = _stable_hash(word)
        idx = h % DIM
        sign = 1.0 if (h >> 1) % 2 == 0 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def add(user_id: str, text: str) -> int:
    conn = _connect()
    try:
        vec = embed(text)
        ts = datetime.now(timezone.utc).isoformat()
        cur = conn.execute(
            "INSERT INTO memory_vectors (user_id, text, embedding, ts) VALUES (?, ?, ?, ?)",
            (user_id, text, json.dumps(vec), ts),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def search(user_id: str, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT text, embedding FROM memory_vectors WHERE user_id = ?", (user_id,)
        ).fetchall()
    finally:
        conn.close()
    q = embed(query)
    scored = [(text, _cosine(q, json.loads(emb))) for text, emb in rows]
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored[:top_k]
