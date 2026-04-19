"""
SQLite データアクセス関数
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "tenken.db"


def get_db():
    """DB接続を返す。row_factoryでdict風アクセスを有効化"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


# ─── 点検項目 ────────────────────────────────────────────────

def get_senpatu_groups(day_of_week: int) -> list[dict]:
    """指定曜日の先発グループデータを返す"""
    sql = """
        SELECT id, day_of_week, group_name, sort_order, machine_name, monthly_numbers
        FROM senpatu_groups
        WHERE day_of_week = ?
        ORDER BY group_name, sort_order
    """
    with get_db() as conn:
        rows = conn.execute(sql, (day_of_week,)).fetchall()
    return [dict(r) for r in rows]


def get_items(day_of_week: int, week_number: int) -> list[dict]:
    """
    指定曜日・週番号の点検項目を返す。
    week_filter=NULL (毎週) または week_filter=week_number にマッチする行を返す。
    """
    sql = """
        SELECT id, code, building, location, description, base_memo, senpatu,
               fault_memo, result_hint, day_of_week, week_filter, sort_order
        FROM inspection_items
        WHERE day_of_week = ?
          AND (week_filter IS NULL OR week_filter = ?)
        ORDER BY CAST(substr(code, 1, instr(code, '-') - 1) AS INTEGER),
                 CAST(substr(code, instr(code, '-') + 1)    AS INTEGER)
    """
    with get_db() as conn:
        rows = conn.execute(sql, (day_of_week, week_number)).fetchall()
    return [dict(r) for r in rows]


def get_all_items() -> list[dict]:
    """全点検項目を返す（管理用）"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM inspection_items ORDER BY day_of_week, building, sort_order"
        ).fetchall()
    return [dict(r) for r in rows]


# ─── 点検結果 ────────────────────────────────────────────────

def get_results(inspection_date: str) -> list[dict]:
    """指定日の点検結果を全件返す"""
    sql = """
        SELECT r.id, r.item_id, r.inspection_date, r.result, r.memo,
               r.created_at, r.updated_at,
               i.code, i.building, i.location
        FROM inspection_results r
        JOIN inspection_items i ON i.id = r.item_id
        WHERE r.inspection_date = ?
        ORDER BY i.day_of_week, i.building, i.sort_order
    """
    with get_db() as conn:
        rows = conn.execute(sql, (inspection_date,)).fetchall()
    return [dict(r) for r in rows]


def upsert_result(item_id: int, inspection_date: str, result: str, memo: str) -> dict:
    """
    点検結果を保存する（UPSERT）。
    既存レコードがあれば更新、なければ挿入。
    """
    sql = """
        INSERT INTO inspection_results (item_id, inspection_date, result, memo, updated_at)
        VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
        ON CONFLICT(item_id, inspection_date)
        DO UPDATE SET
            result     = excluded.result,
            memo       = excluded.memo,
            updated_at = datetime('now', 'localtime')
    """
    with get_db() as conn:
        conn.execute(sql, (item_id, inspection_date, result, memo))
        conn.commit()
        row = conn.execute(
            "SELECT * FROM inspection_results WHERE item_id=? AND inspection_date=?",
            (item_id, inspection_date)
        ).fetchone()
    return dict(row) if row else {}


def delete_results_for_date(inspection_date: str) -> int:
    """指定日の全点検結果を削除する"""
    with get_db() as conn:
        cur = conn.execute(
            "DELETE FROM inspection_results WHERE inspection_date = ?",
            (inspection_date,)
        )
        conn.commit()
    return cur.rowcount


def get_results_for_dates(dates: list[str]) -> list[dict]:
    """複数日の点検結果を一括返す（週単位書き出し用）"""
    if not dates:
        return []
    placeholders = ",".join("?" * len(dates))
    sql = f"""
        SELECT r.id, r.item_id, r.inspection_date, r.result, r.memo,
               r.created_at, r.updated_at,
               i.code, i.building, i.location
        FROM inspection_results r
        JOIN inspection_items i ON i.id = r.item_id
        WHERE r.inspection_date IN ({placeholders})
        ORDER BY i.day_of_week, i.building, i.sort_order
    """
    with get_db() as conn:
        rows = conn.execute(sql, dates).fetchall()
    return [dict(r) for r in rows]


def batch_upsert_results(records: list[dict]) -> int:
    """
    IndexedDBからの同期用バッチ保存。
    records: [{"item_id": int, "inspection_date": str, "result": str, "memo": str}, ...]
    """
    sql = """
        INSERT INTO inspection_results (item_id, inspection_date, result, memo, updated_at)
        VALUES (:item_id, :inspection_date, :result, :memo, datetime('now', 'localtime'))
        ON CONFLICT(item_id, inspection_date)
        DO UPDATE SET
            result     = excluded.result,
            memo       = excluded.memo,
            updated_at = datetime('now', 'localtime')
    """
    with get_db() as conn:
        conn.executemany(sql, records)
        conn.commit()
    return len(records)
