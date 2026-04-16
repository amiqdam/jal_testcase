"""
Database connection setup for JAL Admissions AI.
Supports SQLite (default) and PostgreSQL.
"""
import sqlite3
from backend.config import DATABASE_URL


def get_db():
    """
    Get a database connection.
    Returns a sqlite3 connection with Row factory for dict-like access.
    """
    if DATABASE_URL.startswith("sqlite"):
        db_path = DATABASE_URL.replace("sqlite:///", "").replace("./", "")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn
    else:
        raise ValueError(f"Unsupported database URL: {DATABASE_URL}")
