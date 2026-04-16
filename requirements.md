# Requirements Document

## Fitur: Sistem Otomasi Admisi Berbasis AI — PT Jangkar Arunika Luminara

## Pendahuluan

PT Jangkar Arunika Luminara (JAL Group) menaungi unit pendidikan tinggi yang mengelola volume data besar dan terus bertumbuh — dari data calon mahasiswa (leads), mahasiswa aktif, kurikulum, hingga rekam jejak akademik. Sistem ini membangun otomasi admisi berbasis AI yang menangani tiga tantangan kritis: manajemen database besar, pemrosesan personalisasi dalam skala besar, dan peningkatan konversi leads menjadi mahasiswa terdaftar.

Sistem terdiri dari tiga lapisan: Input (chatbot WhatsApp-style), Processing (AI pipeline klasifikasi, profiling, dan response generation), dan Output (admin dashboard dengan analytics). Pipeline dibangun sebagai web application monorepo (Python backend + HTML/JS frontend) dengan observability penuh atas setiap keputusan AI.

---

## Glosarium

- **Lead**: Calon mahasiswa yang menghubungi sistem melalui chatbot atau kanal lainnya.
- **Funnel Stage**: Posisi lead dalam konversi admisi: awareness → interest → consideration → decision → enrolled.
- **Intent**: Kategori tujuan pesan yang dikirim lead (pertanyaan prodi, biaya, pendaftaran, beasiswa, follow-up, keluhan, ambigu, partnership).
- **NBA (Next Best Action)**: Rekomendasi tindakan lanjutan untuk tim admisi guna meningkatkan probabilitas konversi.
- **Processing Log**: Catatan langkah-per-langkah dari keputusan AI pipeline, termasuk reasoning dan confidence score.
- **Knowledge Base**: Data referensi kampus (program studi, biaya, beasiswa, FAQ) yang diinjeksikan ke LLM sebagai konteks.
- **MessageProcessor**: Komponen orchestrator yang menjalankan seluruh pipeline AI untuk setiap pesan.
- **LLMService**: Abstraction layer untuk komunikasi dengan LLM API (OpenAI/Gemini/Claude).
- **DraftResponse**: Respons yang di-generate AI, menunggu approval atau edit dari admin sebelum dikirim.
- **Observability**: Kemampuan evaluator/admin untuk melihat proses berpikir sistem secara transparan.
- **Personalization Signal**: Informasi dari profil lead yang digunakan untuk menyesuaikan respons (bahasa, tone, konten).
- **Contact Type**: Jenis penghubung — student (calon mahasiswa), parent (orang tua), counselor (guru BK).
- **Urgency Score**: Tingkat urgensi follow-up — low, medium, high, critical.
- **Bilingual**: Kemampuan sistem untuk menerima dan merespons dalam Bahasa Indonesia dan Bahasa Inggris.
- **Session ID**: Identifier unik per browser session untuk melacak lead tanpa login.
- **Channel**: Kanal asal lead — chatbot, whatsapp, form, event, referral.

---

## Persyaratan


### Persyaratan 1: Chatbot Interface — Dual Mode (Layer 1 — Input)

#### 1A. User-Facing Mode (path: `/`)

**User Story:** Sebagai calon mahasiswa (atau orang tua / guru BK), saya ingin bisa mengirim pertanyaan tentang kampus melalui interface chat yang familiar seperti WhatsApp, agar saya bisa mendapatkan informasi tanpa harus mengisi formulir atau datang langsung.

##### Kriteria Penerimaan

1. THE User Chatbot UI SHALL menampilkan interface bergaya WhatsApp/Telegram dengan chat bubble layout, avatar, dan timestamp pada setiap pesan.
2. THE User Chatbot UI SHALL menampilkan welcome message otomatis saat user pertama kali membuka halaman, berisi sapaan dan **3 opsi quick-start yang bisa diklik** (Info Program Studi, Biaya & Beasiswa, Cara Mendaftar) yang berfungsi sebagai pre-classifier intent.
3. WHEN user mengklik salah satu quick-start option, THE system SHALL otomatis mengirimkan pesan terkait ke backend dengan metadata `quick_start_intent` sehingga pipeline menggunakan intent yang sudah ditentukan (confidence = 1.0), melewati step intent classification dari LLM.
4. WHEN user TIDAK mengklik quick-start option dan langsung mengetik pesan, THE system SHALL menghilangkan opsi quick-start dan memproses pesan secara normal melalui LLM untuk intent classification dan profiling.
5. THE User Chatbot UI SHALL menerima dan memproses pesan dalam Bahasa Indonesia dan Bahasa Inggris tanpa user perlu memilih bahasa terlebih dahulu.
6. THE User Chatbot UI SHALL responsive dan mobile-first, dapat digunakan di smartphone, tablet, dan desktop tanpa kehilangan fungsionalitas.
7. THE User Chatbot UI SHALL menampilkan typing indicator saat sistem sedang memproses pesan.
8. THE User Chatbot UI SHALL dapat digunakan oleh pengguna non-teknis tanpa panduan atau training — interaksi harus sealami percakapan chat biasa.

