"""
NextAction model — recommended next best actions for admissions team.
"""
from pydantic import BaseModel
from typing import Optional


class NextAction(BaseModel):
    """Next action database record."""
    id: str
    lead_id: str
    action_type: str
    action_detail: str
    priority: str = "medium"
    reasoning: Optional[str] = None
    due_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str = ""
