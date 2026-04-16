"""
Database schema setup and migrations for JAL Admissions AI System.
Creates all required tables and indexes.
"""
from backend.database.connection import get_db


def run_migrations():
    """Create all tables and indexes if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()
    
    # --- Table: leads ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id              TEXT PRIMARY KEY,
            session_id      TEXT UNIQUE NOT NULL,
            name            TEXT,
            contact_type    TEXT DEFAULT 'unknown',
            language_pref   TEXT DEFAULT 'id',
            school_origin   TEXT,
            school_type     TEXT,
            interested_program TEXT,
            nationality     TEXT,
            academic_achievement TEXT,
            financial_concern INTEGER DEFAULT 0,
            funnel_stage    TEXT DEFAULT 'awareness',
            urgency         TEXT DEFAULT 'low',
            conversion_probability REAL DEFAULT 0.0,
            profile_json    TEXT,
            assigned_counselor TEXT,
            channel         TEXT DEFAULT 'chatbot',
            tags            TEXT,
            created_at      TEXT NOT NULL,
            updated_at      TEXT NOT NULL
        )
    """)
    
    # --- Table: messages ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id              TEXT PRIMARY KEY,
            lead_id         TEXT NOT NULL REFERENCES leads(id),
            direction       TEXT NOT NULL,
            content         TEXT NOT NULL,
            language        TEXT,
            intent          TEXT,
            intent_confidence REAL,
            sentiment       TEXT,
            processing_log  TEXT,
            processing_time_ms INTEGER,
            created_at      TEXT NOT NULL
        )
    """)
    
    # --- Table: draft_responses ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS draft_responses (
            id              TEXT PRIMARY KEY,
            message_id      TEXT NOT NULL REFERENCES messages(id),
            lead_id         TEXT NOT NULL REFERENCES leads(id),
            content         TEXT NOT NULL,
            personalization_signals TEXT,
            status          TEXT DEFAULT 'pending',
            edited_content  TEXT,
            created_at      TEXT NOT NULL
        )
    """)
    
    # --- Table: next_actions ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS next_actions (
            id              TEXT PRIMARY KEY,
            lead_id         TEXT NOT NULL REFERENCES leads(id),
            action_type     TEXT NOT NULL,
            action_detail   TEXT NOT NULL,
            priority        TEXT DEFAULT 'medium',
            reasoning       TEXT,
            due_at          TEXT,
            completed_at    TEXT,
            created_at      TEXT NOT NULL
        )
    """)
    
    # --- Indexes ---
    index_statements = [
        "CREATE INDEX IF NOT EXISTS idx_leads_funnel ON leads(funnel_stage)",
        "CREATE INDEX IF NOT EXISTS idx_leads_urgency ON leads(urgency)",
        "CREATE INDEX IF NOT EXISTS idx_leads_created ON leads(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_leads_session ON leads(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_messages_lead ON messages(lead_id)",
        "CREATE INDEX IF NOT EXISTS idx_messages_intent ON messages(intent)",
        "CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_drafts_lead ON draft_responses(lead_id)",
        "CREATE INDEX IF NOT EXISTS idx_drafts_status ON draft_responses(status)",
        "CREATE INDEX IF NOT EXISTS idx_actions_lead ON next_actions(lead_id)",
        "CREATE INDEX IF NOT EXISTS idx_actions_priority ON next_actions(priority)",
        "CREATE INDEX IF NOT EXISTS idx_actions_due ON next_actions(due_at)",
    ]
    
    for stmt in index_statements:
        cursor.execute(stmt)
    
    conn.commit()
    conn.close()
    print("✅ Database migrations completed successfully.")


if __name__ == "__main__":
    run_migrations()
