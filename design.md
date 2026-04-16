# Design Document: JAL Admissions AI System

## Fitur: Sistem Otomasi Admisi Berbasis AI — PT Jangkar Arunika Luminara

---

## 1. Overview

Sistem ini adalah platform AI end-to-end yang menerima pesan calon mahasiswa melalui chatbot bergaya WhatsApp, memproses setiap pesan melalui pipeline AI (klasifikasi, profiling, funnel staging, response generation), dan menghasilkan output berupa dashboard admisi yang siap digunakan oleh tim non-teknis.

### Tujuan Utama

- Mengintegrasikan data leads dari berbagai kanal ke dalam satu sistem terpusat
- Memberikan respons dan rekomendasi yang dipersonalisasi untuk setiap calon mahasiswa
- Meningkatkan conversion rate melalui automated follow-up dan next-best-action recommendations
- Menyediakan full observability atas proses pengambilan keputusan AI

### Batasan Desain

- Sistem berjalan sebagai web application (monorepo: backend + frontend)
- Penyimpanan menggunakan PostgreSQL (atau SQLite untuk demo cepat)
- LLM menggunakan external API (OpenAI GPT-4 / Gemini / Claude) untuk klasifikasi dan response generation
- Chatbot adalah simulasi messaging — bukan integrasi WhatsApp/Telegram sesungguhnya
- Bahasa: Bahasa Indonesia dan English (bilingual)

---

## 2. Arsitektur

### 2.1 Diagram Arsitektur High-Level

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     JAL Admissions AI System                             │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │                    Layer 1: INPUT (Dual-Mode)                        │ │
│  │                                                                      │ │
│  │   ┌── Mode A: User-Facing (/user) ──────────────────────────────┐   │ │
│  │   │  ┌─────────────┐   ┌──────────────┐                        │   │ │
│  │   │  │ Chatbot UI  │   │ Quick-Start  │  (3 opsi klik-able     │   │ │
│  │   │  │ (WhatsApp   │   │ Pre-Classif. │   → bantu kategorisasi │   │ │
│  │   │  │  style)     │   │ Options      │   → jika skip, LLM     │   │ │
│  │   │  └──────┬──────┘   └──────┬───────┘      classify sendiri) │   │ │
│  │   └─────────┼─────────────────┼─────────────────────────────────┘   │ │
│  │             │                 │                                     │ │
│  │   ┌── Mode B: Admin-Facing (/admin) ────────────────────────────┐   │ │
│  │   │  ┌─────────────┐   ┌──────────────┐   ┌────────────────┐   │   │ │
│  │   │  │ Chat Monitor│   │ Manual       │   │ Categorization │   │   │ │
│  │   │  │ (view all   │   │ Intervention │   │ Dashboard      │   │   │ │
│  │   │  │  user chats)│   │ (reply to    │   │ (table + chart)│   │   │ │
│  │   │  └──────┬──────┘   │  escalated)  │   └───────┬────────┘   │   │ │
│  │   │         │          └──────┬───────┘           │            │   │ │
│  │   └─────────┼─────────────────┼───────────────────┼────────────┘   │ │
│  │             │                 │                   │                │ │
│  │             ▼                 ▼                   │                │ │
│  │       ┌──────────────┐  ┌──────────────┐          │                │ │
│  │       │ WebSocket    │  │ Message      │          │                │ │
│  │       │ Server       │  │ Ingestion API│          │                │ │
│  │       └──────┬───────┘  └──────┬───────┘          │                │ │
│  │              └────────┬────────┘                   │                │ │
│  │                       ▼                            ▼                │ │
│  │              ┌────────────────┐   ┌──────────────────────────┐     │ │
│  │              │ Message Store  │──▶│ Categorization Query API │     │ │
│  │              └────────────────┘   └──────────────────────────┘     │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                         │                │
│  ┌─────────────────────────────────────────────────────│──────────────┐ │
│  │                    Layer 2: PROCESSING               │              │ │
│  │                                                      ▼              │ │
│  │   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐      │ │
│  │   │ Language  │──▶│ Intent   │──▶│ Entity   │──▶│ Funnel   │      │ │
│  │   │ Detection │   │ Classif. │   │ Extract  │   │ Staging  │      │ │
│  │   └──────────┘   └──────────┘   └──────────┘   └────┬─────┘      │ │
│  │                                                      │            │ │
│  │   ┌──────────┐   ┌──────────┐   ┌──────────────┐    │            │ │
│  │   │ NBA      │◀──│ Response │◀──│ Urgency      │◀───┘            │ │
│  │   │ Engine   │   │ Gen.     │   │ Scoring      │                  │ │
│  │   └────┬─────┘   └──────────┘   └──────────────┘                  │ │
│  │        │                                                          │ │
│  │   ┌────▼──────────────────────────────────────┐                   │ │
│  │   │ Observability: Processing Log per message │                   │ │
│  │   │ (step, result, confidence, reasoning)     │                   │ │
│  │   └───────────────────────────────────────────┘                   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                              │                                         │
│  ┌───────────────────────────│───────────────────────────────────────┐ │
│  │                    Layer 3: OUTPUT                                 │ │
│  │        ┌──────────────────┼───────────────────┐                   │ │
│  │        ▼                  ▼                   ▼                   │ │
│  │  ┌───────────┐   ┌──────────────┐   ┌─────────────────┐         │ │
│  │  │ Admin     │   │ Lead DB      │   │ Analytics &     │         │ │
│  │  │ Dashboard │   │ (Classified) │   │ Reports         │         │ │
│  │  └───────────┘   └──────────────┘   └─────────────────┘         │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                     DATA LAYER                                     │ │
│  │  ┌─────────────┐   ┌──────────┐   ┌──────────────────────┐       │ │
│  │  │ PostgreSQL  │   │ Knowledge│   │ LLM API              │       │ │
│  │  │ / SQLite    │   │ Base     │   │ (OpenAI/Gemini/Claude)│       │ │
│  │  └─────────────┘   └──────────┘   └──────────────────────┘       │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Diagram Alur Data (Data Flow)

