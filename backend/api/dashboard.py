"""
Dashboard API — summary stats, funnel data, and analytics.
"""
from fastapi import APIRouter
from backend.services.lead_service import LeadService
from backend.config import runtime_config

router = APIRouter()
lead_service = LeadService()


@router.get("/summary")
async def dashboard_summary():
    """Get dashboard overview statistics."""
    return lead_service.get_dashboard_summary()


@router.get("/config")
async def get_config():
    """Get client-side configuration (quick start options, lead sources) — uses runtime config."""
    sources = runtime_config.get_lead_sources()
    source_labels = {
        "formulir_pendaftaran": "📋 Formulir Pendaftaran",
        "media_sosial": "📱 Media Sosial",
        "website": "🌐 Website",
        "event": "🎓 Event",
        "referral": "👥 Referral (Teman/Keluarga)",
        "lainnya": "📌 Lainnya",
    }
    return {
        "quick_start_options": runtime_config.get_quick_start_options(),
        "lead_sources": [
            {"id": s, "label": source_labels.get(s, f"📌 {s.replace('_', ' ').title()}")}
            for s in sources
        ],
    }
