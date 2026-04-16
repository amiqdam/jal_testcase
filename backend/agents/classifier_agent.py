"""
Classifier Agent — LLM-based intent classification and language detection.
Uses Groq/Llama 3.3 70B for MECE hierarchical classification.
Implements ReAct pattern: Thought → Action → Observation.
"""
import json
import time
from backend.agents.state import AdmissionState


CLASSIFIER_SYSTEM_PROMPT = """Kamu adalah Classifier Agent untuk sistem admisi universitas JAL University.

TUGAS: Analisis pesan dari calon mahasiswa/orang tua/guru BK dan klasifikasikan sesuai taxonomy berikut.

## TAXONOMY KLASIFIKASI (MECE — Mutually Exclusive, Collectively Exhaustive)

### 1. INQUIRY (Pencarian Informasi)
User murni bertanya, belum melakukan aksi pendaftaran.
- **general_inquiry**: Pertanyaan FAQ tentang info institusi umum (lokasi, akreditasi, fasilitas, asrama, UKM, event)
- **academic_inquiry**: Pertanyaan spesifik terkait proses belajar-mengajar (jurusan, kurikulum, mata kuliah, dosen, ekstrakurikuler, prospek karir)
- **financial_inquiry**: Semua hal berhubungan dengan uang dan kelayakan finansial (UKT, beasiswa, cicilan, biaya hidup, perbandingan biaya)

### 2. TRANSACTIONAL (Proses Administratif)
User sedang atau sudah melakukan aksi dalam funnel pendaftaran.
- **registration_process**: Pertanyaan teknis atau panduan langkah-langkah administratif (cara daftar, dokumen, cara bayar, "saya mau daftar")
- **status_follow_up**: Permintaan update atas aksi yang sudah dilakukan (status bayar, pengumuman seleksi, "sudah email tapi belum dibalas")

### 3. SUPPORT (Kendala & Keluhan)
User punya niat tapi terhalang masalah.
- **technical_issue**: Kendala pada sistem/error (link error, upload gagal, VA tidak ditemukan, website down)
- **general_complaint**: Keluhan terkait non-teknis IT (admin judes, proses ribet, lambat respons, kecewa layanan)

### 4. AMBIGUOUS (Lain-lain)
Pesan tidak jelas — jaring pengaman.
- **greeting_unclear**: Pesan pembuka, terlalu pendek, emoji-only (halo, P, mau tanya, hi)

## URGENCY SCORING
- **low**: Pertanyaan informasi standar, tidak ada deadline
- **medium**: Ada urgensi waktu (deadline dekat, sudah menunggu), orang tua/guru BK bertanya
- **critical**: Complaint, frustrated sentiment, deadline besok/hari ini, tidak ada respons lama

## OUTPUT FORMAT (JSON SAJA, tanpa markdown):
{
  "reasoning_process": "Jelaskan step-by-step analisis kamu tentang pesan ini...",
  "detected_language": "id|en|mixed",
  "macro_intent": "INQUIRY|TRANSACTIONAL|SUPPORT|AMBIGUOUS",
  "micro_intent": "general_inquiry|academic_inquiry|financial_inquiry|registration_process|status_follow_up|technical_issue|general_complaint|greeting_unclear",
  "urgency": "low|medium|critical",
  "extracted_keywords": ["keyword1", "keyword2"],
  "confidence": 0.0-1.0,
  "sentiment": "neutral|excited|anxious|confused|frustrated"
}

PENTING:
- Jika pesan mengandung keluhan/frustrasi → SELALU urgency=critical
- Jika pesan multi-intent, pilih yang paling actionable (prioritas: SUPPORT > TRANSACTIONAL > INQUIRY > AMBIGUOUS)
- Confidence harus realistis — jangan selalu 0.95
- Reasoning harus detail, bukan generic
"""


