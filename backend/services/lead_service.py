"""
LeadService — Business logic for lead management (CRUD + funnel rules).
"""
import uuid
import json
from datetime import datetime, timezone
from typing import Optional
from backend.database.connection import get_db
from backend.config import FUNNEL_STAGES


class LeadService:
    """Business logic for lead management."""
    
    def get_or_create_lead(self, session_id: str) -> dict:
        """Get existing lead by session or create new one."""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM leads WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        
        if row:
            lead = dict(row)
            conn.close()
            return lead
        
        # Create new lead
        now = datetime.now(timezone.utc).isoformat()
        lead_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO leads (id, session_id, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        """, (lead_id, session_id, now, now))
        
        conn.commit()
        
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        lead = dict(cursor.fetchone())
        conn.close()
        return lead
    
    def update_profile(self, lead_id: str, entities: dict) -> dict:
        """
        Incrementally update lead profile with extracted entities.
        NEVER overwrite non-null with null.
        """
        conn = get_db()
        cursor = conn.cursor()
        
        # Get current lead
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        lead = dict(cursor.fetchone())
        
        now = datetime.now(timezone.utc).isoformat()
        updates = []
        params = []
        
        # Map entity fields to lead columns
        field_mapping = {
            "name": "name",
            "contact_type": "contact_type",
            "school_origin": "school_origin",
            "school_type": "school_type",
            "interested_program": "interested_program",
            "nationality": "nationality",
            "academic_achievement": "academic_achievement",
            "language": "language_pref",
        }
        
        for entity_key, db_column in field_mapping.items():
            new_value = entities.get(entity_key)
            if new_value and new_value != "unknown" and new_value != "N/A":
                current_value = lead.get(db_column)
                if not current_value or current_value == "unknown":
                    updates.append(f"{db_column} = ?")
                    params.append(new_value)
        
        # Handle financial_concern (boolean)
        if entities.get("financial_concern"):
            updates.append("financial_concern = ?")
            params.append(1)
        
        if updates:
            updates.append("updated_at = ?")
            params.append(now)
            params.append(lead_id)
            
            query = f"UPDATE leads SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        # Return updated lead
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        updated_lead = dict(cursor.fetchone())
        conn.close()
        return updated_lead
    
    def update_funnel_stage(self, lead_id: str, new_stage: str, new_urgency: str) -> dict:
        """
        Update lead's funnel stage and urgency.
        Stage can only move forward (no backward), unless admin override.
        """
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT funnel_stage, urgency FROM leads WHERE id = ?", (lead_id,))
        row = cursor.fetchone()
        current_stage = row["funnel_stage"]
        
        # Only move forward in funnel
        current_idx = FUNNEL_STAGES.index(current_stage) if current_stage in FUNNEL_STAGES else 0
        new_idx = FUNNEL_STAGES.index(new_stage) if new_stage in FUNNEL_STAGES else 0
        
        final_stage = new_stage if new_idx >= current_idx else current_stage
        
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute("""
            UPDATE leads 
            SET funnel_stage = ?, urgency = ?, updated_at = ?
            WHERE id = ?
        """, (final_stage, new_urgency, now, lead_id))
        
        conn.commit()
        
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        lead = dict(cursor.fetchone())
        conn.close()
        return lead
    
    def get_leads_filtered(self, stage: str = None, urgency: str = None,
                           intent: str = None, search: str = None,
                           page: int = 1, limit: int = 20) -> dict:
        """Get filtered and paginated list of leads with last message info."""
        conn = get_db()
        cursor = conn.cursor()
        
        where_clauses = []
        params = []
        
        if stage:
            where_clauses.append("l.funnel_stage = ?")
            params.append(stage)
        if urgency:
            where_clauses.append("l.urgency = ?")
            params.append(urgency)
        if search:
            where_clauses.append("(l.name LIKE ? OR l.session_id LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        # Count total
        count_query = f"SELECT COUNT(*) as total FROM leads l {where_sql}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()["total"]
        
        # Get leads with last message
        offset = (page - 1) * limit
        query = f"""
            SELECT l.*, 
                   m.content as last_message_preview,
                   m.created_at as last_message_at
            FROM leads l
            LEFT JOIN (
                SELECT lead_id, content, created_at,
                       ROW_NUMBER() OVER (PARTITION BY lead_id ORDER BY created_at DESC) as rn
                FROM messages
                WHERE direction = 'inbound'
            ) m ON l.id = m.lead_id AND m.rn = 1
            {where_sql}
            ORDER BY l.updated_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        cursor.execute(query, params)
        
        leads = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return {
            "data": leads,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }
    
    def get_lead_detail(self, lead_id: str) -> Optional[dict]:
        """Get complete lead detail with messages, drafts, and actions."""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        lead = dict(row)
        
        # Get messages
        cursor.execute("""
            SELECT * FROM messages WHERE lead_id = ? ORDER BY created_at ASC
        """, (lead_id,))
        lead["messages"] = [dict(r) for r in cursor.fetchall()]
        
        # Get draft responses
        cursor.execute("""
            SELECT * FROM draft_responses WHERE lead_id = ? ORDER BY created_at DESC
        """, (lead_id,))
        lead["draft_responses"] = [dict(r) for r in cursor.fetchall()]
        
        # Get next actions
        cursor.execute("""
            SELECT * FROM next_actions WHERE lead_id = ? ORDER BY created_at DESC
        """, (lead_id,))
        lead["next_actions"] = [dict(r) for r in cursor.fetchall()]
        
        conn.close()
        return lead
    
    def get_dashboard_summary(self) -> dict:
        """Aggregate stats for dashboard overview."""
        conn = get_db()
        cursor = conn.cursor()
        
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        # Total leads
        cursor.execute("SELECT COUNT(*) as total FROM leads")
        total = cursor.fetchone()["total"]
        
        # New today
        cursor.execute("SELECT COUNT(*) as count FROM leads WHERE created_at LIKE ?", (f"{today}%",))
        new_today = cursor.fetchone()["count"]
        
        # Per funnel stage
        cursor.execute("SELECT funnel_stage, COUNT(*) as count FROM leads GROUP BY funnel_stage")
        funnel_distribution = {row["funnel_stage"]: row["count"] for row in cursor.fetchall()}
        
        # Per urgency
        cursor.execute("SELECT urgency, COUNT(*) as count FROM leads GROUP BY urgency")
        urgency_distribution = {row["urgency"]: row["count"] for row in cursor.fetchall()}
        
        # Critical/high attention count
        cursor.execute("SELECT COUNT(*) as count FROM leads WHERE urgency IN ('critical', 'high')")
        attention_count = cursor.fetchone()["count"]
        
        conn.close()
        
        return {
            "total_leads": total,
            "new_today": new_today,
            "attention_needed": attention_count,
            "funnel_distribution": funnel_distribution,
            "urgency_distribution": urgency_distribution,
        }
    
    def admin_override(self, lead_id: str, updates: dict) -> Optional[dict]:
        """Admin override for funnel_stage, urgency, etc."""
        conn = get_db()
        cursor = conn.cursor()
        
        set_clauses = []
        params = []
        
        for field in ["funnel_stage", "urgency", "assigned_counselor", "tags"]:
            if field in updates and updates[field] is not None:
                set_clauses.append(f"{field} = ?")
                params.append(updates[field])
        
        if not set_clauses:
            conn.close()
            return None
        
        now = datetime.now(timezone.utc).isoformat()
        set_clauses.append("updated_at = ?")
        params.append(now)
        params.append(lead_id)
        
        cursor.execute(f"UPDATE leads SET {', '.join(set_clauses)} WHERE id = ?", params)
        conn.commit()
        
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        lead = dict(cursor.fetchone())
        conn.close()
        return lead