```
=== FLOW A: User-Facing ===

[Calon Mahasiswa / Orang Tua / Guru BK]
      │
      ├──▶ [Quick-Start Options] ──▶ user klik salah satu dari 3 opsi
      │         │                      → otomatis submit sebagai pesan
      │         │                      → intent pre-classified dari opsi
      │         ▼
      └──▶ [Free-Text Input] ──▶ user ketik pesan sendiri
                │                  → LLM classify intent + profiling
                ▼
[Chatbot UI (WhatsApp-style)]
      │
      │ WebSocket / HTTP POST
      ▼
[Message Ingestion API]
      │
      │ save raw message ke database
      │ flag: has_quick_start_hint = true/false
      ▼
[AI Processing Pipeline]
      │
      ├──▶ [1. Language Detection] ──▶ "id" / "en" / "mixed"
      ├──▶ [2. Intent Classification] ──▶ jika quick-start → use hint, jika free-text → LLM classify
      ├──▶ [3. Entity Extraction] ──▶ {name, school, program, ...}
      ├──▶ [4. Sentiment Analysis] ──▶ "anxious" / "frustrated" / "neutral"
      ├──▶ [5. Funnel Staging] ──▶ "awareness" / "interest" / ... / "enrolled"
      ├──▶ [6. Urgency Scoring] ──▶ "low" / "medium" / "high" / "critical"
      │
      │ all steps logged to processing_log JSONB
      ▼
[Response & Action Generation]
      │
      ├──▶ [Draft Response] ──▶ personalized, language-matched
      ├──▶ [Next Best Action] ──▶ for admissions team
      └──▶ [Profile Update] ──▶ lead profile enriched
      │
      │ save all outputs to database
      ▼
[Admin Dashboard + Lead Database + Analytics]


=== FLOW B: Admin-Facing ===

[Admin / Staff Admisi]
      │
      │ akses /admin
      ▼
[Admin Interface — Split View]
      │
      ├──▶ [Chat Monitor Panel]
      │         │
      │         ├── Lihat semua user conversations (real-time)
      │         ├── Pilih conversation untuk di-view
      │         └── Manual reply (intervensi) ke user tertentu
      │                │
      │                ▼
      │         [Admin Reply → Message Ingestion API]
      │                │
      │                └── direction: outbound, sender: admin
      │
      └──▶ [Categorization Dashboard Panel]
                │
                ├── [Sortable/Filterable Table]
                │     └── Kolom: Timestamp, Sender, Message, Intent,
                │              Funnel Stage, Urgency, Sentiment, Confidence
                │
                └── [Dynamic Visualizations] ← reactive to active filters
                      ├── Intent Distribution (Bar Chart)
                      ├── Funnel Distribution (Pie/Donut)
                      ├── Urgency Breakdown (Stacked Bar)
                      └── Chat Volume Timeline (Line Chart)
```

### 2.3 Komponen Sistem

| Komponen | Layer | Tanggung Jawab |
|----------|-------|----------------|
| **User Chatbot UI** | Input (User) | Interface percakapan WhatsApp-style, bilingual, dengan quick-start pre-classifier |
| **Quick-Start Options** | Input (User) | 3 opsi klik-able untuk bantu kategorisasi awal intent |
| **Admin Chat Monitor** | Input (Admin) | View semua user conversations, pilih chat, manual intervention |
| **Admin Categorization Dashboard** | Input (Admin) | Tabel sortable/filterable + visualisasi dinamis per kategori chat |
| **Message API** | Input | Terima pesan (user + admin reply), validasi, simpan ke DB |
| **Categorization Query API** | Input (Admin) | Endpoint filter/sort/aggregate data chat untuk tabel + chart |
| **AI Pipeline** | Processing | Klasifikasi, profiling, staging, scoring |
| **Response Engine** | Processing | Generate respons personalisasi via LLM |
| **NBA Engine** | Processing | Tentukan next best action untuk tim admisi |
| **Observability Logger** | Processing | Catat reasoning setiap step pipeline |
| **Admin Dashboard** | Output | UI untuk tim admisi melihat leads & analytics |
| **Knowledge Base** | Data | Info kampus (prodi, biaya, beasiswa) untuk LLM context |

---

## 3. Komponen dan Interface

### 3.1 Struktur Folder Proyek

```
jal_admissions_ai/
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Konfigurasi global (DB, API keys, dll.)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py              # POST /api/chat/send, GET /api/chat/:leadId
│   │   ├── leads.py             # GET /api/leads, GET /api/leads/:id
│   │   ├── dashboard.py         # GET /api/dashboard/summary, funnel, analytics
│   │   └── responses.py         # POST /api/response/:id/approve, PATCH edit
│   │
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── processor.py         # MessageProcessor — orchestrates pipeline
│   │   ├── language_detector.py # LanguageDetector
│   │   ├── intent_classifier.py # IntentClassifier
│   │   ├── entity_extractor.py  # EntityExtractor
│   │   ├── sentiment_analyzer.py# SentimentAnalyzer
│   │   ├── funnel_stager.py     # FunnelStager
│   │   ├── urgency_scorer.py    # UrgencyScorer
│   │   ├── response_generator.py# ResponseGenerator — personalized drafts
│   │   └── nba_engine.py        # NextBestActionEngine
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── lead.py              # Lead SQLAlchemy/Pydantic model
│   │   ├── message.py           # Message model
│   │   ├── draft_response.py    # DraftResponse model
│   │   ├── next_action.py       # NextAction model
│   │   └── processing_log.py    # ProcessingLog model
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm_service.py       # LLMService — wrapper OpenAI/Gemini/Claude
│   │   ├── knowledge_base.py    # KnowledgeBase — campus info untuk LLM context
│   │   └── lead_service.py      # LeadService — CRUD + business logic leads
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py        # Database connection setup
│   │   ├── migrations.py        # Schema setup / migrations
│   │   └── seed.py              # Seed data: knowledge base + sample leads
│   │
│   └── tests/
│       ├── test_pipeline.py     # Test AI processing pipeline
│       ├── test_api.py          # Test API endpoints
│       └── test_scenarios.py    # Test 17 skenario realistis
│
├── frontend/
│   ├── index.html               # Entry point
│   ├── style.css                # Global styles + design system
│   ├── app.js                   # Main app logic + routing
│   │
│   ├── pages/
│   │   ├── chatbot.js           # User-facing chatbot page (calon mahasiswa)
│   │   ├── admin-chat.js        # Admin-facing chat monitor + intervention
│   │   ├── dashboard.js         # Admin dashboard (overview + leads)
│   │   ├── lead-detail.js       # Individual lead detail view
│   │   └── analytics.js         # Analytics & reports page
│   │
│   ├── components/
│   │   ├── chat-bubble.js       # Chat bubble component (shared user + admin)
│   │   ├── quick-start-options.js # Quick-start pre-classifier (3 opsi klik-able)
│   │   ├── chat-category-table.js # Admin: sortable/filterable categorization table
│   │   ├── dynamic-charts.js    # Admin: reactive Chart.js visualizations
│   │   ├── lead-table.js        # Lead management table
│   │   ├── funnel-chart.js      # Funnel visualization
│   │   ├── processing-log.js    # Processing log viewer
│   │   ├── urgency-badge.js     # Color-coded urgency badge
│   │   └── stat-card.js         # Dashboard stat card
│   │
│   └── assets/
│       └── ...                  # Icons, images
│
├── knowledge_base/
│   └── campus_info.json         # Program studi, biaya, beasiswa, FAQ
│
├── docker-compose.yml           # PostgreSQL + App
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
└── README.md                    # Setup & run instructions
```

