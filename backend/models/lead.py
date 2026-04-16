"""
Lead model — represents a prospective student (calon mahasiswa).
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Lead(BaseModel):
    """Lead database record."""
    id: str
    session_id: str
    name: Optional[str] = None
    contact_type: str = "unknown"
    language_pref: str = "id"
    school_origin: Optional[str] = None
    school_type: Optional[str] = None
    interested_program: Optional[str] = None
    nationality: Optional[str] = None
    academic_achievement: Optional[str] = None
    financial_concern: bool = False
    funnel_stage: str = "awareness"
    urgency: str = "low"
    conversion_probability: float = 0.0
    profile_json: Optional[str] = None
    assigned_counselor: Optional[str] = None
    channel: str = "chatbot"
    tags: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


class LeadSummary(BaseModel):
    """Lightweight lead info for list views."""
    id: str
    session_id: str
    name: Optional[str] = None
    contact_type: str = "unknown"
    funnel_stage: str = "awareness"
    urgency: str = "low"
    interested_program: Optional[str] = None
    last_message_preview: Optional[str] = None
    last_message_at: Optional[str] = None
    created_at: str = ""


class LeadUpdate(BaseModel):
    """Fields that can be updated by admin override."""
    funnel_stage: Optional[str] = None
    urgency: Optional[str] = None
    assigned_counselor: Optional[str] = None
    tags: Optional[str] = None
