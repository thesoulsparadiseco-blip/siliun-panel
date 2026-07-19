"""
Bearer-token auth for /admin/* routes.

The real gate is Cloudflare (firewall rule requiring this same header,
see README section 6). This check is defense-in-depth so the API is not
wide open even if someone reaches Render directly, bypassing Cloudflare.
"""
import os
from fastapi import Header, HTTPException

ADMIN_TOKEN = os.getenv("SILIUN_ADMIN_TOKEN")


def verify_admin(
    authorization: str = Header(None),
    x_admin_id: str = Header(None),
) -> str:
    if not ADMIN_TOKEN:
        raise HTTPException(500, "Server misconfigured: SILIUN_ADMIN_TOKEN is not set")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing 'Authorization: Bearer <token>' header")
    token = authorization.split(" ", 1)[1]
    if token != ADMIN_TOKEN:
        raise HTTPException(403, "Invalid admin token")
    return x_admin_id or "unknown-admin"