### 3.2 Interface Komponen Utama

#### MessageProcessor (Pipeline Orchestrator)

```python
class MessageProcessor:
    """Orchestrates the entire AI processing pipeline for each message."""
    
    def __init__(self, llm_service: LLMService, knowledge_base: KnowledgeBase):
        self.llm = llm_service
        self.kb = knowledge_base
        self.language_detector = LanguageDetector()
        self.intent_classifier = IntentClassifier(llm_service)
        self.entity_extractor = EntityExtractor(llm_service)
        self.sentiment_analyzer = SentimentAnalyzer(llm_service)
        self.funnel_stager = FunnelStager()
        self.urgency_scorer = UrgencyScorer()
        self.response_generator = ResponseGenerator(llm_service, knowledge_base)
        self.nba_engine = NextBestActionEngine()
    
    async def process(self, message: Message, lead: Lead) -> ProcessingResult:
        """
        Process a single message through the full pipeline.
        Returns ProcessingResult containing all outputs + processing_log.
        """
    
    def _build_processing_log(self, steps: list[StepResult]) -> dict:
        """Build structured processing log with reasoning for each step."""
```

#### LLMService (LLM Wrapper)

```python
class LLMService:
    """Abstraction layer for LLM API calls. Supports OpenAI, Gemini, Claude."""
    
    async def analyze_message(self, message: str, lead_profile: dict, 
                               knowledge_context: str) -> AnalysisResult:
        """
        Single-pass LLM call that returns structured analysis:
        language, intent, entities, sentiment, funnel_stage, urgency.
        Uses JSON mode / structured output.
        """
    
    async def generate_response(self, message: str, lead_profile: dict,
                                 analysis: AnalysisResult, 
                                 knowledge_context: str) -> str:
        """Generate personalized response draft based on full context."""
    
    async def generate_nba(self, lead_profile: dict, 
                            analysis: AnalysisResult) -> NextBestAction:
        """Generate next best action recommendation for admissions team."""
```

#### KnowledgeBase

```python
class KnowledgeBase:
    """Campus information provider for LLM context injection."""
    
    def __init__(self, data_path: str = "knowledge_base/campus_info.json"):
        self.data = self._load(data_path)
    
    def get_context(self, intent: str, program: str = None) -> str:
        """
        Return relevant campus info based on detected intent.
        e.g., intent="scholarship" → return beasiswa info section.
        """
    
    def get_program_info(self, program_name: str) -> dict:
        """Return specific program details (curriculum, biaya, prospek)."""
    
    def get_faq(self, topic: str) -> list[dict]:
        """Return FAQ entries relevant to the topic."""
```

#### LeadService

```python
class LeadService:
    """Business logic for lead management."""
    
    async def get_or_create_lead(self, session_id: str) -> Lead:
        """Get existing lead by session or create new one."""
    
    async def update_profile(self, lead_id: str, extracted_entities: dict) -> Lead:
        """Incrementally update lead profile with new extracted entities."""
    
    async def update_funnel_stage(self, lead_id: str, stage: str, 
                                   urgency: str) -> Lead:
        """Update lead's funnel stage and urgency level."""
    
    async def get_leads_filtered(self, stage: str = None, urgency: str = None,
                                  page: int = 1, limit: int = 20) -> list[Lead]:
        """Get filtered and paginated list of leads."""
    
    async def get_dashboard_summary(self) -> DashboardSummary:
        """Aggregate stats for dashboard overview."""
```

---

## 3.3 Layer 1 Detail Design — Dual-Mode Interface

### 3.3.1 Quick-Start Pre-Classifier (Shared: User + Admin Chatbot)

Saat user pertama kali membuka chatbot, ditampilkan welcome message + **3 opsi klik-able** sebagai pre-classifier:

| Opsi | Label Display | Pre-classified Intent | Pesan yang Dikirim |
|------|--------------|----------------------|--------------------|
| 1 | 📚 Info Program Studi | `inquiry_prodi` | "Saya ingin tahu tentang program studi yang tersedia" |
| 2 | 💰 Biaya & Beasiswa | `inquiry_biaya` + `scholarship` | "Saya ingin bertanya tentang biaya kuliah dan beasiswa" |
| 3 | 📝 Cara Mendaftar | `registration` | "Saya ingin tahu cara mendaftar" |

**Behavior:**
- Klik salah satu → opsi menghilang → pesan muncul di chat bubble → auto-submit ke backend
- Backend menerima pesan dengan metadata `quick_start_intent` → pipeline SKIP intent classification step (confidence = 1.0) → langsung proceed ke entity extraction dst.
- Jika user TIDAK klik (langsung ketik pesan sendiri) → opsi menghilang → LLM classify intent secara normal
- Quick-start options hanya muncul di awal conversation (pesan pertama)

