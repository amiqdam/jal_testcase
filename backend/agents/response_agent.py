"""
Response Agent — LLM-based personalized response generation.
Injects knowledge base context and applies personalization rules.
Includes guardrail: only answers university-related questions.
"""
import json
import time
from backend.agents.state import AdmissionState


RESPONSE_SYSTEM_PROMPT = """Kamu adalah AI Asisten Admisi untuk JAL University — universitas swasta terkemuka di Jakarta.

PERAN: Membantu calon mahasiswa, orang tua, dan guru BK dengan informasi yang akurat, personal, dan ramah.

## RULES PERSONALISASI:
1. **Bahasa**: Respons HARUS dalam bahasa yang sama dengan user (ID/EN/Mixed)
2. **Sapaan**: 
   - student → "Kak [nama]" atau "Kak"
   - parent → "Bapak/Ibu"
   - counselor → "Bapak/Ibu Guru"
3. **Tone berdasarkan sentiment**:
   - frustrated → empathetic, apologetic, solutif
   - anxious → reassuring, calm, supportive
   - excited → enthusiastic, encouraging
   - neutral/confused → clear, informative, helpful
4. **Financial concern → proaktif mention beasiswa & KIP**
5. **Gunakan emoji secukupnya (1-3 per respons)**
6. **Gunakan bold (**text**) untuk highlight penting**

## GUARDRAIL:
- HANYA jawab pertanyaan seputar JAL University (admisi, program studi, biaya, fasilitas, kehidupan kampus)
- Jika pertanyaan di luar konteks universitas → jawab sopan: "Maaf, saya hanya bisa membantu dengan informasi seputar JAL University. Ada yang ingin ditanyakan tentang kampus kami? 😊"
- JANGAN berikan informasi yang TIDAK ada di knowledge base — katakan "Saya akan cek informasi tersebut dan menghubungi kembali"

## STRUKTUR RESPONS:
1. Sapaan personal
2. Jawaban langsung dan jelas
3. Informasi pendukung (jika relevan)
4. Ajakan untuk bertanya lebih lanjut / CTA (Call to Action)

OUTPUT: Hanya teks respons langsung (bukan JSON). Maksimal 300 kata.
"""


