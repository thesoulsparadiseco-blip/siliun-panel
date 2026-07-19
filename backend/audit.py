from typing import Any, Dict, Optional
from . import storage


def log_action(admin: str, action: str, target_user: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
    storage.append_audit({
        "ts": storage.now_iso(),
        "admin": admin,
        "action": action,
        "target_user": target_user,
        "details": details or {},
    })