```
┌─────────────────────────────────────────┐
│  💬 Selamat datang di JAL Admissions!   │
│                                         │
│  Pilih topik atau ketik pesan langsung: │
│                                         │
│  ┌─────────────────────────────┐        │
│  │ 📚 Info Program Studi       │        │
│  └─────────────────────────────┘        │
│  ┌─────────────────────────────┐        │
│  │ 💰 Biaya & Beasiswa         │        │
│  └─────────────────────────────┘        │
│  ┌─────────────────────────────┐        │
│  │ 📝 Cara Mendaftar           │        │
│  └─────────────────────────────┘        │
│                                         │
│  ┌──────────────────────────┐ [Send]    │
│  │ Ketik pesan...            │          │
│  └──────────────────────────┘           │
└─────────────────────────────────────────┘
```

### 3.3.2 Admin Chat Monitor & Manual Intervention

Admin mode (`/admin`) menampilkan semua percakapan user dalam satu view. Admin bisa:

1. **Lihat daftar conversations** — list semua active sessions dengan preview pesan terakhir
2. **Pilih conversation** — klik untuk buka full chat history
3. **Manual intervention** — ketik dan kirim balasan langsung ke user yang dipilih

**Kapan admin perlu intervene:**
- Pertanyaan terlalu kompleks untuk AI (butuh keputusan manusia)
- AI confidence rendah (< 0.6) → ditandai dengan badge "Needs Review"
- User secara eksplisit minta bicara dengan manusia
- Urgency = critical (complaint, follow-up tidak direspons)

**Data model untuk admin reply:**
```
messages tabel:
  direction: "outbound"
  content: [admin reply text]
  processing_log: {"source": "admin_manual", "admin_id": "admin"}
```

**Layout Admin — Split View (Desktop):**
```
┌───────────────────────────────┬────────────────────────────────────────┐
│  📋 Chat List                 │  💬 Chat Detail                       │
│                               │                                        │
│  ┌─────────────────────────┐  │  [User Chatbot view — read + reply]   │
│  │ 🔴 Putri Ayu            │  │                                        │
│  │ "Website error terus.." │  │  ┌──────────┐                         │
│  │ 10:30 • critical        │  │  │ Putri:    │                         │
│  └─────────────────────────┘  │  │ "Website  │                         │
│  ┌─────────────────────────┐  │  │  error.." │                         │
│  │ 🟡 Ahmad Rizky          │  │  └──────────┘                         │
│  │ "Ada beasiswa ga?"      │  │        ┌──────────┐                   │
│  │ 10:28 • medium          │  │        │ AI Reply │                   │
│  └─────────────────────────┘  │        │ "Halo.." │                   │
│  ┌─────────────────────────┐  │        └──────────┘                   │
│  │ 🟢 Sarah Lee            │  │                                        │
│  │ "I'd like to apply"     │  │  ⚠️ Needs admin intervention          │
│  │ 10:25 • high            │  │                                        │
│  └─────────────────────────┘  │  ┌──────────────────────────┐ [Send]  │
│                               │  │ Reply sebagai admin...    │         │
│  [Search conversations...]    │  └──────────────────────────┘         │
└───────────────────────────────┴────────────────────────────────────────┘
```

### 3.3.3 Categorization Dashboard (Admin Only)

Panel tambahan di admin mode yang menampilkan **semua pesan masuk** dalam format tabel + chart.

#### Tabel Kategorisasi

| Kolom | Sortable | Filterable | Deskripsi |
|-------|----------|------------|-----------|
| Timestamp | ✅ (asc/desc) | ✅ (date range) | Waktu pesan masuk |
| Sender | ✅ | ✅ (search) | Nama/session lead |
| Message Preview | ❌ | ✅ (search) | Preview 50 chars |
| Intent | ✅ | ✅ (dropdown multi-select) | Kategori intent |
| Funnel Stage | ✅ | ✅ (dropdown multi-select) | Tahap funnel |
| Urgency | ✅ | ✅ (dropdown multi-select) | Level urgensi |
| Sentiment | ✅ | ✅ (dropdown) | Sentimen terdeteksi |
| Confidence | ✅ | ✅ (range slider) | Skor kepercayaan AI |

#### Visualisasi Dinamis (Reactive to Filters)

Semua chart menggunakan **Chart.js** dan update secara reaktif ketika filter/sort berubah.

| Chart | Tipe | Keterangan |
|-------|------|------------|
| Intent Distribution | Horizontal Bar | Jumlah pesan per kategori intent (dari data ter-filter) |
| Funnel Distribution | Pie/Donut | Proporsi leads per funnel stage (dari data ter-filter) |
| Urgency Breakdown | Stacked Bar | Distribusi urgency level (dari data ter-filter) |
| Chat Volume Timeline | Line Chart | Volume chat per waktu — jam/hari (dari data ter-filter) |

**Reactive data flow:**
```
Filter Change → Re-query API dengan filter params
               → Update tabel data
               → Re-render semua chart dengan filtered dataset
               → Chart label + title menunjukkan filter aktif
```

**Layout — Categorization Panel:**
```
┌──────────────────────────────────────────────────────────────────────────┐
│  📊 Chat Categorization                                              │
│                                                                      │
│  [Filter: Intent ▼] [Funnel ▼] [Urgency ▼] [🔍 Search: ________]   │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ ⇕ Time   │ ⇕ Sender  │ Message      │ ⇕ Intent  │ ⇕ Funnel │  │  │
│  │──────────│──────────│──────────────│──────────│──────────│   │  │
│  │ 10:30    │ Putri    │ Website err..│ complaint │ decision │   │  │
│  │ 10:28    │ Ahmad    │ Ada beasisw..│ scholarsh │ interest │   │  │
│  │ 10:25    │ Sarah    │ I'd like to..│ registrat │ decision │   │  │
│  │ ...      │ ...      │ ...          │ ...       │ ...      │   │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌─────────────────────────┐  ┌─────────────────────────┐           │
│  │ Intent Distribution     │  │ Funnel Distribution     │           │
│  │ ████████ inquiry_prodi  │  │     ┌───┐               │           │
│  │ █████ scholarship       │  │  ┌──┤   ├──┐            │           │
│  │ ███ registration        │  │  │  └───┘  │            │           │
│  │ █ complaint             │  │  └─────────┘            │           │
│  └─────────────────────────┘  └─────────────────────────┘           │
│  ┌─────────────────────────┐  ┌─────────────────────────┐           │
│  │ Urgency Breakdown       │  │ Chat Volume Timeline    │           │
│  │ ▓▓▓ low    ▒▒ med       │  │     /\    /\            │           │
│  │ ░░ high   ■ critical   │  │    /  \  /  \           │           │
│  │                         │  │ \_/    \/    \_         │           │
│  └─────────────────────────┘  └─────────────────────────┘           │
└──────────────────────────────────────────────────────────────────────────┘
```

