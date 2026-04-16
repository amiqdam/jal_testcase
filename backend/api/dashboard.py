"""
Dashboard API endpoints — summary stats, funnel data, analytics.
"""
from fastapi import APIRouter
from backend.services.lead_service import LeadService
from backend.database.connection import get_db

router = APIRouter()
lead_service = LeadService()


@router.get("/summary")
async def dashboard_summary():
    """Get aggregated dashboard stats."""
    return lead_service.get_dashboard_summary()


@router.get("/funnel")
async def funnel_data():
    """Get data for funnel visualization."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT funnel_stage, COUNT(*) as count 
        FROM leads 
        GROUP BY funnel_stage
        ORDER BY CASE funnel_stage
            WHEN 'awareness' THEN 1
            WHEN 'interest' THEN 2
            WHEN 'consideration' THEN 3
            WHEN 'decision' THEN 4
            WHEN 'enrolled' THEN 5
        END
    """)
    
    stages = [{"stage": row["funnel_stage"], "count": row["count"]} for row in cursor.fetchall()]
    conn.close()
    
    return {"funnel": stages}


@router.get("/analytics")
async def analytics():
    """Get analytics data — trends, conversion rates, attention items."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Intent distribution
    cursor.execute("""
        SELECT intent, COUNT(*) as count 
        FROM messages 
        WHERE direction = 'inbound' AND intent IS NOT NULL
        GROUP BY intent
        ORDER BY count DESC
    """)
    intent_dist = [{"intent": row["intent"], "count": row["count"]} for row in cursor.fetchall()]
    
    # Daily trend (last 30 days)
    cursor.execute("""
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM leads
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        LIMIT 30
    """)
    daily_trend = [{"date": row["date"], "count": row["count"]} for row in cursor.fetchall()]
    
    # Attention items (critical/high urgency)
    cursor.execute("""
        SELECT l.id, l.name, l.session_id, l.urgency, l.funnel_stage,
               m.content as last_message
        FROM leads l
        LEFT JOIN (
            SELECT lead_id, content,
                   ROW_NUMBER() OVER (PARTITION BY lead_id ORDER BY created_at DESC) as rn
            FROM messages WHERE direction = 'inbound'
        ) m ON l.id = m.lead_id AND m.rn = 1
        WHERE l.urgency IN ('critical', 'high')
        ORDER BY CASE l.urgency WHEN 'critical' THEN 1 WHEN 'high' THEN 2 END
        LIMIT 20
    """)
    attention = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    return {
        "intent_distribution": intent_dist,
        "daily_trend": daily_trend,
        "attention_items": attention
    }
