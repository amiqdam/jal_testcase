"""
Admin Chat Monitor API — view conversations, reasoning logs, and manual intervention.
"""
import uuid
import json
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from backend.models.message import AdminReply
from backend.database.connection import get_db
from backend.services.lead_service import LeadService
from backend.config import MIN_CONFIDENCE_THRESHOLD

router = APIRouter()
lead_service = LeadService()


@router.get("/conversations")
async def list_conversations():
    """List all active conversations with preview, classification, and urgency."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            l.id as lead_id,
            l.name as lead_name,
            l.email,
            l.urgency,
            l.funnel_stage,
            l.contact_type,
            l.macro_intent,
            l.micro_intent,
            l.lead_source,
            m_last.content as last_message_preview,
            m_last.created_at as last_timestamp,
            m_last.intent_confidence,
            CASE
                WHEN l.urgency = 'critical' THEN 1
                WHEN m_last.intent_confidence < ? THEN 1
                ELSE 0
            END as needs_review
        FROM leads l
        LEFT JOIN (
            SELECT lead_id, content, created_at, intent_confidence,
                   ROW_NUMBER() OVER (PARTITION BY lead_id ORDER BY created_at DESC) as rn
            FROM messages WHERE direction = 'inbound'
        ) m_last ON l.id = m_last.lead_id AND m_last.rn = 1
        ORDER BY m_last.created_at DESC
    """, (MIN_CONFIDENCE_THRESHOLD,))
    
    conversations = []
    for row in cursor.fetchall():
        conv = dict(row)
        if conv.get("last_message_preview"):
            conv["last_message_preview"] = conv["last_message_preview"][:80]
        conv["needs_review"] = bool(conv.get("needs_review", 0))
        conversations.append(conv)
    
    conn.close()
    return {"conversations": conversations}


@router.get("/conversations/{lead_id}")
async def get_conversation_detail(lead_id: str):
    """Get full chat history with reasoning traces for a specific lead."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get lead profile
    cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
    lead = cursor.fetchone()
    if not lead:
        conn.close()
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Get all messages
    cursor.execute("""
        SELECT id, direction, content, language, macro_intent, micro_intent,
               intent_confidence, sentiment, processing_log, created_at
        FROM messages 
        WHERE lead_id = ? 
        ORDER BY created_at ASC
    """, (lead_id,))
    
    messages = []
    for row in cursor.fetchall():
        msg = dict(row)
        # Parse processing_log if present
        if msg.get("processing_log"):
            try:
                msg["processing_log"] = json.loads(msg["processing_log"])
            except json.JSONDecodeError:
                pass
        
        # Determine sender
        if msg["direction"] == "inbound":
            msg["sender"] = "user"
        else:
            log = msg.get("processing_log", {})
            if isinstance(log, dict) and log.get("source") == "admin_manual":
                msg["sender"] = "admin"
            else:
                msg["sender"] = "ai"
        
        messages.append(msg)
    
    conn.close()
    
    return {
        "lead_profile": dict(lead),
        "messages": messages
    }


@router.post("/conversations/{lead_id}/reply")
async def admin_reply(lead_id: str, reply: AdminReply):
    """Admin manual intervention — send a reply to a user."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM leads WHERE id = ?", (lead_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if not reply.content or not reply.content.strip():
        raise HTTPException(status_code=400, detail="Reply content cannot be empty")
    
    now = datetime.now(timezone.utc).isoformat()
    message_id = str(uuid.uuid4())
    
    processing_log = json.dumps({
        "source": "admin_manual",
        "admin_id": "admin",
        "timestamp": now
    })
    
    cursor.execute("""
        INSERT INTO messages (id, lead_id, direction, content, processing_log, created_at)
        VALUES (?, ?, 'outbound', ?, ?, ?)
    """, (message_id, lead_id, reply.content.strip(), processing_log, now))
    
    conn.commit()
    conn.close()
    
    return {"message_id": message_id, "timestamp": now}


@router.get("/events")
async def get_new_events(since: str = Query(None)):
    """Get count of new events since timestamp (for toast notifications)."""
    return lead_service.get_new_events_count(since)