### 3.3.4 API Endpoints untuk Layer 1 Admin Features

```python
# Chat Monitor API
class ChatMonitorAPI:
    """Endpoints untuk admin chat monitoring dan intervention."""
    
    # GET /api/admin/conversations — list semua active conversations
    # Response: [{lead_id, lead_name, last_message_preview, last_timestamp, 
    #             urgency, needs_review: bool}]
    
    # GET /api/admin/conversations/:leadId — full chat history
    # Response: {lead_profile, messages: [{direction, content, timestamp, sender}]}
    
    # POST /api/admin/conversations/:leadId/reply — admin manual intervention
    # Body: {content: "admin reply text"}
    # Response: {message_id, timestamp}

# Categorization Query API
class CategorizationQueryAPI:
    """Endpoints untuk tabel dan chart data."""
    
    # GET /api/admin/categorization — filtered/sorted messages for table
    # Query params: intent, funnel_stage, urgency, sentiment,
    #               confidence_min, confidence_max, date_from, date_to,
    #               search, sort_by, sort_order, page, limit
    # Response: {data: [{timestamp, sender, message_preview, intent, 
    #                     funnel_stage, urgency, sentiment, confidence}],
    #            total: int, page: int}
    
    # GET /api/admin/categorization/stats — aggregated stats for charts
    # Query params: same filters as above (excluding sort/page)
    # Response: {intent_distribution: {...}, funnel_distribution: {...},
    #            urgency_breakdown: {...}, volume_timeline: [{date, count}]}
```

---

## 4. Data Models

### 4.1 Database Schema — PostgreSQL/SQLite

```sql
-- Tabel utama: leads (calon mahasiswa)
CREATE TABLE leads (
    id              TEXT PRIMARY KEY,        -- UUID
    session_id      TEXT UNIQUE NOT NULL,    -- browser session identifier
    name            TEXT,
    contact_type    TEXT DEFAULT 'unknown',  -- student | parent | counselor | unknown
    language_pref   TEXT DEFAULT 'id',       -- id | en | mixed
    school_origin   TEXT,
    school_type     TEXT,                    -- SMA | SMK | MA | International | null
    interested_program TEXT,
    nationality     TEXT,
    academic_achievement TEXT,
    financial_concern BOOLEAN DEFAULT FALSE,
    funnel_stage    TEXT DEFAULT 'awareness', -- awareness|interest|consideration|decision|enrolled
    urgency         TEXT DEFAULT 'low',      -- low|medium|high|critical
    conversion_probability REAL DEFAULT 0.0,
    profile_json    TEXT,                    -- JSONB: additional flexible profile data
    assigned_counselor TEXT,
    channel         TEXT DEFAULT 'chatbot',  -- chatbot | whatsapp | form | event | referral
    tags            TEXT,                    -- JSON array of tags
    created_at      TEXT NOT NULL,           -- ISO 8601
    updated_at      TEXT NOT NULL
);

CREATE INDEX idx_leads_funnel ON leads(funnel_stage);
CREATE INDEX idx_leads_urgency ON leads(urgency);
CREATE INDEX idx_leads_created ON leads(created_at);

-- Tabel messages: semua pesan masuk dan keluar
CREATE TABLE messages (
    id              TEXT PRIMARY KEY,        -- UUID
    lead_id         TEXT NOT NULL REFERENCES leads(id),
    direction       TEXT NOT NULL,           -- inbound | outbound
    content         TEXT NOT NULL,
    language        TEXT,                    -- id | en | mixed
    intent          TEXT,                    -- detected intent
    intent_confidence REAL,
    sentiment       TEXT,                    -- anxious | frustrated | neutral | excited | ...
    processing_log  TEXT,                    -- JSONB: full reasoning trace
    processing_time_ms INTEGER,
    created_at      TEXT NOT NULL
);

CREATE INDEX idx_messages_lead ON messages(lead_id);
CREATE INDEX idx_messages_intent ON messages(intent);

-- Tabel draft responses: respons yang di-generate AI
CREATE TABLE draft_responses (
    id              TEXT PRIMARY KEY,
    message_id      TEXT NOT NULL REFERENCES messages(id),
    lead_id         TEXT NOT NULL REFERENCES leads(id),
    content         TEXT NOT NULL,
    personalization_signals TEXT,            -- JSONB: signals used for personalization
    status          TEXT DEFAULT 'pending',  -- pending | approved | sent | edited
    edited_content  TEXT,                    -- if admin edited before sending
    created_at      TEXT NOT NULL
);

CREATE INDEX idx_drafts_lead ON draft_responses(lead_id);
CREATE INDEX idx_drafts_status ON draft_responses(status);

-- Tabel next actions: rekomendasi aksi untuk tim admisi
CREATE TABLE next_actions (
    id              TEXT PRIMARY KEY,
    lead_id         TEXT NOT NULL REFERENCES leads(id),
    action_type     TEXT NOT NULL,           -- auto_respond | send_brochure | assign_counselor | schedule_call | escalate | ...
    action_detail   TEXT NOT NULL,
    priority        TEXT DEFAULT 'medium',   -- low | medium | high | critical
    reasoning       TEXT,                    -- why this action was recommended
    due_at          TEXT,                    -- ISO 8601, when action should be completed
    completed_at    TEXT,
    created_at      TEXT NOT NULL
);

CREATE INDEX idx_actions_lead ON next_actions(lead_id);
CREATE INDEX idx_actions_priority ON next_actions(priority);
CREATE INDEX idx_actions_due ON next_actions(due_at);
```

