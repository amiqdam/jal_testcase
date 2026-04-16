"""
Global configuration for JAL Admissions AI System.
Loads environment variables and defines constants.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# --- Database ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./jal_admissions.db")

# --- App ---
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# --- Rate Limiting ---
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))

# --- Intent Classification Taxonomy (MECE Hierarchical) ---
INTENT_TAXONOMY = {
    "INQUIRY": {
        "description": "Pencarian informasi — user murni bertanya, belum melakukan aksi pendaftaran",
        "micro_intents": {
            "general_inquiry": "Pertanyaan FAQ tentang info institusi umum (lokasi, akreditasi, fasilitas)",
            "academic_inquiry": "Pertanyaan spesifik terkait proses belajar-mengajar (jurusan, kurikulum, ekskul)",
            "financial_inquiry": "Hal terkait uang dan kelayakan finansial (UKT, beasiswa, cicilan)",
        }
    },
    "TRANSACTIONAL": {
        "description": "Proses administratif — user sedang atau sudah melakukan aksi dalam funnel pendaftaran",
        "micro_intents": {
            "registration_process": "Pertanyaan teknis atau panduan langkah-langkah pendaftaran",
            "status_follow_up": "Permintaan update atas aksi yang sudah dilakukan sebelumnya",
        }
    },
    "SUPPORT": {
        "description": "Kendala dan keluhan — user punya niat tapi terhalang masalah",
        "micro_intents": {
            "technical_issue": "Kendala pada sistem (error, link rusak, VA gagal)",
            "general_complaint": "Keluhan terkait non-teknis IT (layanan, pelayanan, proses ribet)",
        }
    },
    "AMBIGUOUS": {
        "description": "Pesan tidak jelas — jaring pengaman agar AI tidak memaksakan klasifikasi",
        "micro_intents": {
            "greeting_unclear": "Pesan pembuka, terlalu pendek, emoji-only, 'halo min', 'P'",
        }
    },
}

# Flattened list of all valid micro intents
ALL_MICRO_INTENTS = []
for macro, details in INTENT_TAXONOMY.items():
    ALL_MICRO_INTENTS.extend(details["micro_intents"].keys())

ALL_MACRO_INTENTS = list(INTENT_TAXONOMY.keys())

# --- Funnel Stages (progressive, forward-only) ---
FUNNEL_STAGES = ["awareness", "interest", "consideration", "decision", "enrolled"]

# --- Urgency Levels (3 levels) ---
URGENCY_LEVELS = ["low", "medium", "critical"]

# --- Lead Sources ---
LEAD_SOURCES = [
    "formulir_pendaftaran",
    "media_sosial",
    "website",
    "event",
    "referral",
    "lainnya",
]

# --- Quick Start Options (pre-classifier) ---
QUICK_START_OPTIONS = [
    {"id": "info_prodi", "label": "📚 Info Program Studi", "macro_intent": "INQUIRY", "micro_intent": "academic_inquiry", "message": "Saya ingin tahu tentang program studi yang tersedia"},
    {"id": "biaya_beasiswa", "label": "💰 Biaya & Beasiswa", "macro_intent": "INQUIRY", "micro_intent": "financial_inquiry", "message": "Saya ingin bertanya tentang biaya kuliah dan beasiswa"},
    {"id": "cara_daftar", "label": "📝 Cara Mendaftar", "macro_intent": "TRANSACTIONAL", "micro_intent": "registration_process", "message": "Saya ingin tahu cara mendaftar"},
    {"id": "info_kampus", "label": "🏫 Info Kampus", "macro_intent": "INQUIRY", "micro_intent": "general_inquiry", "message": "Saya ingin tahu informasi umum tentang kampus"},
]

# --- Validation Thresholds ---
MIN_CONFIDENCE_THRESHOLD = 0.6
MAX_MESSAGE_LENGTH = 5000

# --- NBA (Next Best Action) Types ---
NBA_TYPES = [
    "auto_respond",
    "send_brochure",
    "invite_tour",
    "connect_alumni",
    "assign_counselor",
    "schedule_call",
    "fast_track",
    "escalate",
]


# --- Runtime Config (mutable at runtime via admin) ---
class RuntimeConfig:
    """Mutable configuration that can be updated via admin panel."""
    def __init__(self):
        self.lead_sources = list(LEAD_SOURCES)
        self.quick_start_options = list(QUICK_START_OPTIONS)
    
    def update_lead_sources(self, sources: list):
        self.lead_sources = sources
    
    def update_quick_start_options(self, options: list):
        self.quick_start_options = options
    
    def get_lead_sources(self) -> list:
        return self.lead_sources
    
    def get_quick_start_options(self) -> list:
        return self.quick_start_options


runtime_config = RuntimeConfig()
