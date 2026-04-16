"""
MessageProcessor — Thin wrapper around LangGraph supervisor pipeline.
Handles rate limiting, prompt injection detection, and DB persistence.
"""
import re
import uuid
import json
import time
from datetime import datetime, timezone
from collections import defaultdict
from backend.database.connection import get_db
from backend.services.lead_service import LeadService
from backend.services.knowledge_base import KnowledgeBase
from backend.agents.supervisor import run_admission_pipeline
from backend.config import RATE_LIMIT_PER_MINUTE


class MessageProcessor:
    """Orchestrates message processing through the LangGraph pipeline."""
    
    def __init__(self):
        self.lead_service = LeadService()
        self.knowledge_base = KnowledgeBase()
        # Rate limiting: {email: [timestamp1, timestamp2, ...]}
        self._rate_limits = defaultdict(list)
    
    async def process(self, email: str, name: str, content: str,
                      lead_source: str = None, quick_start_intent: str = None) -> dict:
        """
        Process a message through the full LangGraph pipeline.
        Returns dict with lead_id, message_id, response, processing_log.
        """
        start_time = time.time()
        
        # 1. Rate limiting check
        if not self._check_rate_limit(email):
            return {
                "lead_id": "",
                "message_id": "",
                "response": "Maaf, Anda mengirim pesan terlalu cepat. Silakan tunggu sebentar dan coba lagi. 🙏",
                "processing_log": {"error": "rate_limited"},
            }
        
        # 2. Prompt injection detection
        if self._detect_prompt_injection(content):
            return {
                "lead_id": "",
                "message_id": "",
                "response": "Maaf, pesan Anda tidak dapat diproses. Silakan ajukan pertanyaan seputar JAL University. 😊",
                "processing_log": {"error": "prompt_injection_blocked"},
            }
        
        # 3. Get or create lead
        lead = self.lead_service.get_or_create_lead(email, name, lead_source)
        lead_id = lead["id"]
        
        # 4. Get conversation history
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT direction, content, macro_intent, micro_intent, created_at
            FROM messages WHERE lead_id = ? ORDER BY created_at DESC LIMIT 10
        """, (lead_id,))
        conversation_history = [dict(r) for r in cursor.fetchall()][::-1]  # Reverse to chronological
        conn.close()
        
        # 5. Get knowledge context based on quick-start or general
        macro_hint = ""
        micro_hint = quick_start_intent or ""
        if micro_hint:
            qs_macro = {"academic_inquiry": "INQUIRY", "financial_inquiry": "INQUIRY",
                        "registration_process": "TRANSACTIONAL", "general_inquiry": "INQUIRY"}
            macro_hint = qs_macro.get(micro_hint, "INQUIRY")
        
        knowledge_context = self.knowledge_base.get_context(
            micro_hint or "general_inquiry",
            lead.get("interested_program")
        )
        
        # 6. Run LangGraph pipeline
        final_state = await run_admission_pipeline(
            message=content,
            email=email,
            name=name,
            lead_profile=lead,
            conversation_history=conversation_history,
            knowledge_context=knowledge_context,
            quick_start_intent=quick_start_intent or "",
        )
        
        # 7. Persist results to DB
        now = datetime.now(timezone.utc).isoformat()
        msg_id = str(uuid.uuid4())
        resp_id = str(uuid.uuid4())
        draft_id = str(uuid.uuid4())
        action_id = str(uuid.uuid4())
        
        processing_log = json.dumps({
            "message_id": msg_id,
            "timestamp": now,
            "raw_input": content,
            "total_processing_time_ms": final_state.get("total_processing_time_ms", 0),
            "reasoning_trace": final_state.get("reasoning_trace", []),
            "detected_language": final_state.get("detected_language", "id"),
            "macro_intent": final_state.get("macro_intent", "AMBIGUOUS"),
            "micro_intent": final_state.get("micro_intent", "greeting_unclear"),
            "urgency": final_state.get("urgency", "low"),
            "funnel_stage": final_state.get("funnel_stage", "awareness"),
            "extracted_keywords": final_state.get("extracted_keywords", []),
            "classifier_confidence": final_state.get("classifier_confidence", 0.0),
            "personalization_signals": final_state.get("personalization_signals", []),
        }, ensure_ascii=False)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Save inbound message
        cursor.execute("""
            INSERT INTO messages (id, lead_id, direction, content, language, macro_intent, micro_intent,
                                  intent_confidence, sentiment, processing_log, processing_time_ms, created_at)
            VALUES (?, ?, 'inbound', ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (msg_id, lead_id, content,
              final_state.get("detected_language", "id"),
              final_state.get("macro_intent"),
              final_state.get("micro_intent"),
              final_state.get("classifier_confidence", 0.0),
              None,  # sentiment extracted in trace
              processing_log,
              final_state.get("total_processing_time_ms", 0),
              now))
        
        # Save outbound response
        ai_response = final_state.get("ai_response", "Terima kasih! Ada yang bisa dibantu lagi?")
        cursor.execute("""
            INSERT INTO messages (id, lead_id, direction, content, language, created_at)
            VALUES (?, ?, 'outbound', ?, ?, ?)
        """, (resp_id, lead_id, ai_response, final_state.get("detected_language", "id"), now))
        
        # Save draft response
        cursor.execute("""
            INSERT INTO draft_responses (id, message_id, lead_id, content, 
                                         personalization_signals, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'sent', ?)
        """, (draft_id, msg_id, lead_id, ai_response,
              json.dumps(final_state.get("personalization_signals", []), ensure_ascii=False), now))
        
        # Save next action
        nba = final_state.get("next_best_action", {})
        if nba:
            cursor.execute("""
                INSERT INTO next_actions (id, lead_id, action_type, action_detail,
                                          priority, reasoning, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (action_id, lead_id,
                  nba.get("action_type", "auto_respond"),
                  nba.get("action_detail", ""),
                  nba.get("priority", "low"),
                  nba.get("reasoning", ""),
                  now))
        
        # Save complaint if SUPPORT intent
        macro = final_state.get("macro_intent", "AMBIGUOUS")
        if macro == "SUPPORT":
            complaint_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO complaints_log (id, lead_id, message_id, description, status, created_at)
                VALUES (?, ?, ?, ?, 'open', ?)
            """, (complaint_id, lead_id, msg_id, content, now))
        
        conn.commit()
        conn.close()
        
        # Update lead profile with extracted entities
        profile_updates = final_state.get("profile_updates", {})
        if profile_updates:
            self.lead_service.update_profile(lead_id, profile_updates)
        
        # Update funnel stage and urgency
        self.lead_service.update_funnel_stage(
            lead_id,
            final_state.get("funnel_stage", "awareness"),
            final_state.get("urgency", "low"),
            final_state.get("macro_intent"),
            final_state.get("micro_intent"),
        )
        
        total_ms = int((time.time() - start_time) * 1000)
        
        return {
            "lead_id": lead_id,
            "message_id": msg_id,
            "response": ai_response,
            "processing_log": json.loads(processing_log),
        }
    
    def _check_rate_limit(self, email: str) -> bool:
        """Check if user is within rate limit. Returns True if allowed."""
        now = time.time()
        window = 60  # 1 minute window
        
        # Clean old entries
        self._rate_limits[email] = [t for t in self._rate_limits[email] if now - t < window]
        
        if len(self._rate_limits[email]) >= RATE_LIMIT_PER_MINUTE:
            return False
        
        self._rate_limits[email].append(now)
        return True
    
    def _detect_prompt_injection(self, content: str) -> bool:
        """Detect common prompt injection patterns."""
        injection_patterns = [
            r"ignore\s+(previous|all|above)\s+(instructions|prompts)",
            r"you\s+are\s+now\s+",
            r"forget\s+(everything|all|your)",
            r"new\s+instructions?:",
            r"system\s*prompt",
            r"jailbreak",
            r"DAN\s+mode",
            r"act\s+as\s+(if|a)\s+",
            r"pretend\s+(you|to\s+be)",
        ]
        content_lower = content.lower()
        for pattern in injection_patterns:
            if re.search(pattern, content_lower):
                return True
        return False