### 4.2 Knowledge Base Schema — JSON

File disimpan di `knowledge_base/campus_info.json`.

```json
{
  "university": {
    "name": "Universitas Luminara",
    "tagline": "Membentuk Pemimpin Masa Depan",
    "accreditation": "Unggul (A)",
    "location": "Jakarta Selatan"
  },
  "programs": [
    {
      "id": "ti",
      "name": "Teknik Informatika",
      "faculty": "Fakultas Ilmu Komputer",
      "degree": "S1",
      "accreditation": "A",
      "duration_semesters": 8,
      "total_credits": 144,
      "description": "Program studi yang mempelajari ...",
      "career_prospects": ["Software Engineer", "Data Scientist", "..."],
      "tuition_per_semester": 12500000,
      "registration_fee": 5000000,
      "curriculum_highlights": ["AI & Machine Learning", "..."]
    }
  ],
  "scholarships": [
    {
      "id": "beasiswa_prestasi",
      "name": "Beasiswa Prestasi Akademik",
      "type": "merit_based",
      "discount_range": "25-100%",
      "requirements": ["Nilai rapor rata-rata ≥ 85", "..."],
      "quota": 50
    },
    {
      "id": "kip_kuliah",
      "name": "KIP Kuliah",
      "type": "need_based",
      "coverage": "100% biaya kuliah + bantuan biaya hidup",
      "requirements": ["SKTM dari kelurahan", "..."]
    }
  ],
  "registration": {
    "intake_periods": ["Gelombang 1: Jan-Mar", "Gelombang 2: Apr-Jun", "Gelombang 3: Jul-Sep"],
    "requirements": {
      "general": ["Ijazah SMA/SMK/MA", "Rapor semester 1-5", "Foto 3x4"],
      "international": ["Ijazah setara SMA (legalized)", "TOEFL/IELTS score", "..."]
    },
    "steps": ["Isi formulir online", "Upload dokumen", "Bayar biaya pendaftaran", "Tes seleksi", "Pengumuman"],
    "fee": 350000
  },
  "contacts": {
    "admissions_phone": "021-7890-1234",
    "admissions_email": "admisi@luminara.ac.id",
    "office_hours": "Senin-Jumat 08:00-16:00 WIB"
  }
}
```

### 4.3 Processing Log Schema — per Message

```json
{
  "message_id": "msg-uuid",
  "timestamp": "2026-04-15T10:30:00+07:00",
  "raw_input": "kak mau tanya, ada beasiswa ga?",
  "total_processing_time_ms": 3200,
  "steps": [
    {
      "step": "language_detection",
      "order": 1,
      "result": "id",
      "confidence": 0.98,
      "reasoning": "Indonesian informal markers: 'kak', 'ga' (colloquial negation)",
      "time_ms": 50
    },
    {
      "step": "intent_classification",
      "order": 2,
      "result": "scholarship",
      "confidence": 0.95,
      "reasoning": "Direct keyword 'beasiswa' maps to scholarship intent",
      "time_ms": 800
    },
    {
      "step": "entity_extraction",
      "order": 3,
      "result": {
        "contact_type": "student",
        "financial_concern": true
      },
      "confidence": 0.80,
      "reasoning": "Informal 'kak' → student. Beasiswa inquiry implies financial concern",
      "time_ms": 600
    },
    {
      "step": "sentiment_analysis",
      "order": 4,
      "result": "neutral",
      "confidence": 0.75,
      "reasoning": "Neutral tone, no frustration or excitement markers",
      "time_ms": 200
    },
    {
      "step": "funnel_staging",
      "order": 5,
      "result": "interest",
      "confidence": 0.85,
      "reasoning": "General scholarship inquiry without specific program → early interest",
      "time_ms": 100
    },
    {
      "step": "urgency_scoring",
      "order": 6,
      "result": "medium",
      "reasoning": "Scholarship inquiries default to medium — financial concern is time-sensitive",
      "time_ms": 50
    },
    {
      "step": "response_generation",
      "order": 7,
      "personalization_applied": [
        "bahasa_indonesia",
        "informal_tone",
        "scholarship_focused",
        "encouraging_empathetic"
      ],
      "knowledge_context_used": ["scholarships.beasiswa_prestasi", "scholarships.kip_kuliah"],
      "reasoning": "Student + scholarship interest → warm, encouraging tone with specific options",
      "time_ms": 1200
    },
    {
      "step": "next_best_action",
      "order": 8,
      "result": {
        "action_type": "send_scholarship_guide",
        "secondary": "schedule_followup_3_days"
      },
      "reasoning": "Interest stage + medium urgency → provide info proactively, follow up if silent",
      "time_ms": 200
    }
  ]
}
```

---

## 5. AI Pipeline Design

### 5.1 Single-Pass vs Multi-Pass Strategy

**Approach: Hybrid** — Satu LLM call untuk analisis (intent + entity + sentiment + funnel + urgency), lalu satu LLM call terpisah untuk response generation. Ini optimal karena:
- Analisis bisa dijadikan structured output dalam satu prompt
- Response generation butuh context yang lebih kaya (knowledge base + profil lengkap)

```
Pass 1: Analysis (structured JSON output)
  Input: message + lead_history + system_prompt
  Output: {language, intent, entities, sentiment, funnel_stage, urgency}

Pass 2: Response + NBA Generation
  Input: message + analysis_result + lead_profile + knowledge_base_context
  Output: {draft_response, next_best_action, reasoning}
```

### 5.2 Intent Classification Taxonomy

