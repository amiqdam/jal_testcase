"""
NextAction model — recommended next best actions for admissions team.
Updated to match NBA Agent output with conversion boosters.
"""
from pydantic import BaseModel
from typing import Optional, List


class NextAction(BaseModel):
    """Next action database record."""
    id: str
    lead_id: str
    action_type: str  # auto_respond | send_brochure | invite_tour | connect_alumni | assign_counselor | fast_track | schedule_call | escalate
    action_detail: str
    priority: str = "low"  # low | medium | critical
    reasoning: Optional[str] = None
    conversion_boosters: List[str] = []
    due_at: Optional[str] = None
    completed_at: Optional[str] = None
    created_at: str = ""
