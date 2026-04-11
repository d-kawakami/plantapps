"""SQLite DB初期化"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "daicho.db"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS equipment (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id      INTEGER UNIQUE,
                equipment_name TEXT NOT NULL,
                model          TEXT,
                facility_no    TEXT,
                facility_name  TEXT,
                location       TEXT,
                category_l     TEXT,
                category_m     TEXT,
                category_s     TEXT,
                op_status      TEXT DEFAULT '稼働中',
                manufacturer   TEXT,
                installed_at   DATE,
                service_life   INTEGER,
                notes1         TEXT,
                deleted        INTEGER DEFAULT 0,
                updated_at     DATETIME,
                updated_by     TEXT,
                created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_equipment_facility        ON equipment(facility_no);
            CREATE INDEX IF NOT EXISTS idx_equipment_category        ON equipment(category_l, category_m, category_s);
            CREATE INDEX IF NOT EXISTS idx_equipment_status          ON equipment(op_status);
            CREATE INDEX IF NOT EXISTS idx_equipment_installed       ON equipment(installed_at);
            CREATE INDEX IF NOT EXISTS idx_equipment_deleted         ON equipment(deleted);
            CREATE INDEX IF NOT EXISTS idx_equipment_facility_active ON equipment(facility_no, deleted);

            CREATE TABLE IF NOT EXISTS measurement (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER REFERENCES equipment(id),
                measured_at  DATE NOT NULL,
                value        REAL,
                threshold    REAL,
                note         TEXT,
                recorded_by  TEXT,
                created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS equipment_note (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                equipment_id INTEGER REFERENCES equipment(id),
                note_id      INTEGER,
                note_app     TEXT DEFAULT '03_notedb',
                created_at   DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