#### 1B. Admin-Facing Mode (path: `/admin`)

**User Story:** Sebagai staf admisi, saya ingin bisa memonitor semua percakapan chatbot dengan calon mahasiswa secara real-time, melakukan intervensi manual jika diperlukan, dan melihat kategorisasi setiap chat masuk dalam format tabel yang bisa di-sort/filter beserta visualisasi dinamis, agar saya bisa mengambil tindakan yang tepat dengan cepat.

##### Kriteria Penerimaan — Chat Monitor & Intervention

9. THE Admin Interface SHALL menampilkan daftar semua active conversations dengan preview pesan terakhir, nama/session lead, urgency badge (color-coded), dan timestamp.
10. THE Admin Interface SHALL memungkinkan admin memilih conversation untuk melihat full chat history (termasuk pesan inbound dari user dan outbound dari AI/admin).
11. THE Admin Interface SHALL memungkinkan admin mengirim balasan manual (intervensi) langsung ke user tertentu, yang disimpan sebagai pesan outbound dengan `processing_log.source = "admin_manual"`.
12. THE Admin Interface SHALL menandai conversation yang memerlukan intervensi admin dengan badge "Needs Review" jika: AI confidence < 0.6, urgency = critical, atau user minta bicara dengan manusia.
13. THE Admin Interface SHALL accessible tanpa login/password (URL-based access saja) untuk kemudahan demo.

##### Kriteria Penerimaan — Categorization Dashboard

14. THE Categorization Dashboard SHALL menampilkan tabel semua pesan masuk dengan kolom: Timestamp, Sender, Message Preview (50 chars), Intent, Funnel Stage, Urgency, Sentiment, dan Confidence Score.
15. THE Categorization Table SHALL mendukung **sorting** pada kolom: Timestamp, Sender, Intent, Funnel Stage, Urgency, Sentiment, dan Confidence (klik header kolom untuk toggle asc/desc).
16. THE Categorization Table SHALL mendukung **filtering** melalui: dropdown multi-select untuk Intent, Funnel Stage, Urgency, dan Sentiment; date range picker untuk Timestamp; range slider untuk Confidence; dan search bar untuk Sender/Message.
17. THE Categorization Dashboard SHALL menampilkan **4 chart visualisasi dinamis**: Intent Distribution (horizontal bar), Funnel Distribution (pie/donut), Urgency Breakdown (stacked bar), dan Chat Volume Timeline (line chart).
18. ALL chart visualizations SHALL **reactive** — otomatis update menampilkan data yang sesuai dengan filter dan sort yang aktif di tabel. Misalnya, jika admin filter `urgency=critical`, semua chart hanya menampilkan data dari pesan dengan urgency critical.
19. THE Categorization Dashboard SHALL menggunakan Chart.js sebagai library visualisasi.


### Persyaratan 2: AI Processing Pipeline (Layer 2 — Processing: Klasifikasi & Profiling)

**User Story:** Sebagai sistem AI, saya harus mampu menganalisis setiap pesan yang masuk untuk menentukan intent, mengekstrak informasi relevan, dan membangun profil calon mahasiswa secara inkremental, agar tim admisi memiliki pemahaman lengkap tentang setiap lead.

#### Kriteria Penerimaan

