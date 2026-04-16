"""
LLMService — Abstraction layer for LLM API calls.
Supports OpenAI API with retry logic and rule-based fallback.
"""
import json
import time
import asyncio
from typing import Optional
from backend.config import (
    LLM_PROVIDER, LLM_API_KEY, LLM_MODEL, LLM_TEMPERATURE,
    LLM_MAX_TOKENS, LLM_RETRY_COUNT, LLM_RETRY_BACKOFF,
    INTENT_CATEGORIES, FUNNEL_STAGES, URGENCY_LEVELS,
    MIN_CONFIDENCE_THRESHOLD
)


class LLMService:
    """Abstraction layer for LLM API calls. Supports OpenAI, Gemini, Claude."""
    
    def __init__(self):
        self.provider = LLM_PROVIDER
        self.api_key = LLM_API_KEY
        self.model = LLM_MODEL
        self.client = None
        
        if self.api_key and self.provider == "openai":
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except Exception:
                self.client = None
    
    async def analyze_message(self, message: str, lead_profile: dict,
                               knowledge_context: str) -> dict:
        """
        Single-pass LLM call that returns structured analysis:
        language, intent, intent_confidence, entities, sentiment, funnel_stage, urgency.
        """
        system_prompt = self._build_analysis_prompt(knowledge_context)
        user_prompt = self._build_analysis_user_prompt(message, lead_profile)
        
        result = await self._call_llm(system_prompt, user_prompt)
        
        if result is None:
            # Fallback to rule-based
            return self._rule_based_analysis(message, lead_profile)
        
        try:
            analysis = json.loads(result)
            # Validate required fields
            analysis.setdefault("language", "id")
            analysis.setdefault("intent", "ambiguous")
            analysis.setdefault("intent_confidence", 0.5)
            analysis.setdefault("entities", {})
            analysis.setdefault("sentiment", "neutral")
            analysis.setdefault("funnel_stage", "awareness")
            analysis.setdefault("urgency", "low")
            analysis.setdefault("reasoning", "")
            return analysis
        except (json.JSONDecodeError, KeyError):
            return self._rule_based_analysis(message, lead_profile)
    
    async def generate_response(self, message: str, analysis: dict,
                                 lead_profile: dict, knowledge_context: str) -> str:
        """Generate personalized response draft based on full context."""
        system_prompt = self._build_response_prompt(knowledge_context)
        
        user_prompt = (
            f"Pesan user: \"{message}\"\n\n"
            f"Analisis:\n"
            f"- Bahasa: {analysis.get('language', 'id')}\n"
            f"- Intent: {analysis.get('intent', 'ambiguous')}\n"
            f"- Sentiment: {analysis.get('sentiment', 'neutral')}\n"
            f"- Funnel stage: {analysis.get('funnel_stage', 'awareness')}\n\n"
            f"Profil lead:\n"
            f"- Nama: {lead_profile.get('name', 'Tidak diketahui')}\n"
            f"- Tipe kontak: {lead_profile.get('contact_type', 'unknown')}\n"
            f"- Sekolah: {lead_profile.get('school_origin', 'N/A')}\n"
            f"- Program diminati: {lead_profile.get('interested_program', 'N/A')}\n"
            f"- Kekhawatiran finansial: {lead_profile.get('financial_concern', False)}\n\n"
            f"Buatkan respons yang personal, empatis, dan informatif."
        )
        
        result = await self._call_llm(system_prompt, user_prompt)
        
        if result is None:
            return self._fallback_response(analysis, lead_profile)
        
        return result
    
    async def generate_nba(self, lead_profile: dict, analysis: dict) -> dict:
        """Generate next best action recommendation for admissions team."""
        funnel = analysis.get("funnel_stage", "awareness")
        urgency = analysis.get("urgency", "low")
        intent = analysis.get("intent", "ambiguous")
        sentiment = analysis.get("sentiment", "neutral")
        
        # NBA Matrix (rule-based for speed + reliability)
        return self._get_nba(funnel, urgency, intent, sentiment)
    
    # --- Private Methods ---
    
    async def _call_llm(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Call LLM API with retry logic and exponential backoff."""
        if not self.client:
            return None
        
        for attempt in range(LLM_RETRY_COUNT):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=LLM_TEMPERATURE,
                    max_tokens=LLM_MAX_TOKENS,
                    response_format={"type": "json_object"} if "analysis" in system_prompt.lower()[:100] else None
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt < LLM_RETRY_COUNT - 1:
                    wait_time = LLM_RETRY_BACKOFF[attempt]
                    await asyncio.sleep(wait_time)
                else:
                    print(f"LLM API failed after {LLM_RETRY_COUNT} retries: {e}")
                    return None
    
    def _build_analysis_prompt(self, knowledge_context: str) -> str:
        """Build system prompt for message analysis."""
        return f"""Kamu adalah AI admisi universitas. Analisis pesan calon mahasiswa dan berikan output JSON.

KONTEKS KAMPUS:
{knowledge_context}

KATEGORI INTENT: {', '.join(INTENT_CATEGORIES)}
FUNNEL STAGES: {', '.join(FUNNEL_STAGES)}
URGENCY LEVELS: {', '.join(URGENCY_LEVELS)}

RULES:
- Detect bahasa: "id" (Bahasa Indonesia), "en" (English), "mixed" (campuran)
- Classify intent ke salah satu dari 8 kategori
- Jika pesan mengandung lebih dari 1 intent, prioritaskan yang paling actionable
- Extract entities: name, school_origin, school_type, interested_program, contact_type, nationality, academic_achievement, financial_concern
- Analyze sentiment: neutral, anxious, frustrated, excited, confused, grateful
- Determine funnel stage berdasarkan: awareness (umum), interest (spesifik), consideration (biaya/beasiswa), decision (mau daftar), enrolled (sudah terdaftar)
- Determine urgency: low (umum), medium (specific interest), high (mau daftar/deadline), critical (complaint/frustrated)
- Override: complaint/frustrated → CRITICAL, deadline_mentioned → upgrade +1, no_response_mentioned → HIGH

OUTPUT JSON FORMAT:
{{
  "language": "id",
  "intent": "inquiry_prodi",
  "intent_confidence": 0.95,
  "entities": {{"name": "...", "school_origin": "...", "contact_type": "student", ...}},
  "sentiment": "neutral",
  "funnel_stage": "awareness",
  "urgency": "low",
  "reasoning": "Penjelasan singkat mengapa klasifikasi ini dipilih"
}}"""

    def _build_analysis_user_prompt(self, message: str, lead_profile: dict) -> str:
        """Build user prompt for analysis."""
        profile_context = ""
        if lead_profile:
            profile_context = f"\nProfil lead saat ini: {json.dumps(lead_profile, ensure_ascii=False)}"
        return f"Pesan: \"{message}\"{profile_context}"

    def _build_response_prompt(self, knowledge_context: str) -> str:
        """Build system prompt for response generation."""
        return f"""Kamu adalah customer service AI Universitas Luminara yang ramah, empatis, dan informatif.

KONTEKS KAMPUS:
{knowledge_context}

RULES PERSONALISASI:
- Bahasa: respons HARUS dalam bahasa yang sama dengan user
- Sapaan: student → "Kak", parent → "Bapak/Ibu", counselor → "Bapak/Ibu Guru"
- Tone: frustrated → empati + minta maaf, anxious → menenangkan, excited → antusias
- Jika financial_concern=true → sebutkan beasiswa yang relevan
- Jika school_type=SMK → highlight konversi skill ke program studi
- Referensi informasi dari percakapan sebelumnya jika ada
- Jawaban HARUS berdasarkan data kampus yang diberikan, TIDAK boleh mengarang
- Akhiri dengan pertanyaan follow-up atau CTA yang relevan
- Jangan terlalu panjang. 2-4 paragraf cukup."""

    def _rule_based_analysis(self, message: str, lead_profile: dict) -> dict:
        """Fallback rule-based classification when LLM is unavailable."""
        msg_lower = message.lower()
        
        # Language detection
        id_markers = ["kak", "mau", "ada", "ga", "gak", "apa", "bisa", "dong", "tanya", "gimana", "berapa"]
        en_markers = ["want", "how", "what", "can", "like", "please", "would", "apply", "interested"]
        id_count = sum(1 for m in id_markers if m in msg_lower)
        en_count = sum(1 for m in en_markers if m in msg_lower)
        
        if id_count > 0 and en_count > 0:
            language = "mixed"
        elif en_count > id_count:
            language = "en"
        else:
            language = "id"
        
        # Intent classification (keyword-based)
        intent = "ambiguous"
        confidence = 0.5
        
        intent_keywords = {
            "inquiry_prodi": ["jurusan", "prodi", "program studi", "fakultas", "kurikulum", "akreditasi", "prospek", "karir"],
            "inquiry_biaya": ["biaya", "uang", "bayar", "cicil", "ukt", "spp", "mahal", "murah", "harga"],
            "registration": ["daftar", "pendaftaran", "apply", "register", "formulir", "syarat"],
            "scholarship": ["beasiswa", "kip", "potongan", "gratis", "bantuan", "scholarship"],
            "followup_status": ["status", "sampai mana", "belum ada", "email", "sudah daftar", "reg-"],
            "complaint": ["error", "gagal", "kecewa", "tidak bisa", "tidak ada respons", "lambat", "masalah"],
            "partnership": ["sekolah kami", "guru bk", "kunjungan", "siswa kami", "kerja sama"],
        }
        
        for cat, keywords in intent_keywords.items():
            matches = sum(1 for kw in keywords if kw in msg_lower)
            if matches > 0:
                intent = cat
                confidence = min(0.4 + (matches * 0.15), 0.85)
                break
        
        # Sentiment (basic)
        sentiment = "neutral"
        if any(w in msg_lower for w in ["kecewa", "marah", "error", "gagal", "tidak bisa"]):
            sentiment = "frustrated"
        elif any(w in msg_lower for w in ["😢", "khawatir", "takut", "bingung"]):
            sentiment = "anxious"
        elif any(w in msg_lower for w in ["senang", "tertarik", "excited", "wow"]):
            sentiment = "excited"
        
        # Funnel stage
        funnel_stage = "awareness"
        if intent == "registration":
            funnel_stage = "decision"
        elif intent in ("inquiry_biaya", "scholarship"):
            funnel_stage = "consideration"
        elif intent == "inquiry_prodi" and any(kw in msg_lower for kw in ["tertarik", "interested", "specific"]):
            funnel_stage = "interest"
        elif intent == "followup_status":
            funnel_stage = "decision"
        
        # Urgency
        urgency = "low"
        if intent == "complaint" or sentiment == "frustrated":
            urgency = "critical"
        elif intent == "registration":
            urgency = "high"
        elif funnel_stage == "consideration":
            urgency = "medium"
        elif any(w in msg_lower for w in ["deadline", "besok", "segera", "urgent"]):
            urgency = "high"
        
        # Entity extraction (basic)
        entities = {}
        if any(w in msg_lower for w in ["orang tua", "bapak", "ibu saya", "anak saya"]):
            entities["contact_type"] = "parent"
        elif any(w in msg_lower for w in ["guru bk", "guru", "sekolah kami"]):
            entities["contact_type"] = "counselor"
        else:
            entities["contact_type"] = "student"
        
        if any(w in msg_lower for w in ["beasiswa", "kurang mampu", "bantuan", "kip"]):
            entities["financial_concern"] = True
        
        for prog in ["teknik informatika", "sistem informasi", "manajemen", "psikologi", "dkv", "desain"]:
            if prog in msg_lower:
                entities["interested_program"] = prog
                break
        
        return {
            "language": language,
            "intent": intent,
            "intent_confidence": confidence,
            "entities": entities,
            "sentiment": sentiment,
            "funnel_stage": funnel_stage,
            "urgency": urgency,
            "reasoning": f"Rule-based fallback classification. Intent='{intent}' (confidence={confidence:.2f})"
        }
    
    def _fallback_response(self, analysis: dict, lead_profile: dict) -> str:
        """Generate a template response when LLM is unavailable."""
        intent = analysis.get("intent", "ambiguous")
        language = analysis.get("language", "id")
        contact_type = lead_profile.get("contact_type", "unknown")
        
        greeting = "Kak" if contact_type == "student" else "Bapak/Ibu"
        
        if language == "en":
            greeting = "Hi"
            templates = {
                "inquiry_prodi": f"{greeting}, thank you for your interest in our programs! We have 5 study programs. Please visit luminara.ac.id for details or ask me a specific question.",
                "inquiry_biaya": f"{greeting}, tuition fees range from Rp 10-13 million/semester. We also offer various scholarships. Would you like more details?",
                "registration": f"{greeting}, to register, please visit portal.luminara.ac.id. You'll need your high school diploma and transcripts. Registration fee is Rp 350,000.",
                "scholarship": f"{greeting}, we offer merit-based (25-100% off), KIP Kuliah (100% coverage), and internal scholarships. What are your qualifications?",
                "followup_status": f"{greeting}, please contact our admissions team at 021-7890-1234 or admisi@luminara.ac.id for status updates.",
                "complaint": f"{greeting}, we sincerely apologize for the inconvenience. Please contact us at 021-7890-1234 and we'll resolve this immediately.",
                "ambiguous": f"{greeting}, thank you for reaching out to Universitas Luminara! Could you tell me what you'd like to know about? Programs, fees, scholarships, or registration?",
                "partnership": f"{greeting}, for school partnerships and campus visits, please email admisi@luminara.ac.id.",
            }
        else:
            templates = {
                "inquiry_prodi": f"Halo {greeting}! 😊 Terima kasih sudah menghubungi Universitas Luminara. Kami memiliki 5 program studi. Silakan tanyakan program yang diminati!",
                "inquiry_biaya": f"Halo {greeting}! Biaya kuliah berkisar Rp 10-13 juta/semester. Kami juga menyediakan berbagai beasiswa. Mau tahu lebih detail?",
                "registration": f"Halo {greeting}! Untuk mendaftar, silakan kunjungi portal.luminara.ac.id. Biaya pendaftaran Rp 350.000. Ada yang bisa dibantu?",
                "scholarship": f"Halo {greeting}! Kami punya Beasiswa Prestasi (25-100%), KIP Kuliah (100%), dan Beasiswa Luminara Berprestasi (30-75%). Mau tahu syaratnya?",
                "followup_status": f"Halo {greeting}! Untuk cek status pendaftaran, silakan hubungi 021-7890-1234 atau email admisi@luminara.ac.id.",
                "complaint": f"Halo {greeting}! Mohon maaf atas ketidaknyamanannya 🙏 Silakan hubungi kami di 021-7890-1234 dan kami akan segera menyelesaikannya.",
                "ambiguous": f"Halo {greeting}! 😊 Terima kasih sudah menghubungi Universitas Luminara. Apa yang ingin ditanyakan? Program studi, biaya, beasiswa, atau cara mendaftar?",
                "partnership": f"Halo {greeting}! Untuk kunjungan kampus atau kerjasama, silakan email ke admisi@luminara.ac.id.",
            }
        
        return templates.get(intent, templates["ambiguous"])
    
    def _get_nba(self, funnel: str, urgency: str, intent: str, sentiment: str) -> dict:
        """Get Next Best Action based on funnel stage and urgency matrix."""
        # Critical override
        if urgency == "critical" or sentiment == "frustrated":
            return {
                "action_type": "escalate",
                "action_detail": "Eskalasi ke supervisor. Kirim respons apologi segera. Resolusi dalam 4 jam.",
                "priority": "critical",
                "reasoning": f"Urgency critical / sentiment frustrated. Butuh penanganan segera."
            }
        
        nba_matrix = {
            ("awareness", "low"): {"action_type": "auto_respond", "action_detail": "Auto-respond + schedule follow-up 3 hari", "priority": "low"},
            ("awareness", "medium"): {"action_type": "send_brochure", "action_detail": "Auto-respond + kirim brosur digital", "priority": "medium"},
            ("interest", "low"): {"action_type": "send_brochure", "action_detail": "Kirim info program spesifik + follow-up 3 hari", "priority": "low"},
            ("interest", "medium"): {"action_type": "invite_tour", "action_detail": "Undang campus tour / webinar terdekat", "priority": "medium"},
            ("consideration", "medium"): {"action_type": "connect_alumni", "action_detail": "Hubungkan dengan alumni/mahasiswa aktif + assign konselor", "priority": "medium"},
            ("consideration", "high"): {"action_type": "assign_counselor", "action_detail": "Assign konselor dedicated + hubungi dalam 24 jam", "priority": "high"},
            ("decision", "high"): {"action_type": "fast_track", "action_detail": "Fast-track pendaftaran + bantuan personal", "priority": "high"},
            ("decision", "critical"): {"action_type": "escalate", "action_detail": "Eskalasi ke supervisor + resolusi dalam 4 jam", "priority": "critical"},
        }
        
        key = (funnel, urgency)
        nba = nba_matrix.get(key, {
            "action_type": "auto_respond",
            "action_detail": f"Auto-respond berdasarkan intent '{intent}'. Schedule follow-up 3 hari.",
            "priority": urgency
        })
        
        nba["reasoning"] = f"Funnel: {funnel}, Urgency: {urgency}, Intent: {intent}"
        return nba
