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
                id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id           INTEGER UNIQUE,
                customer_code       TEXT,
                facility_no         TEXT,
                facility_name       TEXT,
                equipment_id        INTEGER,
                equipment_name      TEXT NOT NULL,
                model               TEXT,
                work_type           TEXT,
                location            TEXT,
                manufacturer        TEXT,
                category_l          TEXT,
                category_m          TEXT,
                category_s          TEXT,
                installed_at        DATE,
                removed_at          DATE,
                service_life        INTEGER,
                target_life         INTEGER,
                acquisition_cost    INTEGER,
                replacement_cost    INTEGER,
                asset_group         TEXT,
                fixed_asset_no      TEXT,
                op_status           TEXT DEFAULT '稼働中',
                maintenance_method  TEXT,
                legal_inspection    INTEGER DEFAULT 0,
                importance          TEXT,
                degradation_flag    INTEGER DEFAULT 0,
                cost_impact         TEXT,
                upgrade_target      INTEGER DEFAULT 0,
                high_degradation    INTEGER DEFAULT 0,
                spec                TEXT,
                notes1              TEXT,
                notes2              TEXT,
                series_no           TEXT,
                unit_no             TEXT,
                form_no             TEXT,
                maintenance_form_id TEXT,
                completion_docs     INTEGER DEFAULT 0,
                maintenance_manual  INTEGER DEFAULT 0,
                instruction_manual  INTEGER DEFAULT 0,
                spare_parts_list    INTEGER DEFAULT 0,
                asset_category1     TEXT,
                asset_category2     TEXT,
                asset_category3     TEXT,
                asset_category4     TEXT,
                asset_category5     TEXT,
                prev_facility_no    TEXT,
                prev_equipment_id   TEXT,
                main_equipment      INTEGER DEFAULT 0,
                multi_measurement   TEXT,
                threshold           REAL,
                disposal_limit      TEXT,
                drainage_class      TEXT,
                dept_code           TEXT,
                deleted             INTEGER DEFAULT 0,
                updated_at          DATETIME,
                updated_by          TEXT,
                created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
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
