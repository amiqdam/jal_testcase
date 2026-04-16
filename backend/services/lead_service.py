"""
LeadService — Business logic for lead management (CRUD + funnel rules).
Email-based upsert to prevent duplicates.
"""
import uuid
import json
from datetime import datetime, timezone
from typing import Optional
from backend.database.connection import get_db
from backend.config import FUNNEL_STAGES


class LeadService:
    """Business logic for lead management."""
    
    def get_or_create_lead(self, email: str, name: str, lead_source: str = "lainnya") -> dict:
        """Get existing lead by email or create new one (upsert)."""
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM leads WHERE email = ?", (email,))
        row = cursor.fetchone()
        
        if row:
            lead = dict(row)
            # Update name if provided and different
            if name and lead.get("name") != name:
                cursor.execute("UPDATE leads SET name = ?, updated_at = ? WHERE id = ?",
                               (name, datetime.now(timezone.utc).isoformat(), lead["id"]))
                conn.commit()
                lead["name"] = name
            conn.close()
            return lead
        
        # Create new lead — lead_source is set only on first creation (never overwritten)
        now = datetime.now(timezone.utc).isoformat()
        lead_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO leads (id, email, name, lead_source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (lead_id, email, name, lead_source or "lainnya", now, now))
        
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
            "kelas": "kelas",
            "interested_program": "interested_program",
            "nationality": "nationality",
            "academic_achievement": "academic_achievement",
            "phone_number": "phone_number",
            "tanggal_lahir": "tanggal_lahir",
            "language": "language_pref",
        }
        
        for entity_key, db_column in field_mapping.items():
            new_value = entities.get(entity_key)
            if new_value and new_value != "unknown" and new_value != "N/A" and new_value != "null":
                current_value = lead.get(db_column)
                if not current_value or current_value == "unknown":
                    updates.append(f"{db_column} = ?")
                    params.append(new_value)
        
        # Handle umur (integer)
        umur = entities.get("umur")
        if umur and isinstance(umur, (int, float)) and not lead.get("umur"):
            updates.append("umur = ?")
            params.append(int(umur))
        
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
        
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        updated_lead = dict(cursor.fetchone())
        conn.close()
        return updated_lead
    
    def update_funnel_stage(self, lead_id: str, new_stage: str, new_urgency: str,
                            macro_intent: str = None, micro_intent: str = None) -> dict:
        """Update lead's funnel stage, urgency, and classification."""
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
        
        set_clauses = ["funnel_stage = ?", "urgency = ?", "updated_at = ?"]
        params = [final_stage, new_urgency, now]
        
        if macro_intent:
            set_clauses.append("macro_intent = ?")
            params.append(macro_intent)
        if micro_intent:
            set_clauses.append("micro_intent = ?")
            params.append(micro_intent)
        
        params.append(lead_id)
        cursor.execute(f"UPDATE leads SET {', '.join(set_clauses)} WHERE id = ?", params)
        conn.commit()
        
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        lead = dict(cursor.fetchone())
        conn.close()
        return lead
    
    def get_leads_filtered(self, stage: str = None, urgency: str = None,
                           macro_intent: str = None, search: str = None,
                           page: int = 1, limit: int = 20,
                           lead_source: str = None, interested_program: str = None,
                           school_type: str = None, contact_type: str = None) -> dict:
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
        if macro_intent:
            where_clauses.append("l.macro_intent = ?")
            params.append(macro_intent)
        if search:
            where_clauses.append("(l.name LIKE ? OR l.email LIKE ?)")
            params.extend([f"%{search}%", f"%{search}%"])
        if lead_source:
            where_clauses.append("l.lead_source = ?")
            params.append(lead_source)
        if interested_program:
            where_clauses.append("l.interested_program LIKE ?")
            params.append(f"%{interested_program}%")
        if school_type:
            where_clauses.append("l.school_type = ?")
            params.append(school_type)
        if contact_type:
            where_clauses.append("l.contact_type = ?")
            params.append(contact_type)
        
        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        
        count_query = f"SELECT COUNT(*) as total FROM leads l {where_sql}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()["total"]
        
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
        
        cursor.execute("""
            SELECT * FROM messages WHERE lead_id = ? ORDER BY created_at ASC
        """, (lead_id,))
        lead["messages"] = [dict(r) for r in cursor.fetchall()]
        
        cursor.execute("""
            SELECT * FROM draft_responses WHERE lead_id = ? ORDER BY created_at DESC
        """, (lead_id,))
        lead["draft_responses"] = [dict(r) for r in cursor.fetchall()]
        
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
        
        cursor.execute("SELECT COUNT(*) as total FROM leads")
        total = cursor.fetchone()["total"]
        
        cursor.execute("SELECT COUNT(*) as count FROM leads WHERE created_at LIKE ?", (f"{today}%",))
        new_today = cursor.fetchone()["count"]
        
        cursor.execute("SELECT funnel_stage, COUNT(*) as count FROM leads GROUP BY funnel_stage")
        funnel_distribution = {row["funnel_stage"]: row["count"] for row in cursor.fetchall()}
        
        cursor.execute("SELECT urgency, COUNT(*) as count FROM leads GROUP BY urgency")
        urgency_distribution = {row["urgency"]: row["count"] for row in cursor.fetchall()}
        
        cursor.execute("SELECT lead_source, COUNT(*) as count FROM leads GROUP BY lead_source")
        source_distribution = {row["lead_source"]: row["count"] for row in cursor.fetchall()}
        
        cursor.execute("SELECT COUNT(*) as count FROM leads WHERE urgency = 'critical'")
        attention_count = cursor.fetchone()["count"]
        
        conn.close()
        
        return {
            "total_leads": total,
            "new_today": new_today,
            "attention_needed": attention_count,
            "funnel_distribution": funnel_distribution,
            "urgency_distribution": urgency_distribution,
            "source_distribution": source_distribution,
        }
    
    def get_new_events_count(self, since: str = None) -> dict:
        """Get count of new events since timestamp (for toast notifications)."""
        conn = get_db()
        cursor = conn.cursor()
        
        if not since:
            since = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00")
        
        cursor.execute("SELECT COUNT(*) as count FROM leads WHERE created_at > ?", (since,))
        new_leads = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM messages WHERE direction = 'inbound' AND created_at > ?", (since,))
        new_messages = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM complaints_log WHERE status = 'open' AND created_at > ?", (since,))
        new_complaints = cursor.fetchone()["count"]
        
        conn.close()
        
        return {
            "new_leads": new_leads,
            "new_messages": new_messages,
            "new_complaints": new_complaints,
            "total_new": new_leads + new_messages + new_complaints,
        }
    
    def admin_override(self, lead_id: str, updates: dict) -> Optional[dict]:
        """Admin override for funnel_stage, urgency."""
        conn = get_db()
        cursor = conn.cursor()
        
        set_clauses = []
        params = []
        
        for field in ["funnel_stage", "urgency"]:
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
    
    def export_leads_data(self) -> list:
        """Export all leads as list of dicts (for Pandas DataFrame conversion)."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leads ORDER BY created_at DESC")
        leads = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return leads
