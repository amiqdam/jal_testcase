"""
FastAPI entry point for JAL Admissions AI System.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.database.migrations import run_migrations
from backend.database.seed import seed_demo_data
from backend.api.chat import router as chat_router
from backend.api.leads import router as leads_router
from backend.api.dashboard import router as dashboard_router
from backend.api.responses import router as responses_router
from backend.api.admin_chat import router as admin_chat_router
from backend.api.categorization import router as categorization_router

app = FastAPI(
    title="JAL Admissions AI System",
    description="Sistem Otomasi Admisi Berbasis AI — PT Jangkar Arunika Luminara",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
app.include_router(leads_router, prefix="/api/leads", tags=["Leads"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(responses_router, prefix="/api/response", tags=["Responses"])
app.include_router(admin_chat_router, prefix="/api/admin", tags=["Admin Chat"])
app.include_router(categorization_router, prefix="/api/admin", tags=["Categorization"])

# Mount frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")


@app.on_event("startup")
async def startup_event():
    """Run migrations and seed data on startup."""
    run_migrations()
    seed_demo_data()
    print("🚀 JAL Admissions AI System started!")


@app.get("/")
async def serve_frontend():
    """Serve the main frontend page."""
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "JAL Admissions AI System API", "docs": "/docs"}


@app.get("/admin")
@app.get("/admin/{path:path}")
async def serve_admin(path: str = ""):
    """Serve the admin frontend page (all admin routes)."""
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Admin Dashboard", "docs": "/docs"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "system": "JAL Admissions AI"}
