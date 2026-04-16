"""
Chat API endpoints — send messages and get conversation history.
"""
import re
from fastapi import APIRouter, HTTPException
from backend.models.message import MessageCreate, MessageResponse
from backend.pipeline.processor import MessageProcessor
from backend.database.connection import get_db
from backend.config import MAX_MESSAGE_LENGTH

router = APIRouter()
processor = MessageProcessor()


def sanitize_input(content: str) -> str:
    """Basic XSS sanitization."""
    # Remove script tags and event handlers
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r'on\w+\s*=', '', content, flags=re.IGNORECASE)
    content = re.sub(r'<[^>]+>', '', content)  # Strip all HTML tags
    return content.strip()


@router.post("/send", response_model=MessageResponse)
async def send_message(message: MessageCreate):
    """
    Process a new chat message through the LangGraph AI pipeline.
    Accepts email, name, content, and optional quick_start_intent + lead_source.
    """
    # Validate input
    if not message.content or not message.content.strip():
        raise HTTPException(
            status_code=400,
            detail="Maaf, pesan tidak boleh kosong. Silakan ketik pertanyaan Anda."
        )
    
    if len(message.content) > MAX_MESSAGE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail=f"Maaf, pesan terlalu panjang (maks {MAX_MESSAGE_LENGTH} karakter)."
        )
    
    if not message.email or not message.email.strip():
        raise HTTPException(
            status_code=400,
            detail="Email wajib diisi."
        )
    
    if not message.name or not message.name.strip():
        raise HTTPException(
            status_code=400,
            detail="Nama wajib diisi."
        )
    
    # Sanitize
    clean_content = sanitize_input(message.content)
    if not clean_content:
        raise HTTPException(
            status_code=400,
            detail="Maaf, pesan tidak valid. Silakan coba lagi."
        )
    
    # Process through LangGraph pipeline
    result = await processor.process(
        email=message.email.strip().lower(),
        name=message.name.strip(),
        content=clean_content,
        lead_source=message.lead_source,
        quick_start_intent=message.quick_start_intent,
    )
    
    return MessageResponse(
        lead_id=result["lead_id"],
        message_id=result["message_id"],
        response=result["response"],
        processing_log=result["processing_log"]
    )


@router.get("/{lead_id}")
async def get_conversation(lead_id: str):
    """Get full conversation history for a lead."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM messages WHERE lead_id = ? ORDER BY created_at ASC
    """, (lead_id,))
    
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"lead_id": lead_id, "messages": messages}
