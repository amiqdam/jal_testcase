"""
Seed data — 10 test users with multi-turn journeys.
Each user has realistic conversations with complete processing logs.
"""
import uuid
import json
from datetime import datetime, timezone, timedelta
from backend.database.connection import get_db


def seed_data():
    """Seed the database with 10 test users and their conversations."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if data already exists
    cursor.execute("SELECT COUNT(*) as count FROM leads")
    if cursor.fetchone()["count"] > 0:
        print("📌 Database already seeded. Skipping.")
        conn.close()
        return
    
    now = datetime.now(timezone.utc)
    
    # ========== TEST USERS ==========
    
    users = [
        # User 1: Awareness → Interest (2 messages)
        {
            "email": "user1@test.com",
            "name": "Dina Permata",
            "contact_type": "student",
            "lead_source": "media_sosial",
            "funnel_stage": "interest",
            "urgency": "low",
            "macro_intent": "INQUIRY",
            "micro_intent": "academic_inquiry",
            "messages": [
                {"content": "Halooo kak, mau tanya dong kampusnya ada jurusan apa aja sih?", "direction": "inbound",
                 "macro": "INQUIRY", "micro": "general_inquiry", "conf": 0.88,
                 "trace": [
                     {"agent": "Classifier Agent", "thought": "User menggunakan bahasa Indonesia informal ('halooo kak', 'dong'). Pertanyaan umum tentang jurusan → general_inquiry.", "action": "LLM Classification → INQUIRY/general_inquiry", "observation": "language=id, macro=INQUIRY, micro=general_inquiry, urgency=low, confidence=0.88", "confidence": 0.88, "time_ms": 450},
                     {"agent": "Profiler Agent", "thought": "'kak' mengindikasikan user adalah siswa. Belum menyebut jurusan spesifik.", "action": "Entity Extraction → found 1 profile fields", "observation": "entities={contact_type: student}", "confidence": 0.75, "time_ms": 380},
                     {"agent": "Funnel Stager Agent", "thought": "Current stage: awareness. INQUIRY/general_inquiry → awareness. Stage unchanged.", "action": "Rule-based staging → awareness", "observation": "Stage unchanged: awareness", "confidence": 0.95, "time_ms": 2},
                     {"agent": "Response Agent", "thought": "Generating response for general inquiry about available programs.", "action": "LLM Response Generation (personalization signals: [])", "observation": "Generated 180 chars response.", "confidence": 0.85, "time_ms": 820},
                     {"agent": "NBA Agent", "thought": "Looking up NBA matrix for funnel=awareness, urgency=low.", "action": "Rule-based matrix → auto_respond", "observation": "Action: auto_respond — schedule follow-up 3 hari.", "confidence": 0.95, "time_ms": 1}
                 ]},
                {"content": "Wah keren! Kalo Teknik Informatika belajar apa aja kak? Ada AI nya ga?", "direction": "inbound",
                 "macro": "INQUIRY", "micro": "academic_inquiry", "conf": 0.92,
                 "trace": [
                     {"agent": "Classifier Agent", "thought": "User menanyakan detail kurikulum TI spesifik (AI). Ini sudah masuk ranah academic_inquiry karena menyebut program studi.", "action": "LLM Classification → INQUIRY/academic_inquiry", "observation": "language=id, macro=INQUIRY, micro=academic_inquiry, urgency=low, confidence=0.92", "confidence": 0.92, "time_ms": 410},
                     {"agent": "Profiler Agent", "thought": "'Teknik Informatika' → interested_program. User tertarik AI/ML.", "action": "Entity Extraction → found 1 profile fields", "observation": "entities={interested_program: Teknik Informatika}", "confidence": 0.90, "time_ms": 350},
                     {"agent": "Funnel Stager Agent", "thought": "INQUIRY/academic_inquiry → interest. Advancing from awareness → interest.", "action": "Rule-based staging → interest", "observation": "✅ Stage advanced: awareness → interest", "confidence": 0.95, "time_ms": 1},
                     {"agent": "Response Agent", "thought": "Inject TI curriculum details, highlight AI & ML tracks.", "action": "LLM Response Generation (personalization signals: [name_personalization])", "observation": "Generated 250 chars response with TI details.", "confidence": 0.88, "time_ms": 900},
                     {"agent": "NBA Agent", "thought": "interest + low → send_brochure", "action": "Rule-based matrix → send_brochure", "observation": "Action: send_brochure — program-specific details + follow-up.", "confidence": 0.95, "time_ms": 1}
                 ]},
            ]
        },
        # User 2: Awareness → Consideration (2 messages, beasiswa)
        {
            "email": "user2@test.com",
            "name": "Rizky Aditya",
            "contact_type": "student",
            "lead_source": "website",
            "funnel_stage": "consideration",
            "urgency": "low",
            "macro_intent": "INQUIRY",
            "micro_intent": "financial_inquiry",
            "messages": [
                {"content": "Assalamualaikum, mau tanya info kampus JAL University dong", "direction": "inbound",
                 "macro": "INQUIRY", "micro": "general_inquiry", "conf": 0.85,
                 "trace": [
                     {"agent": "Classifier Agent", "thought": "Greeting islami + pertanyaan umum ('info kampus'). Belum spesifik.", "action": "LLM Classification → INQUIRY/general_inquiry", "observation": "language=id, macro=INQUIRY, micro=general_inquiry, urgency=low, confidence=0.85", "confidence": 0.85, "time_ms": 430},
                     {"agent": "Profiler Agent", "thought": "Tidak ada entitas spesifik yang disebutkan.", "action": "Entity Extraction → found 0 profile fields", "observation": "entities={}", "confidence": 0.5, "time_ms": 300},
                     {"agent": "Funnel Stager Agent", "thought": "INQUIRY/general_inquiry → awareness.", "action": "Rule-based staging → awareness", "observation": "Stage unchanged: awareness", "confidence": 0.95, "time_ms": 1},
                     {"agent": "Response Agent", "thought": "General welcome with campus overview.", "action": "LLM Response Generation", "observation": "Generated 200 chars response.", "confidence": 0.85, "time_ms": 780},
                     {"agent": "NBA Agent", "thought": "awareness + low → auto_respond", "action": "Rule-based matrix → auto_respond", "observation": "Action: auto_respond", "confidence": 0.95, "time_ms": 1}
                 ]},
                {"content": "Kak biaya kuliah berapa ya? Ada beasiswa ga? Keluarga saya kurang mampu 😢", "direction": "inbound",
                 "macro": "INQUIRY", "micro": "financial_inquiry", "conf": 0.94,
                 "trace": [
                     {"agent": "Classifier Agent", "thought": "Multi-topic: biaya + beasiswa + indikasi financial concern ('kurang mampu' + emoji sedih). Primary: financial_inquiry.", "action": "LLM Classification → INQUIRY/financial_inquiry", "observation": "language=id, macro=INQUIRY, micro=financial_inquiry, urgency=low, confidence=0.94, sentiment=anxious", "confidence": 0.94, "time_ms": 480},
                     {"agent": "Profiler Agent", "thought": "'kurang mampu' → financial_concern=true. Belum sebut jurusan.", "action": "Entity Extraction → found 1 profile fields", "observation": "entities={financial_concern: true}", "confidence": 0.88, "time_ms": 360},
                     {"agent": "Funnel Stager Agent", "thought": "INQUIRY/financial_inquiry → consideration. Advancing: awareness → consideration.", "action": "Rule-based staging → consideration", "observation": "✅ Stage advanced: awareness → consideration", "confidence": 0.95, "time_ms": 1},
                     {"agent": "Response Agent", "thought": "Proaktif mention KIP Kuliah dan beasiswa. Tone: reassuring (anxious sentiment).", "action": "LLM Response Generation (personalization signals: [financial_proactive])", "observation": "Generated 300 chars response with scholarship details.", "confidence": 0.90, "time_ms": 950},
                     {"agent": "NBA Agent", "thought": "consideration + low → connect_alumni", "action": "Rule-based matrix → connect_alumni", "observation": "Action: connect_alumni", "confidence": 0.95, "time_ms": 1}
                 ]},
            ]
        },
        # User 3: Interest → Decision (2 messages, mixed EN/ID)
        {
            "email": "user3@test.com",
            "name": "Sarah Tan",
            "contact_type": "student",
            "lead_source": "event",
            "funnel_stage": "decision",
            "urgency": "medium",
            "macro_intent": "TRANSACTIONAL",
            "micro_intent": "registration_process",
            "interested_program": "Manajemen",
            "messages": [
                {"content": "Hi, I'm interested in the Management program. What's the curriculum like?", "direction": "inbound",
                 "macro": "INQUIRY", "micro": "academic_inquiry", "conf": 0.91,
                 "trace": [
                     {"agent": "Classifier Agent", "thought": "English message. Interested in specific program (Management). academic_inquiry.", "action": "LLM Classification → INQUIRY/academic_inquiry", "observation": "language=en, macro=INQUIRY, micro=academic_inquiry, urgency=low, confidence=0.91", "confidence": 0.91, "time_ms": 420},
                     {"agent": "Profiler Agent", "thought": "'Management program' → interested_program=Manajemen.", "action": "Entity Extraction → found 1 profile fields", "observation": "entities={interested_program: Manajemen}", "confidence": 0.85, "time_ms": 340},
                     {"agent": "Funnel Stager Agent", "thought": "INQUIRY/academic_inquiry → interest.", "action": "Rule-based staging → interest", "observation": "Stage set: interest", "confidence": 0.95, "time_ms": 1},
                     {"agent": "Response Agent", "thought": "English response with Management curriculum details.", "action": "LLM Response Generation (personalization signals: [english_response])", "observation": "Generated 280 chars EN response.", "confidence": 0.87, "time_ms": 870},
                     {"agent": "NBA Agent", "thought": "interest + low → send_brochure", "action": "Rule-based matrix → send_brochure", "observation": "Action: send_brochure", "confidence": 0.95, "time_ms": 1}
                 ]},
                {"content": "This looks great! Gimana caranya daftar? Saya mau apply sekarang.", "direction": "inbound",
                 "macro": "TRANSACTIONAL", "micro": "registration_process", "conf": 0.93,
                 "trace": [
                     {"agent": "Classifier Agent", "thought": "Code-switching EN→ID. Explicit registration intent ('mau apply sekarang'). Transactional.", "action": "LLM Classification → TRANSACTIONAL/registration_process", "observation": "language=mixed, macro=TRANSACTIONAL, micro=registration_process, urgency=medium, confidence=0.93", "confidence": 0.93, "time_ms": 440},
                     {"agent": "Profiler Agent", "thought": "No new entities. Already have interested_program.", "action": "Entity Extraction → found 0 profile fields", "observation": "entities={}", "confidence": 0.5, "time_ms": 310},
                     {"agent": "Funnel Stager Agent", "thought": "TRANSACTIONAL/registration_process → decision. Advancing: interest → decision.", "action": "Rule-based staging → decision", "observation": "✅ Stage advanced: interest → decision", "confidence": 0.95, "time_ms": 1},
                     {"agent": "Response Agent", "thought": "Registration steps in mixed language. CTA: direct to portal.", "action": "LLM Response Generation", "observation": "Generated 250 chars response with registration steps.", "confidence": 0.88, "time_ms": 850},
                     {"agent": "NBA Agent", "thought": "decision + medium → fast_track", "action": "Rule-based matrix → fast_track", "observation": "Action: fast_track — priority processing.", "confidence": 0.95, "time_ms": 1}
                 ]},
            ]
        },
        # User 4: Consideration → Enrolled (3 messages: biaya → complaint → enrolled)
        {
            "email": "user4@test.com",
            "name": "Budi Santoso",
            "contact_type": "parent",
            "lead_source": "referral",
            "funnel_stage": "enrolled",
            "urgency": "low",
            "macro_intent": "TRANSACTIONAL",
            "micro_intent": "status_follow_up",
            "messages": [
                {"content": "Selamat siang, saya orang tua dari Budi Jr. Mau tanya biaya kuliah Teknik Informatika dan apakah bisa cicil?", "direction": "inbound",
                 "macro": "INQUIRY", "micro": "financial_inquiry", "conf": 0.90,
                 "trace": [
                     {"agent": "Classifier Agent", "thought": "'orang tua' → parent. Financial inquiry (biaya + cicilan). Specific program TI.", "action": "LLM Classification → INQUIRY/financial_inquiry", "observation": "language=id, macro=INQUIRY, micro=financial_inquiry, urgency=medium, confidence=0.90, sentiment=neutral", "confidence": 0.90, "time_ms": 460},
                     {"agent": "Profiler Agent", "thought": "contact_type=parent, interested_program=Teknik Informatika.", "action": "Entity Extraction → found 2 profile fields", "observation": "entities={contact_type: parent, interested_program: Teknik Informatika}", "confidence": 0.92, "time_ms": 370},
                     {"agent": "Funnel Stager Agent", "thought": "INQUIRY/financial_inquiry → consideration.", "action": "Rule-based staging → consideration", "observation": "Stage set: consideration", "confidence": 0.95, "time_ms": 1},
                     {"agent": "Response Agent", "thought": "Sapaan 'Bapak/Ibu' untuk parent. TI tuition + cicilan info.", "action": "LLM Response Generation", "observation": "Generated 280 chars parent-tone response.", "confidence": 0.88, "time_ms": 880},
                     {"agent": "NBA Agent", "thought": "consideration + medium → assign_counselor", "action": "Rule-based matrix → assign_counselor", "observation": "Action: assign_counselor", "confidence": 0.95, "time_ms": 1}
                 ]},
                {"content": "Website pendaftarannya error terus ya! Sudah coba 3 kali, deadline besok kan? Tolong dibantu dong", "direction": "inbound",
                 "macro": "SUPPORT", "micro": "technical_issue", "conf": 0.95,
                 "trace": [
                     {"agent": "Classifier Agent", "thought": "'error terus' + 'deadline besok' + repeated attempts → SUPPORT/technical_issue + critical urgency.", "action": "LLM Classification → SUPPORT/technical_issue", "observation": "language=id, macro=SUPPORT, micro=technical_issue, urgency=critical, confidence=0.95, sentiment=frustrated", "confidence": 0.95, "time_ms": 400},
                     {"agent": "Profiler Agent", "thought": "No new profile entities from this complaint.", "action": "Entity Extraction → found 0 profile fields", "observation": "entities={}", "confidence": 0.5, "time_ms": 280},
                     {"agent": "Funnel Stager Agent", "thought": "SUPPORT → minimum consideration. Already at consideration. Stage unchanged.", "action": "Rule-based staging → consideration", "observation": "Stage unchanged: consideration", "confidence": 0.95, "time_ms": 1},
                     {"agent": "Response Agent", "thought": "Empathetic tone, apologize for tech issue. Provide alternative contact.", "action": "LLM Response Generation", "observation": "Generated 220 chars empathetic response.", "confidence": 0.85, "time_ms": 820},
                     {"agent": "NBA Agent", "thought": "SUPPORT + critical → escalate", "action": "Rule-based matrix → escalate", "observation": "Action: escalate — IT team resolve within 4h.", "confidence": 0.95, "time_ms": 1}
                 ]},
                {"content": "Alhamdulillah sudah bisa daftar dan anak saya sudah diterima! Terima kasih banyak 🙏", "direction": "inbound",
                 "macro": "TRANSACTIONAL", "micro": "status_follow_up", "conf": 0.87,
                 "trace": [
                     {"agent": "Classifier Agent", "thought": "'sudah diterima' → enrollment confirmation. Positive sentiment.", "action": "LLM Classification → TRANSACTIONAL/status_follow_up", "observation": "language=id, macro=TRANSACTIONAL, micro=status_follow_up, urgency=low, confidence=0.87, sentiment=excited", "confidence": 0.87, "time_ms": 390},
                     {"agent": "Profiler Agent", "thought": "No new entities. Enrollment confirmed.", "action": "Entity Extraction → found 0 profile fields", "observation": "entities={}", "confidence": 0.5, "time_ms": 270},
                     {"agent": "Funnel Stager Agent", "thought": "'sudah diterima' keyword detected → enrolled. Advancing: consideration → enrolled.", "action": "Rule-based staging → enrolled", "observation": "✅ Stage advanced: consideration → enrolled", "confidence": 0.95, "time_ms": 1},
                     {"agent": "Response Agent", "thought": "Congratulations message. Welcome to JAL University.", "action": "LLM Response Generation", "observation": "Generated 200 chars celebratory response.", "confidence": 0.90, "time_ms": 750},
                     {"agent": "NBA Agent", "thought": "enrolled + low → auto_respond", "action": "Rule-based matrix → auto_respond", "observation": "Action: auto_respond — welcome package.", "confidence": 0.95, "time_ms": 1}
                 ]},
            ]
        },
        # User 5: Full journey - Awareness → Enrolled (5 messages)
        {
            "email": "user5@test.com",
            "name": "Putri Handayani",
            "contact_type": "student",
            "lead_source": "formulir_pendaftaran",
            "funnel_stage": "enrolled",
            "urgency": "low",
            "macro_intent": "TRANSACTIONAL",
            "micro_intent": "status_follow_up",
            "interested_program": "Desain Komunikasi Visual",
            "messages": [
                {"content": "Hai, mau tanya dong kalo kuliah di JAL itu gimana ya? Bagus ga?", "direction": "inbound",
                 "macro": "INQUIRY", "micro": "general_inquiry", "conf": 0.86, "trace": [
                     {"agent": "Classifier Agent", "thought": "General question about campus quality. Awareness stage.", "action": "LLM Classification → INQUIRY/general_inquiry", "observation": "language=id, confidence=0.86", "confidence": 0.86, "time_ms": 420},
                     {"agent": "Profiler Agent", "thought": "Student (informal 'hai'). No specific program mentioned.", "action": "Entity Extraction → found 1 fields", "observation": "entities={contact_type: student}", "confidence": 0.7, "time_ms": 320},
                     {"agent": "Funnel Stager Agent", "thought": "general_inquiry → awareness.", "action": "Rule-based → awareness", "observation": "Stage: awareness", "confidence": 0.95, "time_ms": 1},
                     {"agent": "Response Agent", "thought": "Welcome + campus highlights.", "action": "LLM Response", "observation": "200 chars", "confidence": 0.85, "time_ms": 800},
                     {"agent": "NBA Agent", "thought": "awareness + low", "action": "auto_respond", "observation": "auto_respond", "confidence": 0.95, "time_ms": 1}]},
                {"content": "Wah ada DKV ternyata! Saya suka desain nih. Kurikulumnya gimana ya?", "direction": "inbound",
                 "macro": "INQUIRY", "micro": "academic_inquiry", "conf": 0.91, "trace": [
                     {"agent": "Classifier Agent", "thought": "Specific program: DKV. Academic inquiry about curriculum.", "action": "LLM Classification → INQUIRY/academic_inquiry", "observation": "language=id, confidence=0.91", "confidence": 0.91, "time_ms": 430},
                     {"agent": "Profiler Agent", "thought": "DKV → interested_program.", "action": "Entity Extraction → found 1 fields", "observation": "entities={interested_program: DKV}", "confidence": 0.88, "time_ms": 330},
                     {"agent": "Funnel Stager Agent", "thought": "academic_inquiry → interest. Advancing.", "action": "Rule-based → interest", "observation": "✅ awareness → interest", "confidence": 0.95, "time_ms": 1},
                     {"agent": "Response Agent", "thought": "DKV curriculum, UI/UX track, notable lecturers.", "action": "LLM Response", "observation": "280 chars", "confidence": 0.88, "time_ms": 900},
                     {"agent": "NBA Agent", "thought": "interest + low", "action": "send_brochure", "observation": "send_brochure", "confidence": 0.95, "time_ms": 1}]},
                {"content": "Berapa biaya semesternya untuk DKV? Ada beasiswa seni ga?", "direction": "inbound",
                 "macro": "INQUIRY", "micro": "financial_inquiry", "conf": 0.93, "trace": [
                     {"agent": "Classifier Agent", "thought": "Cost + scholarship question → financial_inquiry.", "action": "LLM Classification → INQUIRY/financial_inquiry", "observation": "language=id, confidence=0.93", "confidence": 0.93, "time_ms": 440},
                     {"agent": "Profiler Agent", "thought": "Interested in scholarship → possible financial_concern.", "action": "Entity Extraction → found 0 fields", "observation": "entities={}", "confidence": 0.5, "time_ms": 300},
                     {"agent": "Funnel Stager Agent", "thought": "financial_inquiry → consideration. Advancing.", "action": "Rule-based → consideration", "observation": "✅ interest → consideration", "confidence": 0.95, "time_ms": 1},
                     {"agent": "Response Agent", "thought": "DKV tuition + scholarship options.", "action": "LLM Response", "observation": "250 chars", "confidence": 0.87, "time_ms": 850},
                     {"agent": "NBA Agent", "thought": "consideration + low", "action": "connect_alumni", "observation": "connect_alumni", "confidence": 0.95, "time_ms": 1}]},
                {"content": "Oke saya mau daftar! Gimana caranya kak?", "direction": "inbound",
                 "macro": "TRANSACTIONAL", "micro": "registration_process", "conf": 0.95, "trace": [
                     {"agent": "Classifier Agent", "thought": "Explicit registration intent ('mau daftar').", "action": "LLM Classification → TRANSACTIONAL/registration_process", "observation": "language=id, confidence=0.95", "confidence": 0.95, "time_ms": 380},
                     {"agent": "Profiler Agent", "thought": "No new entities.", "action": "Entity Extraction → found 0 fields", "observation": "entities={}", "confidence": 0.5, "time_ms": 260},
                     {"agent": "Funnel Stager Agent", "thought": "registration_process → decision. Advancing.", "action": "Rule-based → decision", "observation": "✅ consideration → decision", "confidence": 0.95, "time_ms": 1},
                     {"agent": "Response Agent", "thought": "Step-by-step registration guide.", "action": "LLM Response", "observation": "300 chars", "confidence": 0.90, "time_ms": 880},
                     {"agent": "NBA Agent", "thought": "decision + low", "action": "fast_track", "observation": "fast_track", "confidence": 0.95, "time_ms": 1}]},
                {"content": "Yeay saya sudah diterima di DKV! Kapan ya orientasinya?", "direction": "inbound",
                 "macro": "TRANSACTIONAL", "micro": "status_follow_up", "conf": 0.88, "trace": [
                     {"agent": "Classifier Agent", "thought": "'sudah diterima' → enrolled. Asking about orientation.", "action": "LLM Classification → TRANSACTIONAL/status_follow_up", "observation": "language=id, confidence=0.88", "confidence": 0.88, "time_ms": 400},
                     {"agent": "Profiler Agent", "thought": "Enrollment confirmed. DKV.", "action": "Entity Extraction → found 0 fields", "observation": "entities={}", "confidence": 0.5, "time_ms": 270},
                     {"agent": "Funnel Stager Agent", "thought": "'sudah diterima' keyword → enrolled. Advancing.", "action": "Rule-based → enrolled", "observation": "✅ decision → enrolled", "confidence": 0.95, "time_ms": 1},
                     {"agent": "Response Agent", "thought": "Congratulations + JAL Week orientation info.", "action": "LLM Response", "observation": "220 chars", "confidence": 0.88, "time_ms": 780},
                     {"agent": "NBA Agent", "thought": "enrolled + low", "action": "auto_respond", "observation": "auto_respond — welcome package", "confidence": 0.95, "time_ms": 1}]},
            ]
        },
        # User 6: Awareness only (slang, 1 message)
        {
            "email": "user6@test.com",
            "name": "Rangga Pratama",
            "contact_type": "student",
            "lead_source": "media_sosial",
            "funnel_stage": "awareness",
            "urgency": "low",
            "macro_intent": "AMBIGUOUS",
            "micro_intent": "greeting_unclear",
            "messages": [
                {"content": "eh bro kampus lo bgs ga sih? gw denger2 oke", "direction": "inbound",
                 "macro": "AMBIGUOUS", "micro": "greeting_unclear", "conf": 0.65, "trace": [
                     {"agent": "Classifier Agent", "thought": "Sangat informal/slang ('bro', 'lo', 'gw'). Pertanyaan terlalu umum. Low confidence classification.", "action": "LLM Classification → AMBIGUOUS/greeting_unclear", "observation": "language=id, macro=AMBIGUOUS, micro=greeting_unclear, urgency=low, confidence=0.65", "confidence": 0.65, "time_ms": 450},
                     {"agent": "Profiler Agent", "thought": "Very informal → student. No specific info.", "action": "Entity Extraction → found 1 fields", "observation": "entities={contact_type: student}", "confidence": 0.6, "time_ms": 320},
                     {"agent": "Funnel Stager Agent", "thought": "AMBIGUOUS/greeting_unclear → awareness.", "action": "Rule-based → awareness", "observation": "Stage: awareness", "confidence": 0.95, "time_ms": 1},
                     {"agent": "Response Agent", "thought": "Friendly, match some informal tone. Provide options to explore.", "action": "LLM Response", "observation": "150 chars casual response.", "confidence": 0.80, "time_ms": 750},
                     {"agent": "NBA Agent", "thought": "awareness + low", "action": "auto_respond", "observation": "auto_respond + follow-up 3 hari", "confidence": 0.95, "time_ms": 1}]},
            ]
        },
        # User 7: Interest only (English, 1 message)
        {
            "email": "user7@test.com",
            "name": "James Wong",
            "contact_type": "student",
            "lead_source": "website",
            "funnel_stage": "interest",
            "urgency": "low",
            "macro_intent": "INQUIRY",
            "micro_intent": "academic_inquiry",
            "nationality": "Malaysian",
            "interested_program": "Teknik Informatika",
            "messages": [
                {"content": "Hello! I'm from Malaysia and interested in Computer Science. Do you accept international students?", "direction": "inbound",
                 "macro": "INQUIRY", "micro": "academic_inquiry", "conf": 0.90, "trace": [
                     {"agent": "Classifier Agent", "thought": "English message. International student from Malaysia. CS interest → academic_inquiry.", "action": "LLM Classification → INQUIRY/academic_inquiry", "observation": "language=en, macro=INQUIRY, micro=academic_inquiry, urgency=low, confidence=0.90", "confidence": 0.90, "time_ms": 430},
                     {"agent": "Profiler Agent", "thought": "Malaysia → nationality. CS → interested_program=Teknik Informatika. International student.", "action": "Entity Extraction → found 2 fields", "observation": "entities={nationality: Malaysian, interested_program: Teknik Informatika}", "confidence": 0.88, "time_ms": 350},
                     {"agent": "Funnel Stager Agent", "thought": "academic_inquiry → interest.", "action": "Rule-based → interest", "observation": "Stage: interest", "confidence": 0.95, "time_ms": 1},
                     {"agent": "Response Agent", "thought": "English response. International student requirements + TI program.", "action": "LLM Response (personalization: english_response)", "observation": "280 chars EN.", "confidence": 0.87, "time_ms": 880},
                     {"agent": "NBA Agent", "thought": "interest + low", "action": "send_brochure", "observation": "send_brochure — international student guide", "confidence": 0.95, "time_ms": 1}]},
            ]
        },
        # User 8: Consideration only (1 message)
        {
            "email": "user8@test.com",
            "name": "Mega Wulandari",
            "contact_type": "student",
            "lead_source": "event",
            "funnel_stage": "consideration",
            "urgency": "medium",
            "macro_intent": "INQUIRY",
            "micro_intent": "financial_inquiry",
            "interested_program": "Psikologi",
            "messages": [
                {"content": "Kak mau tanya, kalo Psikologi biayanya berapa per semester? Saya juara 1 olimpiade psikologi tingkat kota, bisa dapat beasiswa ga?", "direction": "inbound",
                 "macro": "INQUIRY", "micro": "financial_inquiry", "conf": 0.93, "trace": [
                     {"agent": "Classifier Agent", "thought": "Financial + scholarship question. Mentions academic achievement (juara 1). Psikologi program.", "action": "LLM Classification → INQUIRY/financial_inquiry", "observation": "language=id, macro=INQUIRY, micro=financial_inquiry, urgency=medium, confidence=0.93", "confidence": 0.93, "time_ms": 470},
                     {"agent": "Profiler Agent", "thought": "Psikologi → interested_program. Juara 1 olimpiade → academic_achievement. Scholarship interest → financial_concern.", "action": "Entity Extraction → found 3 fields", "observation": "entities={interested_program: Psikologi, academic_achievement: Juara 1 olimpiade psikologi kota, financial_concern: true}", "confidence": 0.92, "time_ms": 380},
                     {"agent": "Funnel Stager Agent", "thought": "financial_inquiry → consideration.", "action": "Rule-based → consideration", "observation": "Stage: consideration", "confidence": 0.95, "time_ms": 1},
                     {"agent": "Response Agent", "thought": "Psikologi tuition + merit-based scholarship (she qualifies!). Proactive financial support.", "action": "LLM Response (personalization: financial_proactive)", "observation": "320 chars with scholarship calc.", "confidence": 0.90, "time_ms": 920},
                     {"agent": "NBA Agent", "thought": "consideration + medium", "action": "assign_counselor", "observation": "assign_counselor — scholarship consultation", "confidence": 0.95, "time_ms": 1}]},
            ]
        },
        # User 9: Decision only (follow-up, 1 message)
        {
            "email": "user9@test.com",
            "name": "Ahmad Fauzi",
            "contact_type": "student",
            "lead_source": "formulir_pendaftaran",
            "funnel_stage": "decision",
            "urgency": "medium",
            "macro_intent": "TRANSACTIONAL",
            "micro_intent": "status_follow_up",
            "messages": [
                {"content": "Kak saya sudah bayar biaya pendaftaran tapi statusnya belum berubah di portal. Ini gimana ya?", "direction": "inbound",
                 "macro": "TRANSACTIONAL", "micro": "status_follow_up", "conf": 0.91, "trace": [
                     {"agent": "Classifier Agent", "thought": "Status check after payment. Follow-up on registration process.", "action": "LLM Classification → TRANSACTIONAL/status_follow_up", "observation": "language=id, macro=TRANSACTIONAL, micro=status_follow_up, urgency=medium, confidence=0.91", "confidence": 0.91, "time_ms": 410},
                     {"agent": "Profiler Agent", "thought": "Already in registration process. Payment made.", "action": "Entity Extraction → found 0 fields", "observation": "entities={}", "confidence": 0.5, "time_ms": 290},
                     {"agent": "Funnel Stager Agent", "thought": "status_follow_up → decision. Already applied.", "action": "Rule-based → decision", "observation": "Stage: decision", "confidence": 0.95, "time_ms": 1},
                     {"agent": "Response Agent", "thought": "Reassuring response. Provide contact for payment verification.", "action": "LLM Response", "observation": "230 chars with support contact.", "confidence": 0.87, "time_ms": 830},
                     {"agent": "NBA Agent", "thought": "decision + medium", "action": "fast_track", "observation": "fast_track + priority processing", "confidence": 0.95, "time_ms": 1}]},
            ]
        },
        # User 10: Enrolled only (English, 1 message)
        {
            "email": "user10@test.com",
            "name": "Michelle Liu",
            "contact_type": "student",
            "lead_source": "website",
            "funnel_stage": "enrolled",
            "urgency": "low",
            "macro_intent": "INQUIRY",
            "micro_intent": "general_inquiry",
            "interested_program": "Sistem Informasi",
            "messages": [
                {"content": "I've been accepted into Information Systems! When does the orientation start? Also, is there a dorm available?", "direction": "inbound",
                 "macro": "INQUIRY", "micro": "general_inquiry", "conf": 0.85, "trace": [
                     {"agent": "Classifier Agent", "thought": "Enrolled student asking about orientation + dorm. General inquiry.", "action": "LLM Classification → INQUIRY/general_inquiry", "observation": "language=en, macro=INQUIRY, micro=general_inquiry, urgency=low, confidence=0.85", "confidence": 0.85, "time_ms": 430},
                     {"agent": "Profiler Agent", "thought": "'accepted into IS' → enrolled. Interested in dorm.", "action": "Entity Extraction → found 1 fields", "observation": "entities={interested_program: Sistem Informasi}", "confidence": 0.82, "time_ms": 340},
                     {"agent": "Funnel Stager Agent", "thought": "'been accepted' keyword → enrolled.", "action": "Rule-based → enrolled", "observation": "Stage: enrolled", "confidence": 0.95, "time_ms": 1},
                     {"agent": "Response Agent", "thought": "EN response. JAL Week orientation info + dorm details.", "action": "LLM Response (personalization: english_response)", "observation": "260 chars EN with orientation + dorm.", "confidence": 0.88, "time_ms": 860},
                     {"agent": "NBA Agent", "thought": "enrolled + low", "action": "auto_respond", "observation": "auto_respond — welcome package + dorm info", "confidence": 0.95, "time_ms": 1}]},
            ]
        },
    ]
    
    # ========== INSERT DATA ==========
    
    for i, user in enumerate(users):
        lead_id = str(uuid.uuid4())
        base_time = now - timedelta(hours=24 - i)
        
        # Insert lead
        cursor.execute("""
            INSERT INTO leads (id, email, name, contact_type, lead_source, funnel_stage, urgency,
                              macro_intent, micro_intent, interested_program, nationality,
                              created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (lead_id, user["email"], user["name"], user.get("contact_type", "unknown"),
              user["lead_source"], user["funnel_stage"], user["urgency"],
              user["macro_intent"], user["micro_intent"],
              user.get("interested_program"), user.get("nationality"),
              base_time.isoformat(), base_time.isoformat()))
        
        # Insert messages
        for j, msg in enumerate(user["messages"]):
            msg_time = base_time + timedelta(minutes=j * 5)
            
            msg_id = str(uuid.uuid4())
            resp_id = str(uuid.uuid4())
            
            processing_log = json.dumps({
                "message_id": msg_id,
                "timestamp": msg_time.isoformat(),
                "raw_input": msg["content"],
                "reasoning_trace": msg.get("trace", []),
                "macro_intent": msg["macro"],
                "micro_intent": msg["micro"],
                "classifier_confidence": msg["conf"],
            }, ensure_ascii=False)
            
            # Inbound message
            cursor.execute("""
                INSERT INTO messages (id, lead_id, direction, content, language, macro_intent, micro_intent,
                                      intent_confidence, processing_log, created_at)
                VALUES (?, ?, 'inbound', ?, 'id', ?, ?, ?, ?, ?)
            """, (msg_id, lead_id, msg["content"], msg["macro"], msg["micro"], msg["conf"],
                  processing_log, msg_time.isoformat()))
            
            # Outbound response
            resp_time = msg_time + timedelta(seconds=2)
            cursor.execute("""
                INSERT INTO messages (id, lead_id, direction, content, language, created_at)
                VALUES (?, ?, 'outbound', ?, 'id', ?)
            """, (resp_id, lead_id, f"[AI Response untuk {msg['micro']}]", resp_time.isoformat()))
            
            # NBA action
            action_id = str(uuid.uuid4())
            nba_map = {
                "awareness": ("auto_respond", "Auto-respond + follow-up 3 hari"),
                "interest": ("send_brochure", "Kirim info program spesifik"),
                "consideration": ("connect_alumni", "Hubungkan dengan alumni"),
                "decision": ("fast_track", "Fast-track pendaftaran"),
                "enrolled": ("auto_respond", "Welcome package"),
            }
            action_type, detail = nba_map.get(user["funnel_stage"], ("auto_respond", "Auto-respond"))
            cursor.execute("""
                INSERT INTO next_actions (id, lead_id, action_type, action_detail, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (action_id, lead_id, action_type, detail, user["urgency"], msg_time.isoformat()))
        
        # Add complaint for User 4 (technical issue)
        if user["email"] == "user4@test.com":
            complaint_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO complaints_log (id, lead_id, description, status, resolved_at, resolved_by, created_at)
                VALUES (?, ?, ?, 'resolved', ?, 'admin', ?)
            """, (complaint_id, lead_id, "Website pendaftaran error saat upload dokumen",
                  now.isoformat(), (base_time + timedelta(minutes=10)).isoformat()))
    
    conn.commit()
    conn.close()
    print(f"✅ Seeded {len(users)} test users with {sum(len(u['messages']) for u in users)} messages.")
