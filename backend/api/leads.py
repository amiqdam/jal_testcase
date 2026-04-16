"""
Leads API endpoints — list, detail, and admin override.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.services.lead_service import LeadService
from backend.models.lead import LeadUpdate

router = APIRouter()
lead_service = LeadService()


@router.get("")
async def list_leads(
    funnel_stage: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    intent: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """List leads with filtering and pagination."""
    return lead_service.get_leads_filtered(
        stage=funnel_stage,
        urgency=urgency,
        intent=intent,
        search=search,
        page=page,
        limit=limit
    )


@router.get("/{lead_id}")
async def get_lead(lead_id: str):
    """Get complete lead detail with messages, drafts, and actions."""
    lead = lead_service.get_lead_detail(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


@router.patch("/{lead_id}")
async def update_lead(lead_id: str, update: LeadUpdate):
    """Admin override for lead properties (funnel_stage, urgency, etc.)."""
    result = lead_service.admin_override(lead_id, update.model_dump(exclude_none=True))
    if not result:
        raise HTTPException(status_code=404, detail="Lead not found or no changes")
    return result
