"""
Pydantic models for Siliun Panel.
The UserState schema mirrors the JSON standard defined in the spec:
Webflow CMS, Streamlit/FastAPI backend and Cloudflare KV all speak this shape.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class StateHistoryEntry(BaseModel):
    ts: str
    clarity: float
    rhythm: float
    resonanceScore: float


class UserState(BaseModel):
    userId: str
    email: str
    name: str
    memberPlan: str = "Troton Pro"
    clarity: float = 0
    rhythm: float = 0
    intention: int = 0
    silence: bool = False
    resonanceScore: float = 0
    user_state_ready: bool = False
    last_state_check: Optional[str] = None
    stateHistory: List[StateHistoryEntry] = Field(default_factory=list)
    malakaiAccess: bool = False
    pathsOpened: List[str] = Field(default_factory=list)
    notes: Optional[str] = ""
    signals: List[Dict[str, Any]] = Field(default_factory=list)


class UserCreate(BaseModel):
    userId: str
    email: str
    name: str
    memberPlan: str = "Troton Pro"
    clarity: float = 0
    rhythm: float = 0
    intention: int = 0
    silence: bool = False
    notes: Optional[str] = ""


class StateUpdate(BaseModel):
    clarity: Optional[float] = None
    rhythm: Optional[float] = None
    intention: Optional[int] = None
    silence: Optional[bool] = None


class NoteUpdate(BaseModel):
    note: str


class MessagePayload(BaseModel):
    subject: Optional[str] = None
    body: str
    channel: str = "discord"  # discord | email (email requires a provider to be wired up)


class AuditLogEntry(BaseModel):
    admin: Optional[str] = None
    action: str
    target_user: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
