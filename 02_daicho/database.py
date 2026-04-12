"""SQLite DB初期化"""
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "daicho.db"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

# 以下は初期サンプルデータです - 実際の運用では適宜内容を変更してください
SAMPLE_DATA = [
    {
        "record_id": 9001,
        "equipment_name": "横流式沈殿池スクレーパ №1",
        "model": "横流式",
        "facility_no": "F01",
        "facility_name": "東部第一浄化センター",
        "location": "最初沈殿池棟",
        "category_l": "機械",
        "category_m": "汚水処理設備",
        "category_s": "スクレーパ",
        "op_status": "稼働中",
        "manufacturer": "株式会社 東洋環境機械",
        "installed_at": "1976-03-31",
        "service_life": 30,
        "notes1": "竣工時設置。駆動チェーン経年劣化のため要注意。",
    },
    {
        "record_id": 9002,
        "equipment_name": "高圧受変電設備（６kV キュービクル）",
        "model": "屋外収納形",
        "facility_no": "F01",
        "facility_name": "東部第一浄化センター",
        "location": "電気室",
        "category_l": "電気",
        "category_m": "受変電設備",
        "category_s": "キュービクル",
        "op_status": "稼働中",
        "manufacturer": "四菱電機株式会社",
        "installed_at": "1988-09-30",
        "service_life": 25,
        "notes1": "竣工時設置。絶縁劣化診断実施済み（R3年度）。",
    },
    {
        "record_id": 9003,
        "equipment_name": "汚泥脱水機 №2（ベルトプレス形）",
        "model": "BP-1500",
        "facility_no": "F02",
        "facility_name": "北南水再生センター",
        "location": "汚泥処理棟 1階",
        "category_l": "機械",
        "category_m": "汚泥処理設備",
        "category_s": "脱水機",
        "op_status": "稼働中",
        "manufacturer": "株式会社 大和環境プラント",
        "installed_at": "1998-03-25",
        "service_life": 20,
        "notes1": "ベルト交換履歴：H21・H28・R3年度。",
    },
    {
        "record_id": 9004,
        "equipment_name": "中央監視制御盤（水処理系統用）",
        "model": "屋内自立形",
        "facility_no": "F03",
        "facility_name": "東部第一浄化センター",
        "location": "中央監視室",
        "category_l": "電気",
        "category_m": "監視制御設備",
        "category_s": "監視盤",
        "op_status": "稼働中",
        "manufacturer": "栄日計装株式会社",
        "installed_at": "2005-11-30",
        "service_life": 15,
        "notes1": "H30年度にPLC換装済み。表示器は未更新。",
    },
    {
        "record_id": 9005,
        "equipment_name": "雨水排水ポンプ No.3（水中形）",
        "model": "65UW-52.2",
        "facility_no": "F03",
        "facility_name": "東部第一浄化センター",
        "location": "ポンプ室 B系",
        "category_l": "機械",
        "category_m": "ポンプ設備",
        "category_s": "水中ポンプ",
        "op_status": "稼働中",
        "manufacturer": "株式会社 泰和ポンプ製作所",
        "installed_at": "2015-02-28",
        "service_life": 15,
        "notes1": "R4年度オーバーホール実施済み。次回点検R9予定。",
    },
    {
        "record_id": 9006,
        "equipment_name": "放流水量計（電磁式）",
        "model": "AXF150G",
        "facility_no": "F03",
        "facility_name": "北西ポンプ場",
        "location": "放流渠 計測室",
        "category_l": "電気",
        "category_m": "計測設備",
        "category_s": "流量計",
        "op_status": "稼働中",
        "manufacturer": "栄日計装株式会社",
        "installed_at": "2022-10-01",
        "service_life": 10,
        "notes1": "R4年度設備更新時に設置。",
    },
]


def seed_sample_data():
    """equipmentテーブルが空のときにサンプルデータを投入する"""
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM equipment").fetchone()[0]
        if count > 0:
            return 0

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        inserted = 0
        for row in SAMPLE_DATA:
            row = dict(row)
            row["deleted"] = 0
            row["created_at"] = now
            cols = ", ".join(row.keys())
            placeholders = ", ".join(["?"] * len(row))
            conn.execute(
                f"INSERT INTO equipment ({cols}) VALUES ({placeholders})",
                list(row.values()),
            )
            inserted += 1
        return inserted


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
