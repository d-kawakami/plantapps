"""
DB初期化・シードデータ投入スクリプト
使い方: python database.py
"""
import os
import sqlite3
from pathlib import Path
from seed_data import INSPECTION_ITEMS

DB_PATH = Path(os.environ.get('TENKEN_DB_PATH', str(Path(__file__).parent / "tenken.db")))


def init_db():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # ─── テーブル作成 ────────────────────────────────────────
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS inspection_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            code        TEXT    NOT NULL,
            building    TEXT    NOT NULL,
            location    TEXT    NOT NULL,
            description TEXT    DEFAULT '',
            base_memo   TEXT    DEFAULT '',
            senpatu     TEXT    DEFAULT '',
            result_hint TEXT    DEFAULT '',
            day_of_week INTEGER NOT NULL,
            week_filter INTEGER,
            sort_order  INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS senpatu_groups (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            day_of_week     INTEGER NOT NULL,
            group_name      TEXT    NOT NULL,
            sort_order      INTEGER NOT NULL DEFAULT 0,
            machine_name    TEXT    NOT NULL DEFAULT '',
            monthly_numbers TEXT    NOT NULL DEFAULT '[]'
        );

        CREATE TABLE IF NOT EXISTS inspection_results (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id         INTEGER NOT NULL REFERENCES inspection_items(id),
            inspection_date TEXT    NOT NULL,
            result          TEXT,
            memo            TEXT    DEFAULT '',
            created_at      TEXT    DEFAULT (datetime('now', 'localtime')),
            updated_at      TEXT    DEFAULT (datetime('now', 'localtime'))
        );

        CREATE UNIQUE INDEX IF NOT EXISTS idx_result_unique
            ON inspection_results(item_id, inspection_date);
    """)

    # ─── 既存DBへのカラム追加（マイグレーション）───────────────
    for col_def in [
        "ALTER TABLE inspection_items ADD COLUMN base_memo TEXT DEFAULT ''",
        "ALTER TABLE inspection_items ADD COLUMN senpatu TEXT DEFAULT ''",
        "ALTER TABLE inspection_items ADD COLUMN fault_memo TEXT DEFAULT ''",
        "ALTER TABLE inspection_items ADD COLUMN result_hint TEXT DEFAULT ''",
    ]:
        try:
            cur.execute(col_def)
            conn.commit()
        except Exception:
            pass  # 既に存在する場合はスキップ

    # ─── シードデータ投入（既存データは変更しない）────────────
    existing = cur.execute("SELECT COUNT(*) FROM inspection_items").fetchone()[0]
    if existing == 0:
        cur.executemany("""
            INSERT INTO inspection_items
                (code, building, location, description, day_of_week, week_filter, sort_order)
            VALUES
                (:code, :building, :location, :description, :day_of_week, :week_filter, :sort_order)
        """, INSPECTION_ITEMS)
        print(f"シードデータを {len(INSPECTION_ITEMS)} 件投入しました。")
    else:
        print(f"点検項目は既に {existing} 件登録されています。スキップ。")

    conn.commit()
    conn.close()
    print(f"DBを初期化しました: {DB_PATH}")


if __name__ == "__main__":
    init_db()