def classifier_agent(state: AdmissionState, llm) -> dict:
    """
    Classify the user message using LLM.
    Returns partial state updates.
    """
    start_time = time.time()
    message = state["message"]
    
    # Check for quick-start pre-classification
    quick_intent = state.get("quick_start_intent", "")
    if quick_intent:
        # Map quick-start to macro/micro
        qs_mapping = {
            "academic_inquiry": ("INQUIRY", "academic_inquiry"),
            "financial_inquiry": ("INQUIRY", "financial_inquiry"),
            "registration_process": ("TRANSACTIONAL", "registration_process"),
            "general_inquiry": ("INQUIRY", "general_inquiry"),
        }
        macro, micro = qs_mapping.get(quick_intent, ("INQUIRY", "general_inquiry"))
        elapsed = int((time.time() - start_time) * 1000)
        
        return {
            "detected_language": "id",
            "macro_intent": macro,
            "micro_intent": micro,
            "urgency": "low",
            "extracted_keywords": [],
            "classifier_confidence": 0.99,
            "reasoning_trace": state.get("reasoning_trace", []) + [{
                "agent": "Classifier Agent",
                "thought": f"User selected quick-start option: {quick_intent}. Skipping LLM classification.",
                "action": "Pre-classified via quick-start button",
                "observation": f"macro_intent={macro}, micro_intent={micro}, urgency=low",
                "confidence": 0.99,
                "time_ms": elapsed,
            }],
        }
    
    # Build prompt with conversation history
    history_text = ""
    conv_history = state.get("conversation_history", [])
    if conv_history:
        recent = conv_history[-6:]  # Last 3 exchanges
        history_lines = []
        for msg in recent:
            role = "User" if msg.get("direction") == "inbound" else "AI"
            history_lines.append(f"{role}: {msg.get('content', '')[:200]}")
        history_text = f"\n\nKONTEKS PERCAKAPAN SEBELUMNYA:\n" + "\n".join(history_lines)
    
    # Lead profile context
    profile = state.get("lead_profile", {})
    profile_text = ""
    if profile:
        parts = []
        if profile.get("contact_type") and profile["contact_type"] != "unknown":
            parts.append(f"Tipe kontak: {profile['contact_type']}")
        if profile.get("funnel_stage"):
            parts.append(f"Funnel: {profile['funnel_stage']}")
        if profile.get("interested_program"):
            parts.append(f"Program diminati: {profile['interested_program']}")
        if parts:
            profile_text = f"\n\nPROFIL USER SAAT INI:\n" + ", ".join(parts)
    
    user_prompt = f"Analisis pesan berikut:{history_text}{profile_text}\n\nPESAN USER: \"{message}\""
    
    try:
        from langchain_core.messages import SystemMessage, HumanMessage
        response = llm.invoke([
            SystemMessage(content=CLASSIFIER_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])
        
        # Parse JSON from response
        content = response.content.strip()
        # Handle markdown code blocks
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        
        result = json.loads(content)
        elapsed = int((time.time() - start_time) * 1000)
        
        return {
            "detected_language": result.get("detected_language", "id"),
            "macro_intent": result.get("macro_intent", "AMBIGUOUS"),
            "micro_intent": result.get("micro_intent", "greeting_unclear"),
            "urgency": result.get("urgency", "low"),
            "extracted_keywords": result.get("extracted_keywords", []),
            "classifier_confidence": result.get("confidence", 0.5),
            "reasoning_trace": state.get("reasoning_trace", []) + [{
                "agent": "Classifier Agent",
                "thought": result.get("reasoning_process", "Classified message"),
                "action": f"LLM Classification → {result.get('macro_intent')}/{result.get('micro_intent')}",
                "observation": f"language={result.get('detected_language')}, macro={result.get('macro_intent')}, micro={result.get('micro_intent')}, urgency={result.get('urgency')}, confidence={result.get('confidence')}, sentiment={result.get('sentiment', 'neutral')}",
                "confidence": result.get("confidence", 0.5),
                "time_ms": elapsed,
            }],
        }
    except Exception as e:
        elapsed = int((time.time() - start_time) * 1000)
        # Fallback: rule-based classification
        fallback = _rule_based_classify(message)
        return {
            **fallback,
            "reasoning_trace": state.get("reasoning_trace", []) + [{
                "agent": "Classifier Agent",
                "thought": f"LLM call failed: {str(e)}. Falling back to rule-based classification.",
                "action": f"Rule-based fallback → {fallback['macro_intent']}/{fallback['micro_intent']}",
                "observation": f"Error: {str(e)[:100]}. Used keyword matching instead.",
                "confidence": fallback["classifier_confidence"],
                "time_ms": elapsed,
            }],
        }


def _rule_based_classify(message: str) -> dict:
    """Rule-based fallback classification using keyword matching."""
    msg = message.lower()
    
    # SUPPORT checks first (highest priority)
    if any(w in msg for w in ["error", "gagal", "rusak", "down", "bug", "404", "tidak bisa"]):
        return {"detected_language": "id", "macro_intent": "SUPPORT", "micro_intent": "technical_issue",
                "urgency": "critical", "extracted_keywords": [], "classifier_confidence": 0.6}
    if any(w in msg for w in ["kecewa", "keluhan", "complaint", "judes", "ribet", "lambat", "marah"]):
        return {"detected_language": "id", "macro_intent": "SUPPORT", "micro_intent": "general_complaint",
                "urgency": "critical", "extracted_keywords": [], "classifier_confidence": 0.6}
    
    # TRANSACTIONAL
    if any(w in msg for w in ["daftar", "register", "pendaftaran", "apply", "dokumen upload"]):
        return {"detected_language": "id", "macro_intent": "TRANSACTIONAL", "micro_intent": "registration_process",
                "urgency": "medium", "extracted_keywords": [], "classifier_confidence": 0.6}
    if any(w in msg for w in ["status", "follow up", "sudah bayar", "pengumuman", "belum dibalas", "sudah email"]):
        return {"detected_language": "id", "macro_intent": "TRANSACTIONAL", "micro_intent": "status_follow_up",
                "urgency": "medium", "extracted_keywords": [], "classifier_confidence": 0.6}
    
    # INQUIRY
    if any(w in msg for w in ["biaya", "ukt", "beasiswa", "cicilan", "scholarship", "kip", "gratis"]):
        return {"detected_language": "id", "macro_intent": "INQUIRY", "micro_intent": "financial_inquiry",
                "urgency": "low", "extracted_keywords": [], "classifier_confidence": 0.6}
    if any(w in msg for w in ["jurusan", "prodi", "kurikulum", "mata kuliah", "program studi", "fakultas", "curriculum", "course"]):
        return {"detected_language": "id", "macro_intent": "INQUIRY", "micro_intent": "academic_inquiry",
                "urgency": "low", "extracted_keywords": [], "classifier_confidence": 0.6}
    if any(w in msg for w in ["lokasi", "akreditasi", "fasilitas", "asrama", "kampus", "dimana", "where"]):
        return {"detected_language": "id", "macro_intent": "INQUIRY", "micro_intent": "general_inquiry",
                "urgency": "low", "extracted_keywords": [], "classifier_confidence": 0.6}
    
    # AMBIGUOUS (default)
    lang = "en" if any(w in msg for w in ["hi", "hello", "i want", "i'm", "what", "how"]) else "id"
    return {"detected_language": lang, "macro_intent": "AMBIGUOUS", "micro_intent": "greeting_unclear",
            "urgency": "low", "extracted_keywords": [], "classifier_confidence": 0.3}
