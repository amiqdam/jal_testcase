"""
DraftResponse model — AI-generated response drafts pending admin approval.
"""
from pydantic import BaseModel
from typing import Optional


class DraftResponse(BaseModel):
    """Draft response database record."""
    id: str
    message_id: str
    lead_id: str
    content: str
    personalization_signals: Optional[str] = None  # JSON string
    status: str = "pending"  # pending | approved | sent | edited
    edited_content: Optional[str] = None
    created_at: str = ""


class DraftEdit(BaseModel):
    """Input schema for editing a draft response."""
    content: str
