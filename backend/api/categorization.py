"""
Categorization Query API — filtered/sorted messages for table and chart data.
"""
from fastapi import APIRouter, Query
from typing import Optional
from backend.database.connection import get_db

router = APIRouter()


@router.get("/categorization")
async def get_categorization(
    intent: Optional[str] = Query(None),
    funnel_stage: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    confidence_min: Optional[float] = Query(None),
    confidence_max: Optional[float] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200)
):
    """Get filtered and sorted messages for categorization table."""
    conn = get_db()
    cursor = conn.cursor()
    
    where_clauses = ["m.direction = 'inbound'"]
    params = []
    
    if intent:
        where_clauses.append("m.intent = ?")
        params.append(intent)
    if funnel_stage:
        where_clauses.append("l.funnel_stage = ?")
        params.append(funnel_stage)
    if urgency:
        where_clauses.append("l.urgency = ?")
        params.append(urgency)
    if sentiment:
        where_clauses.append("m.sentiment = ?")
        params.append(sentiment)
    if confidence_min is not None:
        where_clauses.append("m.intent_confidence >= ?")
        params.append(confidence_min)
    if confidence_max is not None:
        where_clauses.append("m.intent_confidence <= ?")
        params.append(confidence_max)
    if date_from:
        where_clauses.append("m.created_at >= ?")
        params.append(date_from)
    if date_to:
        where_clauses.append("m.created_at <= ?")
        params.append(date_to)
    if search:
        where_clauses.append("(COALESCE(l.name, l.session_id) LIKE ? OR m.content LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    
    where_sql = "WHERE " + " AND ".join(where_clauses)
    
    # Validate sort column
    valid_sort = {
        "created_at": "m.created_at",
        "timestamp": "m.created_at",
        "sender": "COALESCE(l.name, l.session_id)",
        "intent": "m.intent",
        "funnel_stage": "l.funnel_stage",
        "urgency": "l.urgency",
        "sentiment": "m.sentiment",
        "confidence": "m.intent_confidence",
    }
    sort_col = valid_sort.get(sort_by, "m.created_at")
    sort_dir = "ASC" if sort_order.lower() == "asc" else "DESC"
    
    # Count total
    count_query = f"""
        SELECT COUNT(*) as total 
        FROM messages m 
        JOIN leads l ON m.lead_id = l.id 
        {where_sql}
    """
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]
    
    # Get data
    offset = (page - 1) * limit
    data_query = f"""
        SELECT 
            m.id,
            m.created_at as timestamp,
            COALESCE(l.name, SUBSTR(l.session_id, 1, 8)) as sender,
            SUBSTR(m.content, 1, 80) as message_preview,
            m.intent,
            l.funnel_stage,
            l.urgency,
            m.sentiment,
            m.intent_confidence as confidence,
            l.id as lead_id
        FROM messages m
        JOIN leads l ON m.lead_id = l.id
        {where_sql}
        ORDER BY {sort_col} {sort_dir}
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    cursor.execute(data_query, params)
    
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        "data": data,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }


@router.get("/categorization/stats")
async def get_categorization_stats(
    intent: Optional[str] = Query(None),
    funnel_stage: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    sentiment: Optional[str] = Query(None),
    confidence_min: Optional[float] = Query(None),
    confidence_max: Optional[float] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """Get aggregated stats for charts — respects same filters as categorization table."""
    conn = get_db()
    cursor = conn.cursor()
    
    where_clauses = ["m.direction = 'inbound'"]
    params = []
    
    if intent:
        where_clauses.append("m.intent = ?")
        params.append(intent)
    if funnel_stage:
        where_clauses.append("l.funnel_stage = ?")
        params.append(funnel_stage)
    if urgency:
        where_clauses.append("l.urgency = ?")
        params.append(urgency)
    if sentiment:
        where_clauses.append("m.sentiment = ?")
        params.append(sentiment)
    if confidence_min is not None:
        where_clauses.append("m.intent_confidence >= ?")
        params.append(confidence_min)
    if confidence_max is not None:
        where_clauses.append("m.intent_confidence <= ?")
        params.append(confidence_max)
    if date_from:
        where_clauses.append("m.created_at >= ?")
        params.append(date_from)
    if date_to:
        where_clauses.append("m.created_at <= ?")
        params.append(date_to)
    if search:
        where_clauses.append("(COALESCE(l.name, l.session_id) LIKE ? OR m.content LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    
    where_sql = "WHERE " + " AND ".join(where_clauses)
    base_join = f"FROM messages m JOIN leads l ON m.lead_id = l.id {where_sql}"
    
    # Intent distribution
    cursor.execute(f"SELECT m.intent, COUNT(*) as count {base_join} AND m.intent IS NOT NULL GROUP BY m.intent ORDER BY count DESC", params)
    intent_distribution = {row["intent"]: row["count"] for row in cursor.fetchall()}
    
    # Funnel distribution
    cursor.execute(f"SELECT l.funnel_stage, COUNT(DISTINCT l.id) as count {base_join} GROUP BY l.funnel_stage", params)
    funnel_distribution = {row["funnel_stage"]: row["count"] for row in cursor.fetchall()}
    
    # Urgency breakdown
    cursor.execute(f"SELECT l.urgency, COUNT(DISTINCT l.id) as count {base_join} GROUP BY l.urgency", params)
    urgency_breakdown = {row["urgency"]: row["count"] for row in cursor.fetchall()}
    
    # Volume timeline (by date)
    cursor.execute(f"SELECT DATE(m.created_at) as date, COUNT(*) as count {base_join} GROUP BY DATE(m.created_at) ORDER BY date ASC", params)
    volume_timeline = [{"date": row["date"], "count": row["count"]} for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "intent_distribution": intent_distribution,
        "funnel_distribution": funnel_distribution,
        "urgency_breakdown": urgency_breakdown,
        "volume_timeline": volume_timeline
    }
