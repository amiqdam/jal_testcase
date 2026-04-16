"""
Message model — represents a single chat message (inbound or outbound).
"""
from pydantic import BaseModel
from typing import Optional


class Message(BaseModel):
    """Message database record."""
    id: str
    lead_id: str
    direction: str  # "inbound" | "outbound"
    content: str
    language: Optional[str] = None
    macro_intent: Optional[str] = None
    micro_intent: Optional[str] = None
    intent_confidence: Optional[float] = None
    sentiment: Optional[str] = None
    processing_log: Optional[str] = None  # JSON string with reasoning traces
    processing_time_ms: Optional[int] = None
    created_at: str = ""


class MessageCreate(BaseModel):
    """Input schema for sending a new message."""
    email: str
    name: str
    content: str
    lead_source: Optional[str] = None  # Only needed on first message
    quick_start_intent: Optional[str] = None


class MessageResponse(BaseModel):
    """Response schema after processing a message."""
    lead_id: str
    message_id: str
    response: str
    processing_log: Optional[dict] = None


class AdminReply(BaseModel):
    """Input schema for admin manual reply."""
    content: str