1. THE MessageProcessor SHALL mengklasifikasikan setiap pesan ke dalam minimal satu dari 8 kategori intent: `inquiry_prodi`, `inquiry_biaya`, `registration`, `scholarship`, `followup_status`, `complaint`, `ambiguous`, `partnership`.
2. THE MessageProcessor SHALL mengekstrak entity dari pesan dan membangun profil lead secara inkremental: nama, asal sekolah, jenis sekolah, program studi yang diminati, tipe kontak (student/parent/counselor), nationality, prestasi akademik, kekhawatiran finansial, dan preferensi bahasa.
3. THE MessageProcessor SHALL menentukan posisi lead dalam funnel konversi (awareness, interest, consideration, decision, enrolled) berdasarkan intent, informasi yang diberikan, dan riwayat pesan sebelumnya.
4. THE MessageProcessor SHALL menentukan tingkat urgensi follow-up (low, medium, high, critical) berdasarkan funnel stage, sentiment, dan override rules (complaint → critical, deadline mentioned → upgrade, no_response > 7 hari → high).
5. THE MessageProcessor SHALL menghasilkan draft respons yang dipersonalisasi berdasarkan profil lead (bahasa, tone, konten spesifik), bukan template generik — respons untuk student dan parent pada pertanyaan yang sama harus berbeda.
6. THE MessageProcessor SHALL menghasilkan rekomendasi next best action (NBA) untuk tim admisi berdasarkan funnel stage dan urgency: mulai dari auto-respond hingga eskalasi ke supervisor.
7. THE MessageProcessor SHALL memproses pesan dengan multi-intent (lebih dari satu pertanyaan dalam satu pesan) dengan mengidentifikasi dan merespons semua intent, bukan hanya yang pertama.
8. THE MessageProcessor SHALL menangani pesan ambigu (seperti "info dong") dengan merespons berupa menu opsi, bukan asumsi, dan menandai intent sebagai `ambiguous`.


### Persyaratan 3: Observability & Transparency (Layer 2 — Processing: Logging)

**User Story:** Sebagai evaluator/admin, saya ingin bisa melihat proses berpikir sistem langkah per langkah untuk setiap pesan yang diproses, agar saya bisa memahami mengapa sistem mengambil keputusan tertentu dan melakukan koreksi jika diperlukan.

#### Kriteria Penerimaan

1. THE MessageProcessor SHALL mencatat processing log untuk setiap pesan yang berisi entry untuk semua 8 langkah: language_detection, intent_classification, entity_extraction, sentiment_analysis, funnel_staging, urgency_scoring, response_generation, next_best_action.
2. EACH processing log entry SHALL mencakup: nama step, urutan, hasil, confidence score (0.0-1.0 jika applicable), reasoning (penjelasan mengapa hasil tersebut dipilih), dan waktu pemrosesan dalam milidetik.
3. THE processing log SHALL disimpan sebagai JSONB di kolom `processing_log` pada tabel `messages` sehingga dapat di-query dan ditampilkan di dashboard.
4. THE Admin Dashboard SHALL menampilkan processing log yang bisa di-expand per pesan, menunjukkan setiap langkah pemrosesan dengan reasoning yang dapat dibaca oleh staf non-teknis.
5. THE Admin Dashboard SHALL menampilkan confidence scores secara visual (color-coded bars) sehingga admin dapat dengan cepat mengidentifikasi keputusan AI yang kurang yakin.
6. THE Admin Dashboard SHALL menyediakan kemampuan override: admin dapat mengoreksi klasifikasi intent atau funnel stage, dan koreksi tersebut dicatat sebagai feedback.


### Persyaratan 4: Personalized Response Generation (Layer 2 — Processing: Respons)

**User Story:** Sebagai calon mahasiswa, saya ingin mendapatkan respons yang relevan dan personal berdasarkan situasi dan kebutuhan saya, agar saya merasa diperhatikan dan terbantu dalam proses pendaftaran.

#### Kriteria Penerimaan

1. THE ResponseGenerator SHALL menghasilkan respons dalam bahasa yang sama dengan pesan user — Bahasa Indonesia untuk pesan ID, English untuk pesan EN, dominant language untuk pesan mixed.
2. THE ResponseGenerator SHALL menggunakan sapaan yang sesuai dengan contact_type: "Kak" untuk student, "Bapak/Ibu" untuk parent, "Bapak/Ibu Guru" untuk counselor.
3. THE ResponseGenerator SHALL menyesuaikan konten berdasarkan profil spesifik: lulusan SMK → highlight konversi skill, international student → English track info, keluarga kurang mampu → info beasiswa KIP.
4. THE ResponseGenerator SHALL menyesuaikan tone berdasarkan sentiment: empathetic jika frustrated, reassuring jika anxious, enthusiastic jika excited.
5. THE ResponseGenerator SHALL mereferensi informasi yang sudah diberikan user di pesan sebelumnya (nama, sekolah, prestasi) untuk menunjukkan konteks percakapan dipertahankan.
6. THE ResponseGenerator SHALL menginjeksikan informasi dari KnowledgeBase (data kampus: prodi, biaya, beasiswa) yang relevan dengan intent user, bukan informasi random.
7. WHEN two leads with different profiles ask the same question, THE ResponseGenerator SHALL produce demonstrably different responses reflecting each lead's unique profile.


### Persyaratan 5: Output Dashboard & Reports (Layer 3 — Output)

