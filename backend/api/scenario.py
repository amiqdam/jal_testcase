"""
Scenario Adaptation API — Runtime configuration for lead sources, quick start options.
Allows admin to simulate system changes (new channels, updated options).
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from backend.config import runtime_config, LEAD_SOURCES, QUICK_START_OPTIONS

router = APIRouter()


class LeadSourceUpdate(BaseModel):
    sources: List[str]


class QuickStartOption(BaseModel):
    id: str
    label: str
    macro_intent: str
    micro_intent: str
    message: str


class QuickStartUpdate(BaseModel):
    options: List[QuickStartOption]


@router.get("/config")
async def get_scenario_config():
    """Return current runtime configuration (lead sources, quick start options)."""
    return {
        "lead_sources": runtime_config.get_lead_sources(),
        "quick_start_options": runtime_config.get_quick_start_options(),
        "default_lead_sources": LEAD_SOURCES,
        "default_quick_start_options": QUICK_START_OPTIONS,
    }


@router.put("/lead-sources")
async def update_lead_sources(body: LeadSourceUpdate):
    """Update the list of active lead sources (channels)."""
    runtime_config.update_lead_sources(body.sources)
    return {
        "status": "ok",
        "message": f"Updated to {len(body.sources)} lead sources",
        "lead_sources": runtime_config.get_lead_sources(),
    }


@router.put("/quick-start")
async def update_quick_start(body: QuickStartUpdate):
    """Update quick start options shown in the chatbot."""
    options = [opt.model_dump() for opt in body.options]
    runtime_config.update_quick_start_options(options)
    return {
        "status": "ok",
        "message": f"Updated to {len(options)} quick start options",
        "quick_start_options": runtime_config.get_quick_start_options(),
    }


@router.post("/reset")
async def reset_to_defaults():
    """Reset runtime config to defaults."""
    runtime_config.update_lead_sources(list(LEAD_SOURCES))
    runtime_config.update_quick_start_options(list(QUICK_START_OPTIONS))
    return {
        "status": "ok",
        "message": "Reset to defaults",
        "lead_sources": runtime_config.get_lead_sources(),
        "quick_start_options": runtime_config.get_quick_start_options(),
    }
