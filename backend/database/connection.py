"""
Database connection setup for JAL Admissions AI System.
Supports SQLite (default) and PostgreSQL.
"""
import sqlite3
import os
from backend.config import DATABASE_URL


def get_db_path() -> str:
    """Extract file path from SQLite URL."""
    if DATABASE_URL.startswith("sqlite:///"):
        return DATABASE_URL.replace("sqlite:///", "")
    return "jal_admissions.db"


def get_db() -> sqlite3.Connection:
    """
    Get a SQLite database connection with optimized settings.
    Returns a connection with Row factory for dict-like access.
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    # Enable WAL mode for better concurrency
    conn.execute("PRAGMA journal_mode=WAL")
    # Enable foreign keys
    conn.execute("PRAGMA foreign_keys=ON")
    # Optimize for performance
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
    
    return conn


def close_db(conn: sqlite3.Connection):
    """Close database connection."""
    if conn:
        conn.close()