**User Story:** Sebagai staf admisi dan manajemen, saya ingin melihat semua leads yang sudah terklasifikasi dalam dashboard yang mudah dipahami, agar saya bisa mengambil tindakan yang tepat tanpa berlatar belakang teknis.

#### Kriteria Penerimaan

1. THE Admin Dashboard SHALL menampilkan overview panel dengan: total leads (hari ini/minggu ini/bulan ini), distribusi funnel (bar chart atau funnel visualization), dan leads yang membutuhkan perhatian segera (urgency = critical/high).
2. THE Admin Dashboard SHALL menampilkan lead management table dengan kolom: nama/ID, tipe kontak, pesan terakhir (preview), intent, funnel stage (visual indicator), urgency (color-coded badge), NBA recommendation, draft response (quick-view), dan assigned counselor.
3. THE Admin Dashboard SHALL menyediakan lead detail view yang menampilkan: full conversation history, complete profile card, processing log (expandable), funnel journey timeline, dan semua draft responses.
4. THE Admin Dashboard SHALL menampilkan analytics: jumlah leads per tahap funnel, conversion rate per kanal, rata-rata response time, tren mingguan/bulanan, dan hal-hal yang memerlukan perhatian segera.
5. THE Admin Dashboard SHALL menyediakan kemampuan filter dan sort pada lead table berdasarkan funnel stage, urgency, intent, tanggal, dan assigned counselor.
6. THE Admin Dashboard SHALL dapat dipahami oleh staf non-teknis tanpa penjelasan tambahan — menggunakan bahasa Indonesia, visualisasi yang intuitif, dan color-coding yang konsisten.
7. THE draft response view SHALL memungkinkan admin untuk meng-approve, mengedit, atau menolak draft response sebelum dikirim ke calon mahasiswa.


### Persyaratan 6: Knowledge Base & Data Kampus

**User Story:** Sebagai sistem AI, saya membutuhkan data referensi kampus yang akurat dan terstruktur, agar respons yang saya berikan kepada calon mahasiswa berisi informasi yang benar dan up-to-date.

#### Kriteria Penerimaan

1. THE KnowledgeBase SHALL menyimpan data minimal 5 program studi dengan informasi lengkap: nama, fakultas, jenjang, akreditasi, durasi, total SKS, deskripsi, prospek karir, biaya per semester, biaya pendaftaran, dan highlight kurikulum.
2. THE KnowledgeBase SHALL menyimpan data minimal 3 jenis beasiswa: beasiswa prestasi, beasiswa bantuan finansial (KIP), dan beasiswa internal kampus, masing-masing dengan syarat, coverage, dan kuota.
3. THE KnowledgeBase SHALL menyimpan informasi proses pendaftaran: gelombang intake, persyaratan umum dan internasional, tahapan pendaftaran, dan biaya pendaftaran.
4. THE KnowledgeBase SHALL menyimpan kontak admisi (telepon, email, jam kerja) untuk digunakan dalam respons.
5. THE KnowledgeBase SHALL dapat di-update tanpa mengubah kode — data disimpan dalam file JSON yang terpisah dari aplikasi.
6. THE LLMService SHALL menginjeksikan informasi KnowledgeBase yang relevan ke dalam prompt LLM berdasarkan intent yang terdeteksi, bukan seluruh data.


### Persyaratan 7: Edge Cases & Error Handling

**User Story:** Sebagai sistem, saya harus dapat menangani kondisi dunia nyata — data tidak lengkap, pesan ambigu, error, dan situasi tidak terduga — dengan graceful degradation, agar user selalu mendapatkan respons yang berguna meskipun terjadi masalah.

#### Kriteria Penerimaan

1. WHEN LLM API mengalami timeout atau error, THE MessageProcessor SHALL melakukan retry 3 kali dengan exponential backoff (2, 4, 8 detik), lalu fallback ke rule-based classification dan template acknowledgment jika tetap gagal.
2. WHEN pesan yang diterima kosong, terlalu panjang (>5000 karakter), atau mengandung potensi XSS, THE Message API SHALL menolak pesan dengan error message yang friendly dalam bahasa Indonesia.
3. WHEN profil lead tidak memiliki nama atau informasi apapun, THE MessageProcessor SHALL tetap memproses pesan dan membangun profil secara inkremental — tidak ada hard requirement untuk field tertentu.
4. WHEN LLM classification confidence < 0.6, THE MessageProcessor SHALL menandai intent sebagai `ambiguous` dengan sub-tag `low_confidence` dan merespons dengan pertanyaan klarifikasi, bukan asumsi.
5. WHEN admin mengoreksi klasifikasi intent atau funnel stage, THE system SHALL menyimpan koreksi tersebut sebagai training data untuk evaluasi kualitas AI di masa mendatang.
6. WHEN database connection gagal, THE system SHALL menampilkan pesan "Maaf, sistem sedang mengalami gangguan" dan meng-queue pesan untuk diproses ulang saat koneksi pulih.
7. THE system SHALL menangani pesan dengan bahasa campuran (code-switching) tanpa error — mendeteksi sebagai "mixed" dan merespons dalam bahasa dominan.


