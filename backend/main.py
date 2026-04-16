"""
JAL Admissions AI System — FastAPI Application Entry Point.
Multi-agent LangGraph pipeline for university admissions automation.
"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api import chat, admin_chat, categorization, dashboard, leads, responses, admin_export, admin_complaints
from backend.database.migrations import run_migrations
from backend.database.seed import seed_data

app = FastAPI(
    title="JAL Admissions AI",
    description="AI-powered university admissions automation system with LangGraph multi-agent pipeline",
    version="2.0.0",
)

# --- API Routes ---
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])
app.include_router(admin_chat.router, prefix="/api/admin/chat", tags=["Admin Chat"])
app.include_router(categorization.router, prefix="/api/categorization", tags=["Categorization"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(leads.router, prefix="/api/leads", tags=["Leads"])
app.include_router(responses.router, prefix="/api/responses", tags=["Responses"])
app.include_router(admin_export.router, prefix="/api/admin/export", tags=["Export"])
app.include_router(admin_complaints.router, prefix="/api/admin/complaints", tags=["Complaints"])

# --- Static Files ---
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_dir, "index.html"))


# --- Startup Event ---
@app.on_event("startup")
async def startup():
    """Run database migrations and seed data on startup."""
    # Delete old database to apply new schema
    db_path = "jal_admissions.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️ Old database removed (schema change).")
    
    run_migrations()
    seed_data()
    print("🚀 JAL Admissions AI System v2.0 started!")
    print("   → LangGraph Multi-Agent Pipeline: Classifier → Profiler → Funnel Stager → Response → NBA")
