"""Database connection and initialization management for EchoMind.

Uses standard Python sqlite3 with row factory enabled for clean dict-like access.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import sqlite3
from typing import Optional
from config.settings import settings


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Create a sqlite3 connection with foreign keys enabled and Row factory."""
    path = db_path or settings.DB_PATH
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize the SQLite database schema from database/schema.sql."""
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn = get_connection(db_path)
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()
