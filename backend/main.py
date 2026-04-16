"""
JAL Admissions AI System — FastAPI Application Entry Point.
Multi-agent LangGraph pipeline for university admissions automation.
"""
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.api import chat, admin_chat, categorization, dashboard, leads, responses, admin_export, admin_complaints, knowledge_base_api, scenario
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
app.include_router(knowledge_base_api.router, prefix="/api/admin/knowledge", tags=["Knowledge Base"])
app.include_router(scenario.router, prefix="/api/admin/scenarios", tags=["Scenarios"])

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
    run_migrations()
    
    # Safe schema evolution — add new columns if they don't exist (preserves data)
    _safe_add_columns()
    
    seed_data()
    print("🚀 JAL Admissions AI System v2.0 started!")
    print("   → LangGraph Multi-Agent Pipeline: Classifier → Profiler → Funnel Stager → Response → NBA")


def _safe_add_columns():
    """Add new columns to existing tables without dropping data."""
    import sqlite3
    from backend.database.connection import get_db
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Get existing columns in leads table
    cursor.execute("PRAGMA table_info(leads)")
    existing_cols = {row["name"] for row in cursor.fetchall()}
    
    # Columns to ensure exist (added over time)
    new_columns = {
        "phone_number": "TEXT",
        "tanggal_lahir": "TEXT",
    }
    
    for col_name, col_type in new_columns.items():
        if col_name not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_type}")
                print(f"  ➕ Added column: leads.{col_name} ({col_type})")
            except Exception:
                pass  # Column already exists
    
    conn.commit()
    conn.close()
