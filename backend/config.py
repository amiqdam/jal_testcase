"""
Global configuration for JAL Admissions AI System.
Loads settings from environment variables with sensible defaults.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Database ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./jal_admissions.db")

# --- LLM Provider ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai | gemini | claude
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "2000"))

# --- App Settings ---
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# --- Intent Categories ---
INTENT_CATEGORIES = [
    "inquiry_prodi",
    "inquiry_biaya",
    "registration",
    "scholarship",
    "followup_status",
    "complaint",
    "ambiguous",
    "partnership",
]

# --- Funnel Stages (ordered: lowest → highest) ---
FUNNEL_STAGES = [
    "awareness",
    "interest",
    "consideration",
    "decision",
    "enrolled",
]

# --- Urgency Levels (ordered: lowest → highest) ---
URGENCY_LEVELS = [
    "low",
    "medium",
    "high",
    "critical",
]

# --- Quick-Start Pre-Classifier Options ---
QUICK_START_OPTIONS = [
    {
        "id": "info_prodi",
        "label": "📚 Info Program Studi",
        "intent": "inquiry_prodi",
        "message": "Saya ingin tahu tentang program studi yang tersedia",
    },
    {
        "id": "biaya_beasiswa",
        "label": "💰 Biaya & Beasiswa",
        "intent": "inquiry_biaya",
        "message": "Saya ingin bertanya tentang biaya kuliah dan beasiswa",
    },
    {
        "id": "cara_daftar",
        "label": "📝 Cara Mendaftar",
        "intent": "registration",
        "message": "Saya ingin tahu cara mendaftar",
    },
]

# --- Contact Type Mappings ---
CONTACT_TYPES = ["student", "parent", "counselor", "unknown"]

# --- Sentiment Categories ---
SENTIMENT_CATEGORIES = [
    "neutral",
    "anxious",
    "frustrated",
    "excited",
    "confused",
    "grateful",
]

# --- NBA Action Types ---
NBA_ACTION_TYPES = [
    "auto_respond",
    "send_brochure",
    "invite_tour",
    "connect_alumni",
    "assign_counselor",
    "schedule_call",
    "fast_track",
    "escalate",
]

# --- Message Validation ---
MAX_MESSAGE_LENGTH = 5000
MIN_CONFIDENCE_THRESHOLD = 0.6

# --- Retry Configuration ---
LLM_RETRY_COUNT = 3
LLM_RETRY_BACKOFF = [2, 4, 8]  # seconds
