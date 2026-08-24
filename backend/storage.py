"""
Minimal JSON-file storage layer so the panel can ship today.

IMPORTANT (production note): Render's default filesystem is ephemeral on
free/hobby plans — a redeploy wipes it. render.yaml attaches a small
persistent disk mounted at DATA_DIR so this survives restarts, but for real
production use swap this module for Postgres (Render offers a free Postgres
instance) and keep the same function signatures so nothing else has to change.
"""
import json
import os
import threading
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

DATA_DIR = os.getenv("DATA_DIR", "./data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
AUDIT_FILE = os.path.join(DATA_DIR, "audit_log.jsonl")
RATE_FILE = os.path.join(DATA_DIR, "rate_counters.json")
AGENT_CONVERSATION_FILE = os.path.join(DATA_DIR, "agent_conversation.json")
MAX_AGENT_CONVERSATION = 200

_lock = threading.Lock()


class RateLimitExceeded(Exception):
    pass


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _load_json(path: str, default: Any) -> Any:
    _ensure_data_dir()
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if not content:
            return default
        return json.loads(content)


def _save_json(path: str, data: Any):
    _ensure_data_dir()
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, path)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------- Users ----------------

def _load_users() -> Dict[str, Dict]:
    return _load_json(USERS_FILE, {})


def _save_users(users: Dict[str, Dict]):
    _save_json(USERS_FILE, users)


def get_user(user_id: str) -> Optional[Dict]:
    with _lock:
        users = _load_users()
        return users.get(user_id)


def list_users() -> List[Dict]:
    with _lock:
        return list(_load_users().values())


def upsert_user(user: Dict) -> Dict:
    with _lock:
        users = _load_users()
        users[user["userId"]] = user
        _save_users(users)
        return user


def seed_demo_user_if_empty():
    """Seeds the Angelo demo record from the spec so the panel isn't empty on first boot."""
    with _lock:
        users = _load_users()
        if users:
            return
        demo = {
            "userId": "u_12345",
            "email": "angelo@example.com",
            "name": "Angelo",
            "memberPlan": "Troton Pro",
            "clarity": 78,
            "rhythm": 64,
            "intention": 1,
            "silence": True,
            "resonanceScore": 72,
            "user_state_ready": False,
            "last_state_check": "2026-07-16T07:58:00Z",
            "stateHistory": [
                {"ts": "2026-07-15T08:00:00Z", "clarity": 70, "rhythm": 60, "resonanceScore": 65}
            ],
            "malakaiAccess": False,
            "pathsOpened": ["luz_dorada"],
            "notes": "Prefiere sesiones por la mañana",
            "signals": [],
        }
        users[demo["userId"]] = demo
        _save_users(users)


# ---------------- Audit log ----------------

def append_audit(entry: Dict):
    _ensure_data_dir()
    with _lock:
        with open(AUDIT_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def get_audit(limit: int = 100) -> List[Dict]:
    _ensure_data_dir()
    if not os.path.exists(AUDIT_FILE):
        return []
    with _lock:
        with open(AUDIT_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    entries = [json.loads(l) for l in lines if l.strip()]
    return list(reversed(entries))[:limit]


# ---------------- Personal agent memory ----------------
# Single owner (one AGENT_TOKEN), so this is one flat conversation log —
# no per-user keying needed. Lets /agent survive a reload or a different
# device instead of starting blank every time.

def load_agent_conversation() -> List[Dict]:
    with _lock:
        return _load_json(AGENT_CONVERSATION_FILE, [])


def append_agent_messages(entries: List[Dict]):
    if not entries:
        return
    with _lock:
        conv = _load_json(AGENT_CONVERSATION_FILE, [])
        conv.extend(entries)
        if len(conv) > MAX_AGENT_CONVERSATION:
            conv = conv[-MAX_AGENT_CONVERSATION:]
        _save_json(AGENT_CONVERSATION_FILE, conv)


# ---------------- Rate limiting ----------------

def check_rate_limit(key: str, limit: int):
    """Raises RateLimitExceeded if `key` has already hit `limit` uses today."""
    today = date.today().isoformat()
    full_key = f"{key}:{today}"
    with _lock:
        counters = _load_json(RATE_FILE, {})
        count = counters.get(full_key, 0)
        if count >= limit:
            raise RateLimitExceeded(f"Rate limit exceeded for '{key}': {limit}/day")
        counters[full_key] = count + 1
        _save_json(RATE_FILE, counters)
