"""
Response management API — approve and edit draft responses.
"""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from backend.models.draft_response import DraftEdit
from backend.database.connection import get_db

router = APIRouter()


@router.post("/{response_id}/approve")
async def approve_response(response_id: str):
    """Approve a draft response for sending."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM draft_responses WHERE id = ?", (response_id,))
    draft = cursor.fetchone()
    
    if not draft:
        conn.close()
        raise HTTPException(status_code=404, detail="Draft response not found")
    
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
        UPDATE draft_responses SET status = 'approved' WHERE id = ?
    """, (response_id,))
    
    conn.commit()
    
    cursor.execute("SELECT * FROM draft_responses WHERE id = ?", (response_id,))
    result = dict(cursor.fetchone())
    conn.close()
    
    return result


@router.patch("/{response_id}/edit")
async def edit_response(response_id: str, edit: DraftEdit):
    """Edit a draft response before sending."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM draft_responses WHERE id = ?", (response_id,))
    draft = cursor.fetchone()
    
    if not draft:
        conn.close()
        raise HTTPException(status_code=404, detail="Draft response not found")
    
    cursor.execute("""
        UPDATE draft_responses 
        SET edited_content = ?, status = 'edited'
        WHERE id = ?
    """, (edit.content, response_id))
    
    conn.commit()
    
    cursor.execute("SELECT * FROM draft_responses WHERE id = ?", (response_id,))
    result = dict(cursor.fetchone())
    conn.close()
    
    return result
