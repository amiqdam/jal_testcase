"""
Admin Complaints API — complaint tracking and resolution.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.database.connection import get_db

router = APIRouter()


@router.get("")
async def list_complaints(status: Optional[str] = Query(None)):
    """List complaints with optional status filter (open/resolved)."""
    conn = get_db()
    cursor = conn.cursor()
    
    where = ""
    params = []
    if status:
        where = "WHERE c.status = ?"
        params.append(status)
    
    cursor.execute(f"""
        SELECT c.*, l.name as lead_name, l.email as lead_email
        FROM complaints_log c
        JOIN leads l ON c.lead_id = l.id
        {where}
        ORDER BY c.created_at DESC
    """, params)
    
    complaints = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {"complaints": complaints, "total": len(complaints)}


@router.patch("/{complaint_id}/resolve")
async def resolve_complaint(complaint_id: str):
    """Mark a complaint as resolved."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, status FROM complaints_log WHERE id = ?", (complaint_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    now = datetime.now(timezone.utc).isoformat()
    cursor.execute("""
        UPDATE complaints_log SET status = 'resolved', resolved_at = ?, resolved_by = 'admin'
        WHERE id = ?
    """, (now, complaint_id))
    
    conn.commit()
    
    cursor.execute("SELECT * FROM complaints_log WHERE id = ?", (complaint_id,))
    complaint = dict(cursor.fetchone())
    conn.close()
    
    return complaint