| Intent | Sub-intents | Contoh Trigger |
|--------|------------|----------------|
| `inquiry_prodi` | curriculum, accreditation, career_prospect, comparison | "jurusan apa saja", "akreditasi", "prospek kerja" |
| `inquiry_biaya` | tuition, installment, comparison, total_cost | "biaya berapa", "bisa cicil", "dibanding kampus X" |
| `registration` | how_to, direct_apply, requirements, deadline | "cara daftar", "saya mau daftar", "syarat-syaratnya" |
| `scholarship` | need_based, merit_based, general, quota | "beasiswa", "potongan biaya", "KIP" |
| `followup_status` | check_status, no_response, timeline | "sampai mana prosesnya", "sudah email 3 kali" |
| `complaint` | technical, process, service | "error", "tidak ada respons", "kecewa" |
| `ambiguous` | too_short, unclear, off_topic | "info dong", random text, emoji only |
| `partnership` | school_visit, bulk_inquiry, collaboration | "kunjungan kampus", "untuk sekolah kami" |

### 5.3 Funnel Stage Rules

```
Stage Determination Logic (in priority order):

1. ENROLLED: lead has registration_id OR status mentions "sudah terdaftar"
2. DECISION: intent=registration AND (has name OR has school_origin OR direct_apply)
3. CONSIDERATION: intent in [inquiry_biaya, scholarship] OR comparison language present
4. INTEREST: inquiry about specific program OR follow-up on earlier conversation
5. AWARENESS: general inquiry, first-time contact, "info dong"
```

### 5.4 Urgency Override Rules

```
Base urgency from funnel stage:
  awareness → low
  interest → low-medium  
  consideration → medium
  decision → high
  enrolled → high

Overrides (highest takes precedence):
  1. complaint OR sentiment=frustrated → CRITICAL
  2. deadline_mentioned → upgrade +1 level
  3. no_response_mentioned (>7 days) → upgrade to HIGH
  4. contact_type=counselor (institutional) → minimum MEDIUM
  5. multi_student_inquiry → minimum MEDIUM
```

### 5.5 Personalization Engine Rules

Respons HARUS berbeda untuk profil berbeda pada pertanyaan serupa. Berikut signal yang digunakan:

| Signal | Impact on Response |
|--------|-------------------|
| **Language** | Respons dalam bahasa user (ID/EN/Mixed) |
| **Contact type** | student→"Kak", parent→"Bapak/Ibu", counselor→"Bapak/Ibu Guru" |
| **School type** | SMK→highlight skill conversion, SMA→academic focus, International→English track |
| **Sentiment** | frustrated→empathetic + apology, anxious→reassuring, excited→enthusiastic |
| **Financial concern** | true→proactively mention beasiswa & KIP |
| **Academic achievement** | high→merit scholarship info, average→general beasiswa |
| **Prior interactions** | Reference previous conversation context |
| **Funnel stage** | awareness→broad info, decision→specific actionable steps |

### 5.6 Next Best Action (NBA) Matrix

| Funnel Stage | Urgency | NBA |
|-------------|---------|-----|
| Awareness + Low | Auto-respond + schedule follow-up in 3 days |
| Awareness + Medium | Auto-respond + send digital brochure |
| Interest + Low | Send program-specific details + follow-up 3 days |
| Interest + Medium | Invite to campus tour / webinar |
| Consideration + Medium | Connect with alumni/current student + counselor |
| Consideration + High | Assign dedicated counselor + call within 24h |
| Decision + High | Fast-track registration + personal assistance |
| Decision + Critical | Escalate to supervisor + resolve within 4h |
| Any + Critical (complaint) | Immediate escalation + apology response first |

---

## 6. Error Handling Strategy

### 6.1 Hierarki Error

```
Level 1 — Input Validation (preventable)
  → Empty message, XSS attempt, too long (>5000 chars)
  → Aksi: Return friendly error message, log attempt

Level 2 — LLM API Error (recoverable)
  → Timeout, rate limit, 500 error
  → Aksi: Retry 3x with exponential backoff (2, 4, 8 seconds)
  → Setelah 3x gagal: fallback to rule-based classification + generic acknowledgment

Level 3 — Classification Ambiguity (non-fatal)
  → LLM confidence < 0.6 for intent classification
  → Aksi: Mark as 'ambiguous', respond with clarification question
  → Log low-confidence cases for model improvement

Level 4 — Data Integrity (partially recoverable)
  → Incomplete lead profile, missing required fields
  → Aksi: Process with available data, flag for manual review
  → Profile fields are ALWAYS optional — system never blocks on missing data

Level 5 — System Error (requires attention)
  → Database connection failed, WebSocket disconnected
  → Aksi: Return "Maaf, sistem sedang mengalami gangguan" + queue message for retry
  → Alert admin via dashboard notification
```

### 6.2 LLM Fallback Chain

```
Primary: LLM API (OpenAI/Gemini/Claude)
  → Structured JSON output for analysis
  → Full personalization for response generation

Fallback (if LLM unavailable):
  → Rule-based intent classification (keyword matching)
  → Template-based response (acknowledging receipt)
  → Queue message for LLM processing when available
  → Log all fallback events for monitoring
```

### 6.3 Ambiguous Message Handling

```
"info dong"       → Respond with menu of options (not assumptions)
Multi-intent      → Process all intents, prioritize most actionable
Mixed language    → Respond in dominant language, acknowledge both
Emoji-only        → Respond with friendly clarification request
Off-topic         → Politely redirect to admissions-related topics
```

---

## 7. Correctness Properties

### Property 1: Bilingual Response Consistency

*Untuk setiap* pesan yang terdeteksi sebagai bahasa Indonesia, draft respons yang dihasilkan harus dalam bahasa Indonesia. *Untuk setiap* pesan yang terdeteksi sebagai bahasa Inggris, draft respons harus dalam bahasa Inggris.

**Validates: Requirements 1.1, 1.2**

### Property 2: Intent Classification Coverage

*Untuk setiap* pesan dari 17 skenario uji, intent classification harus menghasilkan minimal satu intent yang valid (bukan `null` atau empty) dari taxonomy yang didefinisikan.

**Validates: Requirements 2.1, 2.2**

### Property 3: Funnel Stage Monotonic Progression

*Untuk setiap* lead, funnel stage hanya dapat bergerak maju (awareness → interest → consideration → decision → enrolled) atau tetap di stage yang sama — tidak boleh mundur, kecuali ada override manual oleh admin.

