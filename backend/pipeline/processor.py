"""
MessageProcessor — Orchestrates the entire AI processing pipeline for each message.
"""
import uuid
import json
import time
from datetime import datetime, timezone
from typing import Optional
from backend.services.llm_service import LLMService
from backend.services.knowledge_base import KnowledgeBase
from backend.services.lead_service import LeadService
from backend.models.processing_log import ProcessingResult, StepResult
from backend.database.connection import get_db


class MessageProcessor:
    """Orchestrates the entire AI processing pipeline for each message."""
    
    def __init__(self):
        self.llm = LLMService()
        self.kb = KnowledgeBase()
        self.lead_service = LeadService()
    
    async def process(self, session_id: str, content: str,
                      quick_start_intent: Optional[str] = None) -> dict:
        """
        Process a single message through the full pipeline.
        Returns dict with all outputs + processing_log.
        """
        total_start = time.time()
        steps = []
        
        # 1. Get or create lead
        lead = self.lead_service.get_or_create_lead(session_id)
        lead_id = lead["id"]
        lead_profile = self._extract_profile(lead)
        
        # 2. Save inbound message
        message_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        # 3. If quick_start_intent provided, use it; otherwise run full analysis
        if quick_start_intent:
            # Quick-start pre-classification
            step_start = time.time()
            analysis = {
                "language": "id",
                "intent": quick_start_intent,
                "intent_confidence": 1.0,
                "entities": {},
                "sentiment": "neutral",
                "funnel_stage": self._intent_to_funnel(quick_start_intent),
                "urgency": "low",
                "reasoning": f"Quick-start pre-classified intent: {quick_start_intent}"
            }
            steps.append(StepResult(
                step="quick_start_classification",
                order=1,
                result=quick_start_intent,
                confidence=1.0,
                reasoning=f"User selected quick-start option, pre-classified as '{quick_start_intent}'",
                time_ms=int((time.time() - step_start) * 1000)
            ))
        else:
            # Full LLM analysis
            # Step 1: Language Detection (part of LLM analysis)
            step_start = time.time()
            
            # Get knowledge context based on initial guess
            knowledge_context = self.kb.get_context("ambiguous")
            
            # Run LLM analysis (single pass)
            analysis = await self.llm.analyze_message(content, lead_profile, knowledge_context)
            analysis_time = int((time.time() - step_start) * 1000)
            
            # Log individual steps from analysis
            steps.append(StepResult(
                step="language_detection",
                order=1,
                result=analysis.get("language", "id"),
                confidence=0.95,
                reasoning=f"Detected language: {analysis.get('language', 'id')}",
                time_ms=analysis_time // 6
            ))
            
            steps.append(StepResult(
                step="intent_classification",
                order=2,
                result=analysis.get("intent", "ambiguous"),
                confidence=analysis.get("intent_confidence", 0.5),
                reasoning=analysis.get("reasoning", "LLM classification"),
                time_ms=analysis_time // 6
            ))
            
            steps.append(StepResult(
                step="entity_extraction",
                order=3,
                result=analysis.get("entities", {}),
                confidence=0.8,
                reasoning=f"Extracted entities: {list(analysis.get('entities', {}).keys())}",
                time_ms=analysis_time // 6
            ))
            
            steps.append(StepResult(
                step="sentiment_analysis",
                order=4,
                result=analysis.get("sentiment", "neutral"),
                confidence=0.75,
                reasoning=f"Detected sentiment: {analysis.get('sentiment', 'neutral')}",
                time_ms=analysis_time // 6
            ))
            
            steps.append(StepResult(
                step="funnel_staging",
                order=5,
                result=analysis.get("funnel_stage", "awareness"),
                confidence=0.85,
                reasoning=f"Funnel stage based on intent '{analysis.get('intent')}' and profile history",
                time_ms=analysis_time // 6
            ))
            
            steps.append(StepResult(
                step="urgency_scoring",
                order=6,
                result=analysis.get("urgency", "low"),
                confidence=0.9,
                reasoning=f"Urgency determined by funnel stage and sentiment",
                time_ms=analysis_time // 6
            ))
        
        # 4. Get enriched knowledge context
        intent = analysis.get("intent", "ambiguous")
        program = analysis.get("entities", {}).get("interested_program")
        knowledge_context = self.kb.get_context(intent, program)
        
        # 5. Update lead profile with extracted entities
        entities = analysis.get("entities", {})
        entities["language"] = analysis.get("language", "id")
        if entities:
            lead = self.lead_service.update_profile(lead_id, entities)
        
        # 6. Update funnel stage
        lead = self.lead_service.update_funnel_stage(
            lead_id,
            analysis.get("funnel_stage", "awareness"),
            analysis.get("urgency", "low")
        )
        
        # 7. Generate response
        step_start = time.time()
        draft_response = await self.llm.generate_response(
            content, analysis, self._extract_profile(lead), knowledge_context
        )
        response_time = int((time.time() - step_start) * 1000)
        
        steps.append(StepResult(
            step="response_generation",
            order=7,
            result="generated",
            confidence=0.9,
            reasoning=f"Personalized response generated for {lead.get('contact_type', 'unknown')} in {analysis.get('language', 'id')}",
            time_ms=response_time
        ))
        
        # 8. Generate NBA
        step_start = time.time()
        nba = await self.llm.generate_nba(self._extract_profile(lead), analysis)
        nba_time = int((time.time() - step_start) * 1000)
        
        steps.append(StepResult(
            step="next_best_action",
            order=8,
            result=nba,
            confidence=0.85,
            reasoning=nba.get("reasoning", "NBA matrix"),
            time_ms=nba_time
        ))
        
        # Build processing log
        total_time = int((time.time() - total_start) * 1000)
        processing_log = {
            "message_id": message_id,
            "timestamp": now,
            "raw_input": content,
            "total_processing_time_ms": total_time,
            "steps": [s.model_dump() for s in steps]
        }
        
        # 9. Save everything to database
        conn = get_db()
        cursor = conn.cursor()
        
        # Save inbound message
        cursor.execute("""
            INSERT INTO messages (id, lead_id, direction, content, language, intent, 
                                  intent_confidence, sentiment, processing_log, 
                                  processing_time_ms, created_at)
            VALUES (?, ?, 'inbound', ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            message_id, lead_id, content,
            analysis.get("language", "id"),
            analysis.get("intent", "ambiguous"),
            analysis.get("intent_confidence", 0.5),
            analysis.get("sentiment", "neutral"),
            json.dumps(processing_log, ensure_ascii=False),
            total_time, now
        ))
        
        # Save outbound response
        response_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO messages (id, lead_id, direction, content, language, 
                                  processing_time_ms, created_at)
            VALUES (?, ?, 'outbound', ?, ?, ?, ?)
        """, (
            response_id, lead_id, draft_response,
            analysis.get("language", "id"),
            response_time, now
        ))
        
        # Save draft response
        draft_id = str(uuid.uuid4())
        personalization_signals = json.dumps({
            "language": analysis.get("language"),
            "contact_type": lead.get("contact_type"),
            "sentiment": analysis.get("sentiment"),
            "intent": analysis.get("intent"),
            "financial_concern": lead.get("financial_concern"),
        }, ensure_ascii=False)
        
        cursor.execute("""
            INSERT INTO draft_responses (id, message_id, lead_id, content, 
                                         personalization_signals, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'sent', ?)
        """, (draft_id, message_id, lead_id, draft_response, personalization_signals, now))
        
        # Save next action
        action_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO next_actions (id, lead_id, action_type, action_detail, 
                                      priority, reasoning, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            action_id, lead_id,
            nba.get("action_type", "auto_respond"),
            nba.get("action_detail", ""),
            nba.get("priority", "medium"),
            nba.get("reasoning", ""),
            now
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "lead_id": lead_id,
            "message_id": message_id,
            "response": draft_response,
            "processing_log": processing_log,
            "analysis": analysis,
            "nba": nba
        }
    
    def _extract_profile(self, lead: dict) -> dict:
        """Extract relevant profile fields from lead record."""
        return {
            "name": lead.get("name"),
            "contact_type": lead.get("contact_type", "unknown"),
            "school_origin": lead.get("school_origin"),
            "school_type": lead.get("school_type"),
            "interested_program": lead.get("interested_program"),
            "nationality": lead.get("nationality"),
            "academic_achievement": lead.get("academic_achievement"),
            "financial_concern": bool(lead.get("financial_concern", 0)),
            "language_pref": lead.get("language_pref", "id"),
            "funnel_stage": lead.get("funnel_stage", "awareness"),
        }
    
    def _intent_to_funnel(self, intent: str) -> str:
        """Map quick-start intent to initial funnel stage."""
        mapping = {
            "inquiry_prodi": "awareness",
            "inquiry_biaya": "consideration",
            "registration": "decision",
            "scholarship": "interest",
        }
        return mapping.get(intent, "awareness")