def response_agent(state: AdmissionState, llm) -> dict:
    """
    Generate personalized response using LLM + knowledge context.
    Returns partial state updates.
    """
    start_time = time.time()
    message = state["message"]
    macro = state.get("macro_intent", "AMBIGUOUS")
    micro = state.get("micro_intent", "greeting_unclear")
    language = state.get("detected_language", "id")
    profile = state.get("lead_profile", {})
    knowledge = state.get("knowledge_context", "")
    funnel = state.get("funnel_stage", "awareness")
    urgency = state.get("urgency", "low")
    entities = state.get("extracted_entities", {})
    
    # Build personalization context
    personal_parts = []
    if profile.get("name"):
        personal_parts.append(f"Nama user: {profile['name']}")
    if profile.get("contact_type") and profile["contact_type"] != "unknown":
        personal_parts.append(f"Tipe kontak: {profile['contact_type']}")
    if entities.get("contact_type") and entities["contact_type"] != "null":
        personal_parts.append(f"Tipe kontak (baru): {entities['contact_type']}")
    if profile.get("interested_program"):
        personal_parts.append(f"Program diminati: {profile['interested_program']}")
    if profile.get("financial_concern"):
        personal_parts.append("⚠️ User punya kekhawatiran finansial — proaktif mention beasiswa!")
    if profile.get("school_type"):
        personal_parts.append(f"Tipe sekolah: {profile['school_type']}")
    
    personal_text = "\n".join(personal_parts) if personal_parts else "Profil belum lengkap"
    
    # Conversation history for context
    conv_history = state.get("conversation_history", [])
    history_text = ""
    if conv_history:
        recent = conv_history[-4:]
        lines = [f"{'User' if m.get('direction')=='inbound' else 'AI'}: {m.get('content','')[:150]}" for m in recent]
        history_text = "\nPERCAKAPAN SEBELUMNYA:\n" + "\n".join(lines)
    
    user_prompt = f"""KLASIFIKASI: {macro}/{micro}
FUNNEL STAGE: {funnel}
URGENCY: {urgency}
BAHASA: {language}

PROFIL USER:
{personal_text}

KNOWLEDGE BASE CONTEXT:
{knowledge[:2000]}
{history_text}

PESAN USER: "{message}"

Generate respons yang personal dan helpful."""
    
    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        response = llm.invoke([
            SystemMessage(content=RESPONSE_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])
        
        ai_response = response.content.strip()
        elapsed = int((time.time() - start_time) * 1000)
        
        # Detect personalization signals used
        signals = []
        if profile.get("name") and profile["name"].lower() in ai_response.lower():
            signals.append("name_personalization")
        if language == "en" and any(w in ai_response.lower() for w in ["hi ", "hello", "welcome"]):
            signals.append("english_response")
        if profile.get("financial_concern") and any(w in ai_response.lower() for w in ["beasiswa", "scholarship", "kip"]):
            signals.append("financial_proactive")
        
        return {
            "ai_response": ai_response,
            "personalization_signals": signals,
            "reasoning_trace": state.get("reasoning_trace", []) + [{
                "agent": "Response Agent",
                "thought": f"Generating response for {macro}/{micro} in {language}. Funnel: {funnel}, Urgency: {urgency}. Personalization: {', '.join(personal_parts[:3]) if personal_parts else 'minimal'}",
                "action": f"LLM Response Generation (personalization signals: {signals})",
                "observation": f"Generated {len(ai_response)} chars response. Signals: {signals}",
                "confidence": 0.85,
                "time_ms": elapsed,
            }],
        }
    except Exception as e:
        elapsed = int((time.time() - start_time) * 1000)
        fallback = _fallback_response(macro, micro, language)
        return {
            "ai_response": fallback,
            "personalization_signals": ["fallback"],
            "reasoning_trace": state.get("reasoning_trace", []) + [{
                "agent": "Response Agent",
                "thought": f"LLM failed: {str(e)}. Using template fallback.",
                "action": f"Fallback template for {macro}/{micro}",
                "observation": f"Error: {str(e)[:100]}",
                "confidence": 0.3,
                "time_ms": elapsed,
            }],
        }


def _fallback_response(macro: str, micro: str, language: str) -> str:
    """Template-based fallback responses."""
    if language == "en":
        templates = {
            "general_inquiry": "Thank you for your interest in JAL University! 😊 We'd be happy to help. Could you please be more specific about what you'd like to know?",
            "academic_inquiry": "JAL University offers 5 programs: Computer Science, Information Systems, Management, Psychology, and Visual Communication Design. Which one interests you?",
            "financial_inquiry": "Our tuition ranges from Rp 10-13M/semester. We also offer scholarships (25-100% off) and KIP Kuliah. Would you like details?",
            "registration_process": "To apply: 1) Fill form at portal.jal.ac.id 2) Upload documents 3) Pay Rp 350K registration fee 4) Take admission test. Need help?",
            "status_follow_up": "Please contact our admissions team: 021-7890-1234 or admisi@jal.ac.id for status updates. Office hours: Mon-Fri 08:00-16:00.",
            "technical_issue": "We're sorry for the inconvenience! Please try again or contact us at 021-7890-1234 / WA: 0812-3456-7890 for immediate help.",
            "general_complaint": "We sincerely apologize. Your feedback is important. Our team will contact you within 4 hours. You can also reach us at: 021-7890-1234.",
            "greeting_unclear": "Hi! Welcome to JAL University! 😊 How can I help? You can ask about programs, costs, scholarships, or registration.",
        }
    else:
        templates = {
            "general_inquiry": "Terima kasih sudah menghubungi JAL University! 😊 Silakan tanyakan apapun tentang kampus kami — program studi, fasilitas, pendaftaran, atau lainnya.",
            "academic_inquiry": "JAL University punya 5 prodi unggulan: Teknik Informatika, Sistem Informasi, Manajemen, Psikologi, dan DKV. Mau tahu detail prodi yang mana?",
            "financial_inquiry": "Biaya kuliah kami mulai Rp 10-13 juta/semester. Ada beasiswa prestasi (25-100%), KIP Kuliah (gratis), dan cicilan 3x. Mau info lebih detail?",
            "registration_process": "Cara daftar: 1) Isi formulir di portal.jal.ac.id 2) Upload dokumen 3) Bayar Rp 350rb 4) Ikuti tes seleksi. Butuh bantuan?",
            "status_follow_up": "Untuk cek status, hubungi admisi: 021-7890-1234 atau email admisi@jal.ac.id. Jam kerja: Senin-Jumat 08:00-16:00 WIB.",
            "technical_issue": "Mohon maaf atas kendala teknisnya! 🙏 Coba browser lain atau hubungi kami langsung: 021-7890-1234 / WA: 0812-3456-7890.",
            "general_complaint": "Mohon maaf sebesar-besarnya. Masukan Anda sangat penting. Tim kami akan menghubungi dalam 4 jam. Kontak: 021-7890-1234.",
            "greeting_unclear": "Halo! Selamat datang di JAL University! 😊 Ada yang bisa dibantu? Silakan tanyakan tentang program studi, biaya, beasiswa, atau pendaftaran.",
        }
    return templates.get(micro, templates.get("greeting_unclear", "Terima kasih sudah menghubungi JAL University! 😊"))
