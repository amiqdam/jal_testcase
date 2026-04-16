"""
Lead model — represents a prospective student / parent / counselor.
All profile fields except email and name are nullable to support non-student users.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Lead(BaseModel):
    """Lead database record."""
    id: str
    email: str
    name: str
    contact_type: str = "unknown"
    language_pref: str = "id"
    school_origin: Optional[str] = None
    school_type: Optional[str] = None
    kelas: Optional[str] = None
    umur: Optional[int] = None
    interested_program: Optional[str] = None
    nationality: Optional[str] = None
    academic_achievement: Optional[str] = None
    phone_number: Optional[str] = None
    tanggal_lahir: Optional[str] = None
    financial_concern: bool = False
    lead_source: str = "lainnya"
    macro_intent: Optional[str] = None
    micro_intent: Optional[str] = None
    funnel_stage: str = "awareness"
    urgency: str = "low"
    channel: str = "chatbot"
    created_at: str = ""
    updated_at: str = ""


class LeadSummary(BaseModel):
    """Lightweight lead info for list views."""
    id: str
    email: str
    name: str
    contact_type: str = "unknown"
    funnel_stage: str = "awareness"
    urgency: str = "low"
    macro_intent: Optional[str] = None
    micro_intent: Optional[str] = None
    interested_program: Optional[str] = None
    lead_source: Optional[str] = None
    last_message_preview: Optional[str] = None
    last_message_at: Optional[str] = None
    created_at: str = ""


class LeadUpdate(BaseModel):
    """Fields that can be updated by admin override."""
    funnel_stage: Optional[str] = None
    urgency: Optional[str] = None