**Validates: Requirements 2.3**

### Property 4: Urgency Override Precedence

*Untuk setiap* pesan yang mengandung keluhan atau sentiment frustrasi, urgency score harus di-set ke `critical` — terlepas dari funnel stage.

**Validates: Requirements 2.4**

### Property 5: Processing Log Completeness

*Untuk setiap* pesan yang diproses, processing log harus memiliki entry untuk semua 8 steps (language_detection, intent_classification, entity_extraction, sentiment_analysis, funnel_staging, urgency_scoring, response_generation, next_best_action) — tidak boleh ada step yang missing.

**Validates: Requirements 3.1**

### Property 6: Personalization Non-Template

*Untuk dua* pesan yang sama ("ada beasiswa ga?") dari dua lead berbeda (student vs parent), draft respons yang dihasilkan harus berbeda dalam hal tone, sapaan, dan konten — bukan template yang sama.

**Validates: Requirements 2.5, 4.2**

### Property 7: NBA Action Validity

*Untuk setiap* next best action yang dihasilkan, `action_type` harus merupakan salah satu dari: `auto_respond`, `send_brochure`, `invite_tour`, `connect_alumni`, `assign_counselor`, `schedule_call`, `fast_track`, `escalate`.

**Validates: Requirements 2.6, 4.3**

### Property 8: Lead Profile Incremental Update

*Untuk setiap* entity yang diekstrak dari pesan baru, profile lead harus diperbarui secara inkremental — field yang sudah terisi tidak boleh di-overwrite dengan `null`, hanya ditambah atau diperbarui dengan nilai baru yang non-null.

**Validates: Requirements 2.2, 5.3**

---

## 8. Testing Strategy

### 8.1 Pendekatan Testing

Sistem diuji melalui tiga lapisan:

- **Unit tests**: Memverifikasi setiap komponen pipeline secara independen
- **Integration tests**: Memverifikasi alur end-to-end dari pesan masuk hingga output
- **Scenario tests**: Memverifikasi 17 skenario realistis menghasilkan output yang masuk akal

### 8.2 Test Structure

```
backend/tests/
├── test_pipeline.py          # Unit test setiap step pipeline
│   ├── test_language_detection
│   ├── test_intent_classification
│   ├── test_entity_extraction
│   ├── test_sentiment_analysis
│   ├── test_funnel_staging
│   ├── test_urgency_scoring
│   ├── test_response_generation
│   └── test_nba_engine
│
├── test_api.py               # Test API endpoints
│   ├── test_send_message
│   ├── test_get_leads
│   ├── test_dashboard_summary
│   └── test_response_approval
│
├── test_scenarios.py         # Test 17 skenario realistis end-to-end
│   ├── test_scenario_01_inquiry_prodi_id
│   ├── test_scenario_02_inquiry_prodi_en
│   ├── ...
│   └── test_scenario_17_guru_bk
│
└── test_edge_cases.py        # Edge case tests
    ├── test_empty_message
    ├── test_very_long_message
    ├── test_xss_attempt
    ├── test_llm_timeout_fallback
    └── test_concurrent_messages
```

### 8.3 Skenario Test — 17 Interaksi Realistis

| # | Skenario | Input | Expected Intent | Expected Funnel | Expected Urgency |
|---|----------|-------|----------------|-----------------|------------------|
| 1 | Inquiry Prodi (ID informal) | "kak mau tanya, di kampus ini ada jurusan IT ga?" | inquiry_prodi | awareness | low |
| 2 | Inquiry Prodi (EN formal) | "I'm interested in Business Management..." | inquiry_prodi | interest | medium |
| 3 | Perbandingan Prodi | "Bedanya SI sama TI apa ya?" | inquiry_prodi | consideration | medium |
| 4 | Biaya (Orang Tua) | "Selamat siang, saya orang tua dari Rizky..." | inquiry_biaya | consideration | medium |
| 5 | Biaya Perbandingan | "biaya di sini berapa? dibanding kampus X?" | inquiry_biaya | consideration | medium |
| 6 | Cara Mendaftar | "Gimana caranya daftar? lulusan SMK akuntansi" | registration | decision | high |
| 7 | Pendaftaran Langsung | "Saya mau daftar sekarang. Nama Putri Ayu..." | registration | decision | high |
| 8 | Pendaftaran (EN, International) | "I'd like to apply. International student, Malaysia" | registration | decision | high |
| 9 | Beasiswa (keluarga kurang mampu) | "Ada beasiswa ga? keluarga kurang mampu, nilai 85 😢" | scholarship | interest | high |
| 10 | Beasiswa Prestasi | "Juara 1 olimpiade matematika provinsi" | scholarship | consideration | medium |
| 11 | Cek Status | "Sudah daftar, nomor REG-2026-0412" | followup_status | decision | high |
| 12 | Follow-up Tidak Ada Respons | "Sudah email 3x, belum ada balasan, 2 minggu" | followup_status | decision | critical |
| 13 | Keluhan Teknis | "Website error terus, deadline besok!" | complaint | decision | critical |
| 14 | Pesan Tidak Jelas | "info dong" | ambiguous | awareness | low |
| 15 | Multi-Intent | "Jurusan DKV ada? Biaya? Beasiswa? Mau daftar" | multi-intent | decision | high |
| 16 | Code-switching | "Hi kak, I'm from Singapore. Mau tanya prodi..." | inquiry_prodi | interest | medium |
| 17 | Guru BK | "Saya Ibu Sari, guru BK SMAN 3. Ada 5 siswa..." | partnership | awareness | medium |

### 8.4 Edge Cases yang Harus Dicover

- Pesan kosong → friendly error, no crash
- Pesan > 5000 karakter → truncate, process, warn
- XSS/injection attempt → sanitize, log, respond safely
- LLM timeout → fallback rule-based, queue for retry
- Concurrent messages from same lead → process sequentially, update profile correctly
- Same question from different profiles → different personalized responses
- Lead with zero profile data → still process, explain limitations in log
- Non-text input (emoji only, numbers only) → mark ambiguous, ask clarification
