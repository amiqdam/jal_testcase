"""
Categorization Query API — filtered/sorted messages for table and chart data.
"""
from fastapi import APIRouter, Query
from typing import Optional
from backend.database.connection import get_db

router = APIRouter()


@router.get("/messages")
async def get_categorized_messages(
    macro_intent: Optional[str] = Query(None),
    micro_intent: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    funnel_stage: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_dir: str = Query("desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    """Get messages with filtering and sorting for categorization table."""
    conn = get_db()
    cursor = conn.cursor()
    
    where_clauses = ["m.direction = 'inbound'"]
    params = []
    
    if macro_intent:
        where_clauses.append("m.macro_intent = ?")
        params.append(macro_intent)
    if micro_intent:
        where_clauses.append("m.micro_intent = ?")
        params.append(micro_intent)
    if urgency:
        where_clauses.append("l.urgency = ?")
        params.append(urgency)
    if funnel_stage:
        where_clauses.append("l.funnel_stage = ?")
        params.append(funnel_stage)
    
    where_sql = " AND ".join(where_clauses)
    
    # Whitelist sort columns
    allowed_sorts = {
        "created_at": "m.created_at",
        "macro_intent": "m.macro_intent",
        "micro_intent": "m.micro_intent",
        "urgency": "l.urgency",
        "funnel_stage": "l.funnel_stage",
        "name": "l.name",
    }
    sort_col = allowed_sorts.get(sort_by, "m.created_at")
    sort_direction = "ASC" if sort_dir.lower() == "asc" else "DESC"
    
    count_query = f"""
        SELECT COUNT(*) as total
        FROM messages m JOIN leads l ON m.lead_id = l.id
        WHERE {where_sql}
    """
    cursor.execute(count_query, params)
    total = cursor.fetchone()["total"]
    
    offset = (page - 1) * limit
    query = f"""
        SELECT m.id, m.lead_id, m.content, m.language, m.macro_intent, m.micro_intent,
               m.intent_confidence, m.created_at,
               l.name, l.email, l.urgency, l.funnel_stage, l.lead_source, l.contact_type
        FROM messages m
        JOIN leads l ON m.lead_id = l.id
        WHERE {where_sql}
        ORDER BY {sort_col} {sort_direction}
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])
    cursor.execute(query, params)
    
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return {
        "data": messages,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }


@router.get("/chart-data")
async def get_chart_data(
    macro_intent: Optional[str] = Query(None),
    urgency: Optional[str] = Query(None),
    funnel_stage: Optional[str] = Query(None),
):
    """Get aggregated chart data for visualizations with optional filters."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Build filter clauses dynamically for messages joining leads
    where_clauses = ["m.direction = 'inbound'"]
    params = []
    
    if macro_intent:
        where_clauses.append("m.macro_intent = ?")
        params.append(macro_intent)
    if urgency:
        where_clauses.append("l.urgency = ?")
        params.append(urgency)
    if funnel_stage:
        where_clauses.append("l.funnel_stage = ?")
        params.append(funnel_stage)
        
    where_sql = " AND ".join(where_clauses)
    
    # Micro intent distribution
    cursor.execute(f"""
        SELECT m.micro_intent, COUNT(*) as count
        FROM messages m JOIN leads l ON m.lead_id = l.id
        WHERE {where_sql} AND m.micro_intent IS NOT NULL
        GROUP BY m.micro_intent
    """, params)
    micro_dist = {row["micro_intent"]: row["count"] for row in cursor.fetchall()}
    
    # Macro intent distribution
    cursor.execute(f"""
        SELECT m.macro_intent, COUNT(*) as count
        FROM messages m JOIN leads l ON m.lead_id = l.id
        WHERE {where_sql} AND m.macro_intent IS NOT NULL
        GROUP BY m.macro_intent
    """, params)
    intent_dist = {row["macro_intent"]: row["count"] for row in cursor.fetchall()}
    
    # Funnel distribution
    cursor.execute(f"""
        SELECT l.funnel_stage, COUNT(DISTINCT l.id) as count
        FROM messages m JOIN leads l ON m.lead_id = l.id
        WHERE {where_sql}
        GROUP BY l.funnel_stage
    """, params)
    funnel_dist = [{"stage": row["funnel_stage"], "count": row["count"]} for row in cursor.fetchall()]
    
    # Urgency distribution
    cursor.execute(f"""
        SELECT l.urgency, COUNT(DISTINCT l.id) as count
        FROM messages m JOIN leads l ON m.lead_id = l.id
        WHERE {where_sql}
        GROUP BY l.urgency
    """, params)
    urgency_dist = {row["urgency"]: row["count"] for row in cursor.fetchall()}
    
    # Lead source distribution
    cursor.execute(f"""
        SELECT l.lead_source, COUNT(DISTINCT l.id) as count
        FROM messages m JOIN leads l ON m.lead_id = l.id
        WHERE {where_sql}
        GROUP BY l.lead_source
    """, params)
    source_dist = {row["lead_source"]: row["count"] for row in cursor.fetchall()}
    
    # Recent message volume (last 7 days by day)
    cursor.execute(f"""
        SELECT DATE(m.created_at) as day, COUNT(*) as count
        FROM messages m JOIN leads l ON m.lead_id = l.id
        WHERE {where_sql}
        GROUP BY DATE(m.created_at)
        ORDER BY day DESC
        LIMIT 7
    """, params)
    daily_volume = [{"date": row["day"], "count": row["count"]} for row in cursor.fetchall()][::-1]
    
    conn.close()
    
    return {
        "macro_intent_distribution": intent_dist,
        "micro_intent_distribution": micro_dist,
        "funnel": funnel_dist,
        "urgency_distribution": urgency_dist,
        "source_distribution": source_dist,
        "daily_volume": daily_volume,
    }
