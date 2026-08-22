"""
memory/graph_db — capa 6.1 del spec: "Grafo de conocimiento: neo4j
local / sqlite graph". Sin neo4j disponible en este entorno, se
implementa el grafo sobre sqlite (nodes + edges), suficiente para
recorridos de vecinos; el punto de extensión (swap a neo4j real) queda
documentado acá para cuando el despliegue lo soporte.
"""
import os
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import DATA_DIR

DB_PATH = os.path.join(DATA_DIR, "graph_db.sqlite3")


def _connect() -> sqlite3.Connection:
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            label TEXT NOT NULL,
            ts TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            target TEXT NOT NULL,
            relation TEXT NOT NULL,
            ts TEXT NOT NULL,
            FOREIGN KEY(source) REFERENCES nodes(id),
            FOREIGN KEY(target) REFERENCES nodes(id)
        )
    """)
    return conn


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def add_node(node_id: str, node_type: str, label: str) -> None:
    conn = _connect()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO nodes (id, type, label, ts) VALUES (?, ?, ?, ?)",
            (node_id, node_type, label, _now()),
        )
        conn.commit()
    finally:
        conn.close()


def add_edge(source: str, target: str, relation: str) -> None:
    conn = _connect()
    try:
        conn.execute(
            "INSERT INTO edges (source, target, relation, ts) VALUES (?, ?, ?, ?)",
            (source, target, relation, _now()),
        )
        conn.commit()
    finally:
        conn.close()


def neighbors(node_id: str) -> List[Dict[str, Any]]:
    conn = _connect()
    try:
        rows = conn.execute(
            """SELECT n.id, n.type, n.label, e.relation FROM edges e
               JOIN nodes n ON n.id = e.target
               WHERE e.source = ?""",
            (node_id,),
        ).fetchall()
    finally:
        conn.close()
    return [{"id": r[0], "type": r[1], "label": r[2], "relation": r[3]} for r in rows]


def get_node(node_id: str) -> Optional[Dict[str, Any]]:
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT id, type, label, ts FROM nodes WHERE id = ?", (node_id,)
        ).fetchone()
    finally:
        conn.close()
    return {"id": row[0], "type": row[1], "label": row[2], "ts": row[3]} if row else None
