# Rencana Implementasi: JAL Admissions AI System

## Gambaran Umum

Implementasi sistem otomasi admisi berbasis AI untuk unit pendidikan PT Jangkar Arunika Luminara. Sistem memproses pesan calon mahasiswa melalui chatbot WhatsApp-style, menjalankan AI pipeline (klasifikasi, profiling, funnel staging, response generation), dan menghasilkan dashboard admisi untuk tim non-teknis. Dibangun sebagai monorepo web application (Python FastAPI backend + HTML/JS frontend).

Bahasa implementasi: **Python** (backend), **HTML/CSS/JavaScript** (frontend)

## Tasks

- [ ] 1. Setup proyek dan konfigurasi dasar
  - [ ] 1.1 Buat struktur folder proyek
    - Buat `backend/` dengan subfolder: `api/`, `pipeline/`, `models/`, `services/`, `database/`, `tests/`
    - Buat `frontend/` dengan subfolder: `pages/`, `components/`, `assets/`
    - Buat `knowledge_base/` untuk data referensi kampus
    - Buat `requirements.txt` dengan dependensi: `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, `openai`, `python-dotenv`, `websockets`, `pytest`, `httpx`
    - _Persyaratan: 10.1, 10.4_

  - [ ] 1.2 Implementasi `backend/config.py` — konfigurasi global
    - Definisikan `DATABASE_URL` (SQLite default, PostgreSQL optional)
    - Definisikan `LLM_PROVIDER` dan `LLM_API_KEY` dari environment variables
    - Definisikan `LLM_MODEL` (default: "gpt-4" atau "gemini-1.5-pro")
    - Definisikan `INTENT_CATEGORIES` list: inquiry_prodi, inquiry_biaya, registration, scholarship, followup_status, complaint, ambiguous, partnership
    - Definisikan `FUNNEL_STAGES` ordered list: awareness, interest, consideration, decision, enrolled
    - Definisikan `URGENCY_LEVELS` ordered list: low, medium, high, critical
    - Buat `.env.example` dengan semua environment variables
    - _Persyaratan: 10.2, 10.5, 10.6_

  - [ ] 1.3 Buat `knowledge_base/campus_info.json` — data referensi kampus
    - Buat data universitas fiktif "Universitas Luminara" dengan info lengkap
    - Buat minimal 5 program studi: Teknik Informatika, Sistem Informasi, Manajemen, Psikologi, DKV — masing-masing dengan nama, fakultas, jenjang, akreditasi, durasi, SKS, deskripsi, prospek karir, biaya, dan highlight kurikulum
    - Buat 3 jenis beasiswa: Beasiswa Prestasi Akademik (merit, 25-100%), KIP Kuliah (need-based, 100%), Beasiswa Internal (kombinasi)
    - Buat info pendaftaran: 3 gelombang intake, persyaratan umum & internasional, tahapan pendaftaran, biaya pendaftaran
    - Buat kontak admisi: telepon, email, jam kerja
    - _Persyaratan: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 2. Database Layer — Models & Migrations
  - [ ] 2.1 Implementasi `backend/database/connection.py` — setup koneksi database
    - Buat fungsi `get_db()` untuk SQLite connection (default) atau PostgreSQL
    - Set WAL mode untuk SQLite concurrency
    - _Persyaratan: 10.5_

  - [ ] 2.2 Implementasi `backend/database/migrations.py` — schema setup
    - Buat tabel `leads` dengan kolom: id, session_id, name, contact_type, language_pref, school_origin, school_type, interested_program, nationality, academic_achievement, financial_concern, funnel_stage, urgency, conversion_probability, profile_json, assigned_counselor, channel, tags, created_at, updated_at
    - Buat tabel `messages` dengan kolom: id, lead_id, direction, content, language, intent, intent_confidence, sentiment, processing_log, processing_time_ms, created_at
    - Buat tabel `draft_responses` dengan kolom: id, message_id, lead_id, content, personalization_signals, status, edited_content, created_at
    - Buat tabel `next_actions` dengan kolom: id, lead_id, action_type, action_detail, priority, reasoning, due_at, completed_at, created_at
    - Buat semua indexes: leads(funnel_stage), leads(urgency), messages(lead_id), messages(intent), draft_responses(lead_id), next_actions(lead_id)
    - _Persyaratan: 9.1–9.8_

  - [ ] 2.3 Implementasi `backend/models/` — Pydantic models
    - Buat `lead.py`: Lead model (SQLAlchemy + Pydantic response schema)
    - Buat `message.py`: Message model
    - Buat `draft_response.py`: DraftResponse model
    - Buat `next_action.py`: NextAction model
    - Buat `processing_log.py`: ProcessingLog schema (step, result, confidence, reasoning, time_ms)
    - _Persyaratan: 3.1, 3.2, 3.3_

- [ ] 3. Service Layer — LLM & Knowledge Base
  - [ ] 3.1 Implementasi `backend/services/knowledge_base.py` — KnowledgeBase
    - Buat class `KnowledgeBase` yang load `campus_info.json`
    - Method `get_context(intent, program)` → return relevant campus info berdasarkan intent
    - Method `get_program_info(program_name)` → return detail program studi
    - Method `get_scholarship_info()` → return semua info beasiswa
    - Method `get_registration_info()` → return info pendaftaran
    - _Persyaratan: 6.5, 6.6_

  - [ ] 3.2 Implementasi `backend/services/llm_service.py` — LLMService
    - Buat class `LLMService` yang support OpenAI API (extensible ke Gemini/Claude)
    - Method `analyze_message(message, lead_profile, knowledge_context)` → return structured JSON: {language, intent, intent_confidence, entities, sentiment, funnel_stage, urgency, reasoning}
    - Method `generate_response(message, analysis, lead_profile, knowledge_context)` → return personalized draft response string
    - Method `generate_nba(lead_profile, analysis)` → return {action_type, action_detail, reasoning}
    - Implement retry logic: 3x exponential backoff (2, 4, 8 detik) pada API error
    - Implement fallback: jika LLM unavailable setelah retry, gunakan rule-based classification
    - _Persyaratan: 2.1, 2.5, 2.6, 4.1–4.7, 7.1_

  - [ ] 3.3 Implementasi `backend/services/lead_service.py` — LeadService
    - Buat class `LeadService` untuk CRUD dan business logic
    - Method `get_or_create_lead(session_id)` → get existing atau create new lead
    - Method `update_profile(lead_id, entities)` → incremental update, NEVER overwrite non-null with null
    - Method `update_funnel_stage(lead_id, stage, urgency)` → update stage (forward only, no backward)
    - Method `get_leads_filtered(stage, urgency, page, limit)` → filtered paginated list
    - Method `get_dashboard_summary()` → aggregate stats (total, per funnel, per urgency, new today)
    - _Persyaratan: 5.1, 5.2, 5.5_

- [ ] 4. AI Processing Pipeline
  - [ ] 4.1 Implementasi `backend/pipeline/processor.py` — MessageProcessor
    - Buat class `MessageProcessor` yang orchestrates semua pipeline steps
    - Method `process(message, lead)` → ProcessingResult containing all outputs + processing_log
    - Pipeline steps (sequential):
      1. Language Detection → "id" / "en" / "mixed"
      2. Intent Classification → one of 8 categories (atau multi-intent)
      3. Entity Extraction → {name, school, program, contact_type, ...}
      4. Sentiment Analysis → anxious / frustrated / neutral / excited / ...
      5. Funnel Staging → awareness / interest / consideration / decision / enrolled
      6. Urgency Scoring → low / medium / high / critical (with override rules)
      7. Response Generation → personalized draft
      8. NBA Generation → recommended next action
    - Setiap step menghasilkan StepResult: {step, result, confidence, reasoning, time_ms}
    - Seluruh steps dikumpulkan ke processing_log JSONB
    - _Persyaratan: 2.1–2.8, 3.1, 3.2_

  - [ ] 4.2 Implementasi individual pipeline components (di dalam `backend/pipeline/`)
    - `language_detector.py`: LanguageDetector — detect id/en/mixed (bisa rule-based atau LLM)
    - `intent_classifier.py`: IntentClassifier — classify into 8 categories, support multi-intent
    - `entity_extractor.py`: EntityExtractor — extract structured entities from message
    - `sentiment_analyzer.py`: SentimentAnalyzer — detect emotional tone
    - `funnel_stager.py`: FunnelStager — determine funnel stage based on intent + profile history
    - `urgency_scorer.py`: UrgencyScorer — determine urgency with override rules (complaint→critical, deadline→upgrade, no_response→high)
    - `response_generator.py`: ResponseGenerator — generate personalized draft using LLM + KnowledgeBase
    - `nba_engine.py`: NextBestActionEngine — recommend action based on funnel + urgency matrix
    - _Persyaratan: 2.1–2.8, 4.1–4.7_

  - [ ] 4.3 Tulis test skenario untuk MessageProcessor
    - Test all 17 skenario realistis melalui pipeline
    - Verify intent, funnel_stage, urgency untuk setiap skenario
    - Verify processing_log memiliki semua 8 steps
    - Verify response personalization berbeda untuk profil berbeda pada pertanyaan sama
    - _Persyaratan: 8.1, 8.2, 8.3, 8.4_

- [ ] 5. Checkpoint — Pastikan pipeline berjalan untuk semua 17 skenario
  - Jalankan `pytest backend/tests/` dan pastikan semua test lulus
  - Verifikasi processing_log terisi lengkap untuk setiap skenario
  - Verifikasi personalisasi respons berbeda untuk profil berbeda

- [ ] 6. API Layer — FastAPI Endpoints
  - [ ] 6.1 Implementasi `backend/main.py` — FastAPI entry point
    - Setup FastAPI app dengan CORS middleware (allow all origins untuk dev)
    - Mount static files untuk frontend
    - Include semua routers (chat, leads, dashboard, responses)
    - Startup event: run migrations + seed data
    - _Persyaratan: 10.1_

  - [ ] 6.2 Implementasi `backend/api/chat.py` — Chat endpoints
    - `POST /api/chat/send` — menerima {session_id, content}, process via MessageProcessor, return {lead_id, message_id, response, processing_log}
    - `GET /api/chat/{lead_id}` — return conversation history untuk lead
    - Validasi input: tolak pesan kosong, >5000 chars, XSS detection
    - _Persyaratan: 9.1, 9.2, 7.2_

  - [ ] 6.3 Implementasi `backend/api/leads.py` — Lead endpoints
    - `GET /api/leads` — list leads dengan filter (funnel_stage, urgency, intent) dan pagination
    - `GET /api/leads/{id}` — lead detail lengkap: profil, messages, processing_logs, drafts, next_actions
    - `PATCH /api/leads/{id}` — admin override untuk funnel_stage atau intent (manual correction)
    - _Persyaratan: 9.3, 9.4, 3.6_

  - [ ] 6.4 Implementasi `backend/api/dashboard.py` — Dashboard endpoints
    - `GET /api/dashboard/summary` — total leads, distribusi per funnel/urgency, leads baru hari ini
    - `GET /api/dashboard/funnel` — data untuk funnel visualization chart
    - `GET /api/dashboard/analytics` — tren mingguan, conversion rate, attention items
    - _Persyaratan: 9.5, 9.6_

  - [ ] 6.5 Implementasi `backend/api/responses.py` — Response management endpoints
    - `POST /api/response/{id}/approve` — approve draft response
    - `PATCH /api/response/{id}/edit` — edit draft before sending
    - _Persyaratan: 9.7_

  - [ ] 6.6 Implementasi `backend/api/admin_chat.py` — Admin chat monitor & intervention endpoints
    - `GET /api/admin/conversations` — list semua active conversations dengan preview, urgency, needs_review flag
    - `GET /api/admin/conversations/{lead_id}` — full chat history untuk lead (inbound + outbound)
    - `POST /api/admin/conversations/{lead_id}/reply` — admin manual reply, simpan sebagai outbound message dengan processing_log.source = "admin_manual"
    - _Persyaratan: 1B.9, 1B.10, 1B.11, 1B.12_

  - [ ] 6.7 Implementasi `backend/api/categorization.py` — Categorization query endpoints
    - `GET /api/admin/categorization` — filtered/sorted messages for table (query params: intent, funnel_stage, urgency, sentiment, confidence_min/max, date_from/to, search, sort_by, sort_order, page, limit)
    - `GET /api/admin/categorization/stats` — aggregated stats for charts (intent_distribution, funnel_distribution, urgency_breakdown, volume_timeline), respecting same filter params
    - _Persyaratan: 1B.14, 1B.15, 1B.16, 1B.17, 1B.18_

  - [ ] 6.8 Tulis API tests
    - Test semua endpoints dengan httpx AsyncClient
    - Test validasi input (empty, too long, XSS)
    - Test filter dan pagination pada /api/leads
    - Test response approval dan edit flow
    - Test admin chat monitor endpoints (list, history, reply)
    - Test categorization endpoints (filter, sort, stats aggregation)
    - _Persyaratan: 9.8_

- [ ] 7. Checkpoint — Pastikan semua API endpoints berfungsi
  - Jalankan `pytest backend/tests/test_api.py`
  - Test manual via curl/httpie untuk setiap endpoint

- [ ] 8. Frontend — Shared Chatbot Components
  - [ ] 8.1 Implementasi `frontend/style.css` — Design system
    - Definisikan CSS custom properties: color palette (dark mode primary), typography (Inter/Roboto), spacing scale
    - Definisikan chat bubble styles (inbound green, outbound white/gray)
    - Definisikan urgency color palette: low→gray, medium→yellow, high→orange, critical→red
    - Definisikan funnel stage color palette: awareness→light blue, interest→blue, consideration→indigo, decision→purple, enrolled→green
    - Responsive breakpoints: mobile (<768px), tablet (768-1024px), desktop (>1024px)
    - Glassmorphism dan subtle gradient effects
    - Smooth transition dan hover animations
    - _Persyaratan: 1A.6_

  - [ ] 8.2 Implementasi `frontend/components/chat-bubble.js` — Shared chat bubble
    - Bubble dengan avatar, timestamp, dan animasi masuk
    - Support direction: inbound (user) dan outbound (AI/admin)
    - Admin replies ditandai dengan badge "Admin" pada bubble
    - _Persyaratan: 1A.1_

  - [ ] 8.3 Implementasi `frontend/components/quick-start-options.js` — Quick-start pre-classifier
    - Render 3 opsi klik-able: 📚 Info Program Studi, 💰 Biaya & Beasiswa, 📝 Cara Mendaftar
    - Klik salah satu → opsi menghilang → pesan muncul di chat bubble → auto-submit ke backend dengan metadata `quick_start_intent`
    - Jika user ketik pesan sendiri sebelum klik → opsi menghilang → submit tanpa `quick_start_intent`
    - Hanya muncul di awal conversation (pesan pertama)
    - _Persyaratan: 1A.2, 1A.3, 1A.4_

- [ ] 8A. Frontend — User-Facing Chatbot
  - [ ] 8A.1 Implementasi `frontend/pages/chatbot.js` — User chatbot page
    - Build WhatsApp-style chat interface: chat bubble layout dengan avatar, timestamp
    - Welcome message otomatis saat pertama buka + quick-start options component
    - Input field di bawah dengan send button
    - Typing indicator saat system processing (animated dots)
    - Auto-scroll ke pesan terbaru
    - Mobile-responsive: full-screen chat pada mobile
    - Connect ke `POST /api/chat/send` untuk kirim pesan (include `quick_start_intent` jika applicable)
    - Display response dari backend sebagai bubble baru
    - Generate unique session_id dan simpan di localStorage
    - _Persyaratan: 1A.1, 1A.2, 1A.5, 1A.6, 1A.7, 1A.8_

- [ ] 8B. Frontend — Admin-Facing Chat Monitor & Intervention
  - [ ] 8B.1 Implementasi `frontend/pages/admin-chat.js` — Admin chat monitor
    - Split view layout: chat list (kiri) + chat detail (kanan)
    - Chat list: semua active conversations, sorted by most recent, dengan urgency badge (color-coded) dan "Needs Review" indicator
    - Chat detail: full conversation history (inbound + outbound), termasuk AI replies dan admin replies
    - Admin reply input: text field + send button untuk kirim balasan manual
    - Connect ke `GET /api/admin/conversations` untuk list conversations
    - Connect ke `GET /api/admin/conversations/:leadId` untuk chat history
    - Connect ke `POST /api/admin/conversations/:leadId/reply` untuk admin reply
    - Search conversations functionality
    - Mobile responsive: stacked layout, chat list di atas, detail di bawah
    - _Persyaratan: 1B.9, 1B.10, 1B.11, 1B.12, 1B.13_

  - [ ] 8B.2 Implementasi `frontend/components/chat-category-table.js` — Categorization table
    - Render tabel semua pesan masuk dengan kolom: Timestamp, Sender, Message Preview, Intent, Funnel Stage, Urgency, Sentiment, Confidence
    - Sorting: klik header kolom untuk toggle asc/desc (Timestamp, Sender, Intent, Funnel, Urgency, Sentiment, Confidence)
    - Filtering: dropdown multi-select untuk Intent, Funnel Stage, Urgency, Sentiment; search bar untuk Sender/Message
    - Pagination: navigasi halaman
    - On filter/sort change: emit event untuk trigger chart update
    - Connect ke `GET /api/admin/categorization` dengan query params
    - _Persyaratan: 1B.14, 1B.15, 1B.16_

  - [ ] 8B.3 Implementasi `frontend/components/dynamic-charts.js` — Reactive visualizations
    - 4 chart menggunakan Chart.js:
      1. Intent Distribution — horizontal bar chart
      2. Funnel Distribution — pie/donut chart
      3. Urgency Breakdown — stacked bar chart
      4. Chat Volume Timeline — line chart
    - Reactive: listen to filter change events dari categorization table → re-query `GET /api/admin/categorization/stats` → re-render semua chart
    - Chart labels/title menunjukkan filter aktif (misal: "Intent Distribution (filtered: urgency=critical)")
    - Include Chart.js via CDN (`<script src="https://cdn.jsdelivr.net/npm/chart.js">`)
    - _Persyaratan: 1B.17, 1B.18, 1B.19_

- [ ] 9. Frontend — Admin Dashboard (Overview + Lead Management)
  - [ ] 9.1 Implementasi `frontend/pages/dashboard.js` — Main dashboard
    - Overview panel: stat cards (total leads, new today, critical urgency count, avg response time)
    - Funnel visualization: horizontal bar chart atau funnel shape showing leads per stage
    - Attention needed panel: list of leads with urgency=critical/high, with quick-action buttons
    - Connect ke `GET /api/dashboard/summary` dan `GET /api/dashboard/funnel`
    - _Persyaratan: 5.1, 5.6_

  - [ ] 9.2 Implementasi `frontend/pages/lead-detail.js` — Lead detail page
    - Profile card: semua informasi lead (nama, kontak, sekolah, program, dll.)
    - Conversation history: full chat log dengan both inbound dan outbound messages
    - Processing log viewer: expandable per-message log showing all 8 pipeline steps
    - Funnel journey timeline: visual timeline dari awareness → current stage
    - Draft response panel: view, edit, approve draft responses
    - Next actions list: recommended actions with priority badges
    - _Persyaratan: 5.3, 5.7, 3.4, 3.5_

  - [ ] 9.3 Implementasi `frontend/pages/analytics.js` — Analytics page
    - Leads per funnel stage chart (bar chart)
    - Leads per urgency chart (pie chart)
    - Trend chart: new leads per day (line chart, last 30 days)
    - Intent distribution chart (horizontal bar)
    - _Persyaratan: 5.4_

  - [ ] 9.4 Implementasi dashboard components
    - `components/stat-card.js`: number + label + trend indicator
    - `components/lead-table.js`: sortable, filterable table with pagination
    - `components/funnel-chart.js`: funnel or bar visualization
    - `components/processing-log.js`: expandable processing log viewer with confidence bars
    - `components/urgency-badge.js`: color-coded badge (low=gray, medium=yellow, high=orange, critical=red)
    - _Persyaratan: 5.2, 5.5, 3.4, 3.5_

  - [ ] 9.5 Implementasi `frontend/app.js` — Main app routing
    - Client-side routing: `/` → user chatbot, `/admin` → admin chat monitor + categorization dashboard, `/admin/dashboard` → overview dashboard, `/admin/lead/:id` → lead detail, `/admin/analytics` → analytics
    - Navigation bar untuk admin pages (Chat Monitor, Dashboard, Analytics)
    - No login required — URL-based access
    - _Persyaratan: 1B.13, 5.6_

- [ ] 10. Checkpoint — Pastikan frontend chatbot dan dashboard berfungsi
  - Jalankan `uvicorn backend.main:app` dan buka browser
  - Test chatbot: kirim beberapa pesan, verify respons muncul
  - Test dashboard: verify leads muncul, filter bekerja, detail view loading
  - Test processing log viewer: verify semua steps tampil dengan reasoning

- [ ] 11. Seed Data & Demo Scenarios
  - [ ] 11.1 Implementasi `backend/database/seed.py` — seed data
    - Buat fungsi `seed_demo_data()` yang insert 17 skenario sebagai pre-existing conversations
    - Setiap skenario sudah memiliki: lead profile, message(s), processing_log, draft_response, next_action
    - Skenario mencakup berbagai funnel stages dan urgency levels untuk dashboard penuh
    - Seed dijalankan otomatis saat pertama kali app start (jika database kosong)
    - _Persyaratan: 8.1, 10.3_

  - [ ] 11.2 Verifikasi 17 skenario menghasilkan output yang benar
    - Run semua skenario melalui pipeline (bukan seed statis — actual AI processing)
    - Verify setiap skenario menghasilkan intent, funnel, urgency, response, NBA yang masuk akal
    - Verify dua skenario dengan profil berbeda pada pertanyaan serupa menghasilkan respons berbeda
    - _Persyaratan: 8.2, 8.3_

- [ ] 12. Polish & Final Testing
  - [ ] 12.1 UI polish
    - Pastikan semua micro-animations smooth (chat bubble entry, typing indicator, page transitions)
    - Pastikan mobile responsiveness bekerja sempurna
    - Pastikan color scheme konsisten dan premium
    - Pastikan semua text dalam bahasa Indonesia (kecuali data EN)
    - _Persyaratan: 1.4, 1.6, 5.6_

  - [ ] 12.2 End-to-end testing
    - Test flow lengkap: buka chatbot → kirim pesan → lihat respons → buka dashboard → lihat lead → lihat processing log → approve response
    - Test edge cases: pesan kosong, pesan sangat panjang, pesan ambigu, multi-intent
    - Test LLM fallback: simulate API failure, verify rule-based fallback bekerja
    - _Persyaratan: 7.1–7.7_

  - [ ] 12.3 Documentation
    - Buat/update README.md dengan: deskripsi proyek, arsitektur diagram, setup instructions (3 langkah), daftar environment variables, cara menjalankan tests
    - Pastikan `.env.example` lengkap
    - _Persyaratan: 10.1, 10.2, 10.4_

- [ ] 13. Checkpoint akhir — Full system verification
  - Jalankan seluruh test suite: `pytest backend/tests/ -v`
  - Jalankan app dan demo semua 17 skenario live
  - Verifikasi dashboard menampilkan data yang benar
  - Verifikasi processing logs transparan dan informatif
  - Verifikasi respons personalisasi berbeda untuk profil berbeda

## Catatan

- Setiap task merujuk ke persyaratan spesifik dari requirements.md untuk keterlacakan
- Priority order: pipeline (Task 4) → API (Task 6) → chatbot UI (Task 8) → dashboard UI (Task 9) → polish (Task 12)
- Knowledge base (`campus_info.json`) dibuat di awal (Task 1.3) karena digunakan oleh LLM pipeline
- Seed data (Task 11) dibuat setelah pipeline dan frontend siap, agar evaluator langsung melihat dashboard terisi
- SQLite digunakan as default untuk kemudahan setup — tidak perlu Docker/PostgreSQL untuk demo
- Frontend menggunakan vanilla HTML/CSS/JS (no framework) untuk simplicity dan performance
- LLM API key harus di-set di `.env` — sistem tidak berjalan tanpa LLM provider
