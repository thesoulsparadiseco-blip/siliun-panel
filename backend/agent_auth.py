"""
Bearer-token auth for /api/agent/* routes.

Separate from SILIUN_ADMIN_TOKEN (backend/auth.py) on purpose: the personal
agent is meant to be reachable from the owner's own devices only, not from
whoever holds the admin panel token, and vice versa.
"""
import os
from fastapi import Header, HTTPException

AGENT_TOKEN = os.getenv("AGENT_TOKEN")


def verify_agent(authorization: str = Header(None)) -> str:
    if not AGENT_TOKEN:
        raise HTTPException(500, "Server misconfigured: AGENT_TOKEN is not set")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing 'Authorization: Bearer <token>' header")
    token = authorization.split(" ", 1)[1]
    if token != AGENT_TOKEN:
        raise HTTPException(403, "Invalid agent token")
    return token
