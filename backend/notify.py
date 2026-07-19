"""
Pluggable notification sender for POST /admin/user/:id/message.

Only Discord is wired up (via a webhook, matching the Make/Discord flow in
the spec's deployment steps 5 and 6). Email is a labeled stub — plug in
Resend/SendGrid/etc. and implement _send_email when you're ready.
"""
import os
import requests


def send(user: dict, payload) -> bool:
    channel = getattr(payload, "channel", "discord")
    if channel == "discord":
        return _send_discord(user, payload)
    if channel == "email":
        return _send_email(user, payload)
    raise ValueError(f"Unsupported channel: {channel}")


def _send_discord(user: dict, payload) -> bool:
    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook:
        return False  # not configured; caller should surface this as a failed send
    text = f"**{payload.subject or 'Siliun Panel'}** — para {user.get('name')} ({user.get('userId')})\n{payload.body}"
    resp = requests.post(webhook, json={"content": text}, timeout=10)
    return resp.status_code < 300


def _send_email(user: dict, payload) -> bool:
    # Stub: no email provider configured yet. Wire this to Resend/SendGrid/etc.
    return False
