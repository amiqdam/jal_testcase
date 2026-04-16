"""
Admin Export API — export leads data as JSON or CSV.
"""
import csv
import io
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from backend.services.lead_service import LeadService

router = APIRouter()
lead_service = LeadService()


@router.get("/leads")
async def export_leads_json():
    """Export all leads as JSON (Pandas DataFrame-ready)."""
    leads = lead_service.export_leads_data()
    return {"data": leads, "total": len(leads)}


@router.get("/leads/csv")
async def export_leads_csv():
    """Export all leads as CSV file download."""
    leads = lead_service.export_leads_data()
    
    if not leads:
        return StreamingResponse(
            io.StringIO("No data"),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=jal_leads_export.csv"}
        )
    
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=leads[0].keys())
    writer.writeheader()
    writer.writerows(leads)
    
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=jal_leads_export.csv"}
    )
