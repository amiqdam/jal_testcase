"""
Leads API — list leads, detail, and admin override.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.services.lead_service import LeadService
from backend.models.lead import LeadUpdate

router = APIRouter()
lead_service = LeadService()


@router.get("")
async def list_leads(
    stage: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    macro_intent: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    lead_source: Optional[str] = Query(None),
    interested_program: Optional[str] = Query(None),
    school_type: Optional[str] = Query(None),
    contact_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Get filtered and paginated leads list."""
    return lead_service.get_leads_filtered(
        stage, urgency, macro_intent, search, page, limit,
        lead_source, interested_program, school_type, contact_type
    )


@router.get("/{lead_id}")
async def get_lead_detail(lead_id: str):
    """Get complete lead detail with messages, drafts, and actions."""
    lead = lead_service.get_lead_detail(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id}")
async def admin_override(lead_id: str, updates: LeadUpdate):
    """Admin override for lead funnel_stage and urgency."""
    result = lead_service.admin_override(lead_id, updates.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=400, detail="No valid updates provided")
    return result