### Persyaratan 8: Skenario Interaksi Realistis

**User Story:** Sebagai evaluator, saya ingin sistem diuji dengan minimal 15 skenario interaksi realistis yang mencakup berbagai kasus, agar saya yakin sistem dapat menangani keragaman pesan di dunia nyata.

#### Kriteria Penerimaan

1. THE system SHALL menyediakan dan mampu memproses minimal 17 skenario interaksi realistis yang mencakup: pertanyaan umum prodi (ID dan EN), pertanyaan biaya (orang tua dan umum), pendaftaran (lokal dan internasional), beasiswa (need-based dan merit-based), follow-up status, keluhan, pesan ambigu, multi-intent, code-switching, dan inquiry dari guru BK.
2. FOR EACH skenario, THE system SHALL menghasilkan: intent classification yang benar, funnel stage yang tepat, urgency score yang sesuai, draft response yang dipersonalisasi, dan next best action yang relevan.
3. THE system SHALL menunjukkan perbedaan nyata dalam response personalization antara profil yang berbeda pada pertanyaan serupa (contoh: student vs parent bertanya soal biaya).
4. THE testing framework SHALL menyimpan input dan expected output dari semua 17 skenario sebagai automated test yang dapat di-run ulang.


### Persyaratan 9: API Endpoints

**User Story:** Sebagai frontend developer, saya membutuhkan API yang terdefinisi dengan jelas untuk mengintegrasikan chatbot dan dashboard dengan backend AI pipeline, agar frontend dan backend dapat dikembangkan secara paralel.

#### Kriteria Penerimaan

1. THE Backend SHALL menyediakan endpoint `POST /api/chat/send` yang menerima `{session_id, content}` dan mengembalikan `{lead_id, message_id, response, processing_log}`.
2. THE Backend SHALL menyediakan endpoint `GET /api/chat/:leadId` yang mengembalikan seluruh riwayat percakapan untuk lead tersebut.
3. THE Backend SHALL menyediakan endpoint `GET /api/leads` yang mengembalikan daftar leads dengan filtering (funnel_stage, urgency, intent) dan pagination (cursor-based).
4. THE Backend SHALL menyediakan endpoint `GET /api/leads/:id` yang mengembalikan detail lengkap lead: profil, riwayat pesan, processing logs, draft responses, dan next actions.
5. THE Backend SHALL menyediakan endpoint `GET /api/dashboard/summary` yang mengembalikan aggregated stats: total leads, distribusi per funnel stage, distribusi per urgency, dan leads baru hari ini.
6. THE Backend SHALL menyediakan endpoint `GET /api/dashboard/funnel` yang mengembalikan data untuk funnel visualization.
7. THE Backend SHALL menyediakan endpoint `POST /api/response/:id/approve` dan `PATCH /api/response/:id/edit` untuk admin mengelola draft responses.
8. ALL API endpoints SHALL mengembalikan response dalam format JSON dengan HTTP status codes yang appropriate (200, 201, 400, 404, 500).


### Persyaratan 10: Deployment & Setup

**User Story:** Sebagai evaluator, saya ingin bisa menjalankan sistem dengan mudah di local machine, agar saya bisa menguji dan mengevaluasi tanpa setup yang rumit.

#### Kriteria Penerimaan

1. THE system SHALL dapat dijalankan dengan maksimal 3 perintah setelah clone repository (install dependencies, setup environment, run).
2. THE system SHALL menyediakan file `.env.example` yang berisi semua environment variables yang diperlukan (LLM API key, database URL).
3. THE system SHALL menyediakan seed data yang langsung membuat 17 skenario interaksi siap diproses saat pertama kali dijalankan.
4. THE system SHALL menyediakan README.md dengan instruksi setup yang jelas dan lengkap.
5. THE system SHALL dapat berjalan dengan SQLite (tanpa Docker/PostgreSQL) untuk evaluasi cepat, dengan opsi upgrade ke PostgreSQL untuk production.
6. THE system SHALL mendukung minimal satu LLM provider (OpenAI/Gemini/Claude) yang dikonfigurasi via environment variable.
