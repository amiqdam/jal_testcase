"""
Dashboard API — summary stats, funnel data, and analytics.
"""
from fastapi import APIRouter
from backend.services.lead_service import LeadService
from backend.config import QUICK_START_OPTIONS

router = APIRouter()
lead_service = LeadService()


@router.get("/summary")
async def dashboard_summary():
    """Get dashboard overview statistics."""
    return lead_service.get_dashboard_summary()


@router.get("/config")
async def get_config():
    """Get client-side configuration (quick start options, etc)."""
    return {
        "quick_start_options": QUICK_START_OPTIONS,
        "lead_sources": [
            {"id": "formulir_pendaftaran", "label": "📋 Formulir Pendaftaran"},
            {"id": "media_sosial", "label": "📱 Media Sosial"},
            {"id": "website", "label": "🌐 Website"},
            {"id": "event", "label": "🎓 Event"},
            {"id": "referral", "label": "👥 Referral (Teman/Keluarga)"},
            {"id": "lainnya", "label": "📌 Lainnya"},
        ]
    }
