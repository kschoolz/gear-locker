import sqlite3
from pathlib import Path

DB_PATH = "gear.db"
MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"


def _dict_factory(cursor, row):
    return {col[0]: value for col, value in zip(cursor.description, row)}


def get_connection(path=DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = _dict_factory
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def migrate(path=DB_PATH):
    conn = get_connection(path)
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            " filename TEXT PRIMARY KEY,"
            " applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.commit()
        applied = {r["filename"] for r in conn.execute("SELECT filename FROM schema_migrations")}
        for file in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if file.name in applied:
                continue
            name = file.name.replace("'", "''")
            try:
                conn.executescript(
                    f"BEGIN;\n{file.read_text()}\n;"
                    f"INSERT INTO schema_migrations (filename) VALUES ('{name}');\nCOMMIT;"
                )
            except Exception:
                conn.rollback()
                raise
    finally:
        conn.close()
