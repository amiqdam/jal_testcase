"""
Seed data — pre-populate database with 17 realistic demo scenarios.
"""
import uuid
import json
from datetime import datetime, timezone, timedelta
from backend.database.connection import get_db


def seed_demo_data():
    """Insert 17 demo scenarios if database is empty."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as count FROM leads")
    if cursor.fetchone()["count"] > 0:
        conn.close()
        return  # Already seeded
    
    now = datetime.now(timezone.utc)
    
    scenarios = [
        {
            "name": "Rina Safitri", "session": "sess-001", "contact_type": "student",
            "school_origin": "SMA Negeri 5 Jakarta", "school_type": "SMA",
            "program": "Teknik Informatika", "funnel": "awareness", "urgency": "low",
            "language": "id", "intent": "inquiry_prodi", "confidence": 0.95,
            "sentiment": "neutral", "message": "kak mau tanya, di kampus ini ada jurusan IT ga?",
            "response": "Halo Kak Rina! 😊 Tentu ada! Kami punya program Teknik Informatika (S1, Akreditasi A) di Fakultas Ilmu Komputer. Kurikulumnya mencakup AI & Machine Learning, Cloud Computing, dan Cybersecurity. Biaya Rp 12.5 juta/semester. Mau tahu lebih detail tentang kurikulum atau prospek karirnya?",
            "nba_type": "auto_respond", "nba_detail": "Auto-respond + schedule follow-up 3 hari", "nba_priority": "low",
        },
        {
            "name": "James Chen", "session": "sess-002", "contact_type": "student",
            "school_origin": "International School Jakarta", "school_type": "International",
            "program": "Manajemen", "funnel": "interest", "urgency": "medium",
            "language": "en", "intent": "inquiry_prodi", "confidence": 0.92,
            "sentiment": "excited", "message": "I'm interested in Business Management program. What's the curriculum like?",
            "response": "Hi James! 😊 Great choice! Our Management program (S1, Accreditation A) at Faculty of Economics & Business covers Digital Marketing, Financial Management, Entrepreneurship, and Strategic Management. Tuition is Rp 10M/semester. We also have an English track for international students. Would you like to know about career prospects or the application process?",
            "nba_type": "send_brochure", "nba_detail": "Kirim info program spesifik + follow-up 3 hari", "nba_priority": "medium",
        },
        {
            "name": "Dimas Pratama", "session": "sess-003", "contact_type": "student",
            "school_origin": "SMA Negeri 1 Bandung", "school_type": "SMA",
            "program": None, "funnel": "consideration", "urgency": "medium",
            "language": "id", "intent": "inquiry_prodi", "confidence": 0.88,
            "sentiment": "confused", "message": "Bedanya SI sama TI apa ya?",
            "response": "Halo Kak! 😊 Pertanyaan bagus! Perbedaan utamanya:\n\n**Teknik Informatika (TI)**: fokus ke pengembangan software, AI, cybersecurity. Cocok yang suka coding.\n\n**Sistem Informasi (SI)**: memadukan IT + bisnis. Fokus ke ERP, Business Intelligence, IT Project Management. Cocok yang suka IT tapi juga tertarik manajemen.\n\nDua-duanya akreditasi A. Mau tahu program mana yang lebih cocok dengan minat Kak?",
            "nba_type": "connect_alumni", "nba_detail": "Hubungkan dengan alumni/mahasiswa aktif + assign konselor", "nba_priority": "medium",
        },
        {
            "name": "Bapak Hendra", "session": "sess-004", "contact_type": "parent",
            "school_origin": "SMAN 3 Surabaya", "school_type": "SMA",
            "program": "Teknik Informatika", "funnel": "consideration", "urgency": "medium",
            "language": "id", "intent": "inquiry_biaya", "confidence": 0.93,
            "sentiment": "neutral", "message": "Selamat siang, saya orang tua dari Rizky. Mau tanya biaya kuliah jurusan IT berapa ya per semesternya?",
            "response": "Selamat siang, Bapak Hendra! 🙏 Terima kasih sudah menghubungi kami. Biaya kuliah Teknik Informatika:\n\n- UKT: Rp 12.500.000/semester\n- Biaya pendaftaran: Rp 5.000.000 (satu kali)\n\nKami juga menyediakan:\n- Beasiswa Prestasi (25-100% potongan)\n- KIP Kuliah (100% gratis + biaya hidup)\n- Cicilan hingga 3x/semester\n\nApakah Bapak ingin tahu lebih detail tentang beasiswa yang tersedia?",
            "nba_type": "send_brochure", "nba_detail": "Auto-respond + kirim brosur digital", "nba_priority": "medium",
        },
        {
            "name": "Anisa Rahma", "session": "sess-005", "contact_type": "student",
            "school_origin": "SMA Negeri 2 Medan", "school_type": "SMA",
            "program": None, "funnel": "consideration", "urgency": "medium",
            "language": "id", "intent": "inquiry_biaya", "confidence": 0.87,
            "sentiment": "anxious", "message": "biaya di sini berapa? dibanding kampus X gimana?",
            "response": "Halo Kak Anisa! 😊 Biaya kuliah kami berkisar Rp 10-13 juta/semester tergantung jurusan. Dibandingkan kampus sejenis, kami termasuk kompetitif dengan fasilitas lengkap (Lab Komputer 4 ruang, Co-Working Space, dll).\n\nKalau ada kekhawatiran soal biaya, kami punya beberapa beasiswa:\n- Beasiswa Prestasi: potongan 25-100%\n- KIP Kuliah: 100% gratis\n\nMau tahu jurusan mana yang diminati supaya bisa kasih info biaya yang lebih detail?",
            "nba_type": "connect_alumni", "nba_detail": "Hubungkan dengan alumni + konselor", "nba_priority": "medium",
        },
        {
            "name": "Putri Ayu", "session": "sess-006", "contact_type": "student",
            "school_origin": "SMK Akuntansi Jakarta", "school_type": "SMK",
            "program": "Manajemen", "funnel": "decision", "urgency": "high",
            "language": "id", "intent": "registration", "confidence": 0.96,
            "sentiment": "excited", "message": "Gimana caranya daftar? saya lulusan SMK akuntansi mau ambil manajemen",
            "response": "Halo Kak Putri! 🎉 Wah senang sekali! Sebagai lulusan SMK Akuntansi, Kak Putri punya dasar yang kuat untuk program Manajemen kami — banyak skill akuntansi yang bisa dikonversi langsung!\n\nCara mendaftar:\n1. Isi formulir online di portal.luminara.ac.id\n2. Upload dokumen (ijazah, rapor, foto)\n3. Bayar pendaftaran Rp 350.000 via virtual account\n4. Ikuti tes seleksi (Sabtu terdekat)\n\nBiaya Manajemen: Rp 10 juta/semester. Ada beasiswa juga lho! Mau dibantu proses pendaftarannya?",
            "nba_type": "fast_track", "nba_detail": "Fast-track pendaftaran + bantuan personal", "nba_priority": "high",
        },
        {
            "name": "Siti Nurhaliza", "session": "sess-007", "contact_type": "student",
            "school_origin": "MAN 1 Yogyakarta", "school_type": "MA",
            "program": "Psikologi", "funnel": "decision", "urgency": "high",
            "language": "id", "intent": "registration", "confidence": 0.97,
            "sentiment": "excited", "message": "Saya mau daftar sekarang. Nama Siti Nurhaliza, dari MAN 1 Yogyakarta, mau ambil psikologi",
            "response": "Halo Kak Siti! 🎉 Selamat atas keputusannya! Program Psikologi kami (Akreditasi A) sangat cocok. Saya sudah mencatat datanya:\n\n- Nama: Siti Nurhaliza\n- Asal: MAN 1 Yogyakarta\n- Program: Psikologi\n\nLangkah selanjutnya:\n1. Kunjungi portal.luminara.ac.id\n2. Upload rapor semester 1-5 + foto\n3. Bayar Rp 350.000\n\nBiaya Psikologi: Rp 11.5 juta/semester. Saat ini Gelombang 2 masih buka (gratis biaya pendaftaran online)! 🎁 Mau langsung dibantu?",
            "nba_type": "fast_track", "nba_detail": "Fast-track pendaftaran + bantuan personal", "nba_priority": "high",
        },
        {
            "name": "Sarah Lee", "session": "sess-008", "contact_type": "student",
            "school_origin": "Penang Free School", "school_type": "International",
            "program": "Teknik Informatika", "funnel": "decision", "urgency": "high",
            "language": "en", "intent": "registration", "confidence": 0.94,
            "sentiment": "neutral", "message": "I'd like to apply. I'm an international student from Malaysia, interested in Computer Science.",
            "response": "Hi Sarah! 😊 Welcome! We'd love to have you at Universitas Luminara. For international students, here's what you need:\n\n1. Legalized high school diploma\n2. TOEFL ≥500 / IELTS ≥5.5\n3. Translated transcripts\n4. Valid passport\n\nOur IT program (Accreditation A) covers AI, Cloud Computing, and Cybersecurity. Tuition: Rp 12.5M/semester (~800 USD). We can assist with student visa processing!\n\nShall I connect you with our international admissions team?",
            "nba_type": "assign_counselor", "nba_detail": "Assign konselor dedicated + hubungi dalam 24 jam", "nba_priority": "high",
        },
        {
            "name": "Ahmad Fauzi", "session": "sess-009", "contact_type": "student",
            "school_origin": "SMA Negeri 1 Semarang", "school_type": "SMA",
            "program": None, "funnel": "interest", "urgency": "high",
            "language": "id", "intent": "scholarship", "confidence": 0.95,
            "sentiment": "anxious", "message": "Ada beasiswa ga? keluarga kurang mampu, nilai rata2 85 😢",
            "response": "Halo Kak Ahmad! 🤗 Tenang ya, kami punya beberapa opsi beasiswa yang bisa membantu:\n\n1. **KIP Kuliah** (100% gratis + biaya hidup Rp 700rb/bulan)\n   - Syarat: penghasilan keluarga ≤ Rp 4 juta/bulan + SKTM\n\n2. **Beasiswa Prestasi** (25% potongan)\n   - Dengan nilai 85, Kak Ahmad sudah memenuhi syarat!\n\n3. **Beasiswa Luminara Berprestasi** (30-75%)\n   - Untuk prestasi non-akademik\n\nKIP Kuliah sepertinya paling cocok untuk kondisi Kak Ahmad. Mau dibantu proses pengajuannya? 💪",
            "nba_type": "assign_counselor", "nba_detail": "Assign konselor dedicated + hubungi dalam 24 jam", "nba_priority": "high",
            "financial_concern": True,
        },
        {
            "name": "Dewi Lestari", "session": "sess-010", "contact_type": "student",
            "school_origin": "SMA Negeri 1 Jakarta", "school_type": "SMA",
            "program": None, "funnel": "consideration", "urgency": "medium",
            "language": "id", "intent": "scholarship", "confidence": 0.91,
            "sentiment": "excited", "message": "Saya juara 1 olimpiade matematika tingkat provinsi! Ada beasiswa prestasi?",
            "response": "Halo Kak Dewi! 🏆 Wow, juara 1 olimpiade matematika provinsi — prestasi luar biasa!\n\nDengan prestasi itu, Kak Dewi berpeluang besar mendapatkan:\n\n1. **Beasiswa Prestasi Akademik** → potongan 75-100% (juara olimpiade nasional/provinsi)\n2. **Beasiswa Luminara Berprestasi** → potongan 50-75% untuk prestasi non-akademik\n\nSiapkan sertifikat juara dan surat rekomendasi kepala sekolah ya. Mau tahu program studi apa yang diminati? Kami bisa cek total biaya setelah beasiswa 🎓",
            "nba_type": "connect_alumni", "nba_detail": "Hubungkan dengan alumni penerima beasiswa", "nba_priority": "medium",
        },
        {
            "name": "Rizky Pratama", "session": "sess-011", "contact_type": "student",
            "school_origin": None, "school_type": None,
            "program": None, "funnel": "decision", "urgency": "high",
            "language": "id", "intent": "followup_status", "confidence": 0.93,
            "sentiment": "neutral", "message": "Saya sudah daftar, nomor pendaftaran REG-2026-0412. Sampai mana prosesnya?",
            "response": "Halo Kak Rizky! 😊 Terima kasih sudah mendaftar. Dengan nomor REG-2026-0412, saya bantu cek ya.\n\nUntuk informasi status pendaftaran terkini, silakan:\n1. Cek di portal.luminara.ac.id → Login → Status Pendaftaran\n2. Atau hubungi langsung: 021-7890-1234\n3. Email: admisi@luminara.ac.id\n\nHasil seleksi biasanya diumumkan 7-14 hari kerja setelah tes. Ada yang bisa dibantu lagi?",
            "nba_type": "schedule_call", "nba_detail": "Jadwalkan follow-up call untuk update status", "nba_priority": "high",
        },
        {
            "name": "Mega Wulandari", "session": "sess-012", "contact_type": "student",
            "school_origin": None, "school_type": None,
            "program": None, "funnel": "decision", "urgency": "critical",
            "language": "id", "intent": "followup_status", "confidence": 0.96,
            "sentiment": "frustrated", "message": "Sudah email 3 kali, belum ada balasan sama sekali. Ini sudah 2 minggu! Gimana sih?",
            "response": "Halo Kak Mega! 🙏 Mohon maaf sebesar-besarnya atas keterlambatan respons kami. Ini sangat tidak seharusnya terjadi dan kami mengerti frustrasi Kak Mega.\n\nSaya akan langsung eskalasi masalah ini ke tim admisi untuk penanganan segera:\n- Tim kami akan menghubungi dalam 4 jam ke depan\n- Atau Kak Mega bisa langsung hubungi: 021-7890-1234 / WA: 0812-3456-7890\n\nSekali lagi mohon maaf ya Kak. Kami pastikan ini tidak terulang 🙏",
            "nba_type": "escalate", "nba_detail": "Eskalasi ke supervisor. Resolusi dalam 4 jam.", "nba_priority": "critical",
        },
        {
            "name": "Budi Santoso", "session": "sess-013", "contact_type": "student",
            "school_origin": None, "school_type": None,
            "program": None, "funnel": "decision", "urgency": "critical",
            "language": "id", "intent": "complaint", "confidence": 0.97,
            "sentiment": "frustrated", "message": "Website error terus pas mau upload dokumen! Deadline besok!",
            "response": "Halo Kak Budi! 🙏 Mohon maaf atas gangguan teknisnya! Kami paham ini sangat urgent karena deadline besok.\n\nSolusi cepat:\n1. **Coba browser lain** (Chrome/Firefox recommended)\n2. **Pastikan file < 5MB** format PDF/JPG\n3. **Kalau masih error**, kirim dokumen via email ke: admisi@luminara.ac.id dengan subject \"URGENT - Upload Dokumen [Nama]\"\n\nKami akan pastikan dokumen Kak Budi diproses tepat waktu meski dikirim via email. Hubungi 021-7890-1234 jika butuh bantuan langsung. 💪",
            "nba_type": "escalate", "nba_detail": "Eskalasi ke supervisor + tim IT. Resolusi dalam 4 jam.", "nba_priority": "critical",
        },
        {
            "name": None, "session": "sess-014", "contact_type": "unknown",
            "school_origin": None, "school_type": None,
            "program": None, "funnel": "awareness", "urgency": "low",
            "language": "id", "intent": "ambiguous", "confidence": 0.4,
            "sentiment": "neutral", "message": "info dong",
            "response": "Halo! 😊 Terima kasih sudah menghubungi Universitas Luminara! Apa yang ingin diketahui?\n\n📚 **Program Studi** — 5 prodi unggulan\n💰 **Biaya & Beasiswa** — mulai Rp 10 juta + berbagai beasiswa\n📝 **Cara Mendaftar** — pendaftaran online mudah\n📊 **Status Pendaftaran** — cek progress\n\nSilakan pilih topik atau langsung tanyakan ya! 🙌",
            "nba_type": "auto_respond", "nba_detail": "Auto-respond + schedule follow-up 3 hari", "nba_priority": "low",
        },
        {
            "name": "Fajar Hidayat", "session": "sess-015", "contact_type": "student",
            "school_origin": "SMA Negeri 7 Jakarta", "school_type": "SMA",
            "program": "Desain Komunikasi Visual", "funnel": "decision", "urgency": "high",
            "language": "id", "intent": "inquiry_prodi", "confidence": 0.90,
            "sentiment": "excited", "message": "Jurusan DKV ada? Biayanya berapa? Ada beasiswa? Saya mau daftar!",
            "response": "Halo Kak Fajar! 🎨 Wah antusias sekali! Yuk dijawab satu-satu:\n\n✅ **DKV ada!** Desain Komunikasi Visual (Akreditasi B+), Fakultas Desain & Seni\n💰 **Biaya**: Rp 13 juta/semester, pendaftaran Rp 5 juta\n🎓 **Beasiswa**: Prestasi (25-100%), KIP Kuliah (100%), Luminara Berprestasi (30-75%)\n📝 **Cara daftar**: portal.luminara.ac.id → upload dokumen → bayar Rp 350rb → tes seleksi\n\nKurikulumnya keren: UI/UX Design, Motion Graphics, Brand Identity, Typography. Mau langsung daftar? 🚀",
            "nba_type": "fast_track", "nba_detail": "Fast-track pendaftaran + bantuan personal", "nba_priority": "high",
        },
        {
            "name": "Kevin Tan", "session": "sess-016", "contact_type": "student",
            "school_origin": "ACS International Singapore", "school_type": "International",
            "program": "Teknik Informatika", "funnel": "interest", "urgency": "medium",
            "language": "mixed", "intent": "inquiry_prodi", "confidence": 0.89,
            "sentiment": "neutral", "message": "Hi kak, I'm from Singapore. Mau tanya soal prodi computer science dong, ada English track ga?",
            "response": "Hi Kak Kevin! 😊 Welcome from Singapore! Yes, our Computer Science (Teknik Informatika) program supports English-medium instruction for international students.\n\nProgram highlights:\n- AI & Machine Learning, Cloud Computing, Cybersecurity\n- Akreditasi A, 8 semester, 144 SKS\n- Biaya: Rp 12.5 juta/semester (~800 USD)\n- Magang di 100+ perusahaan mitra\n\nFor international students, you'll need TOEFL ≥500 atau IELTS ≥5.5. We also help with student visa! 🎓\n\nMau tahu lebih detail atau langsung apply?",
            "nba_type": "invite_tour", "nba_detail": "Undang campus tour / webinar terdekat", "nba_priority": "medium",
        },
        {
            "name": "Ibu Sari", "session": "sess-017", "contact_type": "counselor",
            "school_origin": "SMAN 3 Depok", "school_type": "SMA",
            "program": None, "funnel": "awareness", "urgency": "medium",
            "language": "id", "intent": "partnership", "confidence": 0.94,
            "sentiment": "neutral", "message": "Saya Ibu Sari, guru BK SMAN 3 Depok. Ada 5 siswa yang tertarik. Bisa atur kunjungan kampus?",
            "response": "Selamat siang, Ibu Sari! 🙏 Terima kasih atas minat siswa-siswa SMAN 3 Depok!\n\nTentu bisa! Kami menyediakan program kunjungan kampus yang meliputi:\n- Tour fasilitas (lab, perpustakaan, studio)\n- Presentasi program studi\n- Sesi tanya jawab dengan dosen\n- Info beasiswa khusus\n\nUntuk mengatur jadwal kunjungan (gratis), silakan:\n📧 Email: admisi@luminara.ac.id\n📞 Telepon: 021-7890-1234\n\nKami bisa menjadwalkan untuk kelompok 5+ siswa di hari Selasa atau Kamis. Kapan waktu yang cocok untuk Ibu Sari dan siswa-siswa? 😊",
            "nba_type": "assign_counselor", "nba_detail": "Assign konselor + koordinasi kunjungan kampus", "nba_priority": "medium",
        },
    ]
    
    for i, s in enumerate(scenarios):
        lead_id = str(uuid.uuid4())
        msg_id = str(uuid.uuid4())
        resp_id = str(uuid.uuid4())
        draft_id = str(uuid.uuid4())
        action_id = str(uuid.uuid4())
        ts = (now - timedelta(hours=len(scenarios) - i)).isoformat()
        
        # Insert lead
        cursor.execute("""
            INSERT INTO leads (id, session_id, name, contact_type, language_pref,
                               school_origin, school_type, interested_program,
                               financial_concern, funnel_stage, urgency,
                               channel, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'chatbot', ?, ?)
        """, (
            lead_id, s["session"], s.get("name"), s["contact_type"],
            s["language"], s.get("school_origin"), s.get("school_type"),
            s.get("program"), 1 if s.get("financial_concern") else 0,
            s["funnel"], s["urgency"], ts, ts
        ))
        
        # Insert inbound message
        processing_log = json.dumps({
            "message_id": msg_id, "timestamp": ts,
            "raw_input": s["message"],
            "total_processing_time_ms": 2500,
            "steps": [
                {"step": "language_detection", "order": 1, "result": s["language"], "confidence": 0.95, "reasoning": f"Detected {s['language']}", "time_ms": 50},
                {"step": "intent_classification", "order": 2, "result": s["intent"], "confidence": s["confidence"], "reasoning": f"Classified as {s['intent']}", "time_ms": 800},
                {"step": "entity_extraction", "order": 3, "result": {"contact_type": s["contact_type"]}, "confidence": 0.85, "reasoning": "Extracted entities", "time_ms": 400},
                {"step": "sentiment_analysis", "order": 4, "result": s["sentiment"], "confidence": 0.8, "reasoning": f"Sentiment: {s['sentiment']}", "time_ms": 200},
                {"step": "funnel_staging", "order": 5, "result": s["funnel"], "confidence": 0.85, "reasoning": f"Stage: {s['funnel']}", "time_ms": 100},
                {"step": "urgency_scoring", "order": 6, "result": s["urgency"], "confidence": 0.9, "reasoning": f"Urgency: {s['urgency']}", "time_ms": 50},
                {"step": "response_generation", "order": 7, "result": "generated", "confidence": 0.9, "reasoning": "Personalized response generated", "time_ms": 800},
                {"step": "next_best_action", "order": 8, "result": {"action_type": s["nba_type"]}, "confidence": 0.85, "reasoning": s["nba_detail"], "time_ms": 100},
            ]
        }, ensure_ascii=False)
        
        cursor.execute("""
            INSERT INTO messages (id, lead_id, direction, content, language, intent,
                                  intent_confidence, sentiment, processing_log,
                                  processing_time_ms, created_at)
            VALUES (?, ?, 'inbound', ?, ?, ?, ?, ?, ?, 2500, ?)
        """, (msg_id, lead_id, s["message"], s["language"], s["intent"],
              s["confidence"], s["sentiment"], processing_log, ts))
        
        # Insert outbound response
        cursor.execute("""
            INSERT INTO messages (id, lead_id, direction, content, language, created_at)
            VALUES (?, ?, 'outbound', ?, ?, ?)
        """, (resp_id, lead_id, s["response"], s["language"], ts))
        
        # Insert draft response
        cursor.execute("""
            INSERT INTO draft_responses (id, message_id, lead_id, content, status, created_at)
            VALUES (?, ?, ?, ?, 'sent', ?)
        """, (draft_id, msg_id, lead_id, s["response"], ts))
        
        # Insert next action
        cursor.execute("""
            INSERT INTO next_actions (id, lead_id, action_type, action_detail,
                                      priority, reasoning, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (action_id, lead_id, s["nba_type"], s["nba_detail"],
              s["nba_priority"], f"Funnel: {s['funnel']}, Urgency: {s['urgency']}", ts))
    
    conn.commit()
    conn.close()
    print(f"✅ Seeded {len(scenarios)} demo scenarios.")
