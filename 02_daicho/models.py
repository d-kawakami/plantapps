"""機器台帳 データアクセス層"""
import csv
import io
from datetime import date, datetime
from pathlib import Path

import chardet

from database import get_db

# CSV列名 → DBカラム名マッピング
CSV_COLUMN_MAP = {
    "工種番号": "work_type",
    "レコードID": "record_id",
    "顧客コード": "customer_code",
    "施設番号": "facility_no",
    "施設名称": "facility_name",
    "機器ID": "equipment_id",
    "機器名称": "equipment_name",
    "形式": "model",
    "様式番号": "form_no",
    "完成図書": "completion_docs",
    "保点要領書": "maintenance_manual",
    "取扱説明書": "instruction_manual",
    "予備品リスト": "spare_parts_list",
    "設置場所": "location",
    "資産款": "asset_category1",
    "資産項": "asset_category2",
    "資産目": "asset_category3",
    "資産節": "asset_category4",
    "資産整項": "asset_category5",
    "設置年月日": "installed_at",
    "撤去年月日": "removed_at",
    "更新前施設番号": "prev_facility_no",
    "更新前機器ID": "prev_equipment_id",
    "主要機器": "main_equipment",
    "大分類": "category_l",
    "中分類": "category_m",
    "小分類": "category_s",
    "耐用年数": "service_life",
    "系列番号": "series_no",
    "号機番号": "unit_no",
    "記事１": "notes1",
    "記事２": "notes2",
    "製造所": "manufacturer",
    "稼働状況": "op_status",
    "保全方法": "maintenance_method",
    "管理部署コード": "dept_code",
    "資産グループ": "asset_group",
    "固定資産番号": "fixed_asset_no",
    "仕様": "spec",
    "複数回測定値": "multi_measurement",
    "許容限界値": "threshold",
    "処分制限期間": "disposal_limit",
    "法定点検有無": "legal_inspection",
    "設備重要度": "importance",
    "劣化予兆判断可否": "degradation_flag",
    "コストインパクト": "cost_impact",
    "高度化対象": "upgrade_target",
    "劣化度大": "high_degradation",
    "保守点検様式ID": "maintenance_form_id",
    "排水区分": "drainage_class",
    "削除フラグ": "deleted",
    "更新日時": "updated_at",
    "更新ユーザID": "updated_by",
    "取得価額": "acquisition_cost",
    "目標耐用年数": "target_life",
    "再取得価額": "replacement_cost",
}

# DBカラム名 → CSV列名 (逆引き)
DB_TO_CSV_MAP = {v: k for k, v in CSV_COLUMN_MAP.items()}

INTEGER_FIELDS = {
    "record_id", "equipment_id", "service_life", "target_life",
    "acquisition_cost", "replacement_cost", "legal_inspection",
    "degradation_flag", "upgrade_target", "high_degradation",
    "completion_docs", "maintenance_manual", "instruction_manual",
    "spare_parts_list", "main_equipment", "deleted",
}

REAL_FIELDS = {"threshold"}

DATE_FIELDS = {"installed_at", "removed_at"}

BOOL_CSV_FIELDS = {
    "completion_docs", "maintenance_manual", "instruction_manual",
    "spare_parts_list", "main_equipment", "legal_inspection",
    "degradation_flag", "upgrade_target", "high_degradation",
}


def _coerce(field, value):
    """文字列値をDBの型に変換する"""
    if value is None or value == "":
        return None
    if field in INTEGER_FIELDS:
        try:
            return int(float(str(value).strip()))
        except (ValueError, TypeError):
            return None
    if field in REAL_FIELDS:
        try:
            return float(str(value).strip())
        except (ValueError, TypeError):
            return None
    if field in DATE_FIELDS:
        s = str(value).strip()
        # 日付フォーマット正規化
        for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y%m%d"):
            try:
                return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass
        return None
    return str(value).strip() if str(value).strip() != "" else None


def _build_where(filters):
    """フィルタ辞書からWHERE句とパラメータを構築する"""
    clauses = ["deleted = 0"]
    params = []

    if filters.get("facility_no"):
        clauses.append("facility_no = ?")
        params.append(filters["facility_no"])
    if filters.get("work_type"):
        clauses.append("work_type = ?")
        params.append(filters["work_type"])
    if filters.get("category_l"):
        clauses.append("category_l = ?")
        params.append(filters["category_l"])
    if filters.get("category_m"):
        clauses.append("category_m = ?")
        params.append(filters["category_m"])
    if filters.get("category_s"):
        clauses.append("category_s = ?")
        params.append(filters["category_s"])
    if filters.get("q"):
        clauses.append("equipment_name LIKE ?")
        params.append(f"%{filters['q']}%")
    if filters.get("manufacturer"):
        clauses.append("manufacturer LIKE ?")
        params.append(f"%{filters['manufacturer']}%")
    if filters.get("op_status"):
        clauses.append("op_status = ?")
        params.append(filters["op_status"])
    if filters.get("installed_from"):
        clauses.append("installed_at >= ?")
        params.append(filters["installed_from"])
    if filters.get("installed_to"):
        clauses.append("installed_at <= ?")
        params.append(filters["installed_to"])
    if filters.get("facility_name"):
        clauses.append("facility_name LIKE ?")
        params.append(f"%{filters['facility_name']}%")

    return " AND ".join(clauses), params


def list_equipment(filters=None, page=1, per_page=50):
    """機器一覧を返す (items, total_count)"""
    if filters is None:
        filters = {}
    where, params = _build_where(filters)
    sort = filters.get("sort", "id")
    allowed_sorts = {
        "id", "equipment_name", "facility_name", "installed_at",
        "updated_at", "op_status", "category_l",
    }
    if sort not in allowed_sorts:
        sort = "id"

    offset = (page - 1) * per_page
    with get_db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) FROM equipment WHERE {where}", params
        ).fetchone()[0]
        rows = conn.execute(
            f"SELECT * FROM equipment WHERE {where} ORDER BY {sort} DESC LIMIT ? OFFSET ?",
            params + [per_page, offset],
        ).fetchall()
    return [dict(r) for r in rows], total


def get_equipment(eq_id):
    """1件取得"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM equipment WHERE id = ?", (eq_id,)
        ).fetchone()
    return dict(row) if row else None


def create_equipment(data):
    """新規登録。新しいidを返す"""
    data = dict(data)
    data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data.setdefault("deleted", 0)

    # 有効なカラムのみ
    valid_cols = _get_columns()
    data = {k: v for k, v in data.items() if k in valid_cols and k != "id"}

    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    with get_db() as conn:
        cur = conn.execute(
            f"INSERT INTO equipment ({cols}) VALUES ({placeholders})",
            list(data.values()),
        )
        return cur.lastrowid


def update_equipment(eq_id, data):
    """更新"""
    data = dict(data)
    data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    valid_cols = _get_columns()
    data = {k: v for k, v in data.items() if k in valid_cols and k not in ("id", "created_at")}

    set_clause = ", ".join(f"{k} = ?" for k in data.keys())
    with get_db() as conn:
        conn.execute(
            f"UPDATE equipment SET {set_clause} WHERE id = ?",
            list(data.values()) + [eq_id],
        )


def delete_equipment(eq_id, updated_by=None):
    """論理削除"""
    with get_db() as conn:
        conn.execute(
            "UPDATE equipment SET deleted = 1, updated_at = ?, updated_by = ? WHERE id = ?",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), updated_by, eq_id),
        )


def physical_delete_equipment(eq_id):
    """物理削除"""
    with get_db() as conn:
        conn.execute("DELETE FROM equipment WHERE id = ?", (eq_id,))


def duplicate_equipment(eq_id):
    """複製して新しいidを返す"""
    row = get_equipment(eq_id)
    if not row:
        return None
    row.pop("id", None)
    row.pop("record_id", None)
    row["equipment_id"] = None
    row["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row["deleted"] = 0

    cols = ", ".join(row.keys())
    placeholders = ", ".join(["?"] * len(row))
    with get_db() as conn:
        cur = conn.execute(
            f"INSERT INTO equipment ({cols}) VALUES ({placeholders})",
            list(row.values()),
        )
        return cur.lastrowid


def get_facilities():
    """施設一覧(distinct)を返す"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT facility_no, facility_name FROM equipment WHERE deleted = 0 AND facility_no IS NOT NULL ORDER BY facility_no"
        ).fetchall()
    return [dict(r) for r in rows]


def get_categories():
    """分類一覧(distinct)を返す"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT category_l, category_m, category_s FROM equipment WHERE deleted = 0 ORDER BY category_l, category_m, category_s"
        ).fetchall()
    return [dict(r) for r in rows]


def get_autocomplete(field, q):
    """オートコンプリート候補を返す"""
    allowed = {"equipment_name", "manufacturer", "location", "facility_name", "category_l", "category_m", "category_s"}
    if field not in allowed:
        return []
    with get_db() as conn:
        rows = conn.execute(
            f"SELECT DISTINCT {field} FROM equipment WHERE deleted = 0 AND {field} LIKE ? ORDER BY {field} LIMIT 20",
            (f"%{q}%",),
        ).fetchall()
    return [r[0] for r in rows if r[0]]


def import_csv_row(row_dict):
    """CSVの1行をインポート (record_idでupsert)"""
    data = {}
    for csv_col, db_col in CSV_COLUMN_MAP.items():
        # BOMつき先頭カラム対応
        val = row_dict.get(csv_col) or row_dict.get("\ufeff" + csv_col)
        data[db_col] = _coerce(db_col, val)

    # equipment_nameが空の場合はスキップ
    if not data.get("equipment_name"):
        return None

    record_id = data.get("record_id")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        if record_id is not None:
            existing = conn.execute(
                "SELECT id FROM equipment WHERE record_id = ?", (record_id,)
            ).fetchone()
        else:
            existing = None

        if existing:
            # UPDATE
            eq_id = existing[0]
            data["updated_at"] = now
            valid_cols = _get_columns()
            update_data = {k: v for k, v in data.items() if k in valid_cols and k not in ("id", "created_at")}
            set_clause = ", ".join(f"{k} = ?" for k in update_data.keys())
            conn.execute(
                f"UPDATE equipment SET {set_clause} WHERE id = ?",
                list(update_data.values()) + [eq_id],
            )
            return eq_id
        else:
            # INSERT
            data["created_at"] = now
            data.setdefault("deleted", 0)
            valid_cols = _get_columns()
            insert_data = {k: v for k, v in data.items() if k in valid_cols and k != "id"}
            cols = ", ".join(insert_data.keys())
            placeholders = ", ".join(["?"] * len(insert_data))
            cur = conn.execute(
                f"INSERT INTO equipment ({cols}) VALUES ({placeholders})",
                list(insert_data.values()),
            )
            return cur.lastrowid


def export_equipment(filters=None):
    """エクスポート用に全一致行を返す"""
    if filters is None:
        filters = {}
    where, params = _build_where(filters)
    with get_db() as conn:
        rows = conn.execute(
            f"SELECT * FROM equipment WHERE {where} ORDER BY id",
            params,
        ).fetchall()
    return [dict(r) for r in rows]


def list_measurements(eq_id):
    """測定履歴一覧"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM measurement WHERE equipment_id = ? ORDER BY measured_at DESC",
            (eq_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def create_measurement(eq_id, data):
    """測定値追加"""
    data = dict(data)
    data["equipment_id"] = eq_id
    data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    with get_db() as conn:
        cur = conn.execute(
            f"INSERT INTO measurement ({cols}) VALUES ({placeholders})",
            list(data.values()),
        )
        return cur.lastrowid


def get_aging_summary():
    """老朽化サマリー (aging_rate計算付き)"""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, equipment_name, facility_name, category_l, category_m,
                      installed_at, service_life, op_status
               FROM equipment
               WHERE deleted = 0 AND installed_at IS NOT NULL AND service_life IS NOT NULL AND service_life > 0
               ORDER BY installed_at ASC"""
        ).fetchall()

    today = date.today()
    result = []
    for r in rows:
        row = dict(r)
        try:
            inst = date.fromisoformat(row["installed_at"])
            elapsed_years = (today - inst).days / 365.25
            aging_rate = (elapsed_years / row["service_life"]) * 100
            remaining_life = row["service_life"] - elapsed_years
        except (ValueError, TypeError):
            elapsed_years = None
            aging_rate = None
            remaining_life = None
        row["elapsed_years"] = round(elapsed_years, 1) if elapsed_years is not None else None
        row["aging_rate"] = round(aging_rate, 1) if aging_rate is not None else None
        row["remaining_life"] = round(remaining_life, 1) if remaining_life is not None else None
        result.append(row)

    result.sort(key=lambda x: x["aging_rate"] or 0, reverse=True)
    return result


def get_dashboard_stats():
    """ダッシュボード統計"""
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM equipment WHERE deleted = 0").fetchone()[0]
        status_rows = conn.execute(
            "SELECT op_status, COUNT(*) as cnt FROM equipment WHERE deleted = 0 GROUP BY op_status"
        ).fetchall()

    status_counts = {}
    for r in status_rows:
        status_counts[r["op_status"] or "不明"] = r["cnt"]

    # 老朽化アラート (aging_rate >= 80)
    aging = get_aging_summary()
    aging_alert_count = sum(1 for a in aging if a["aging_rate"] is not None and a["aging_rate"] >= 80)

    return {
        "total": total,
        "status_counts": status_counts,
        "active": status_counts.get("稼働中", 0),
        "stopped": status_counts.get("停止", 0),
        "removed": status_counts.get("撤去", 0),
        "aging_alert_count": aging_alert_count,
    }


def count_equipment():
    """全機器数（削除含む）"""
    with get_db() as conn:
        return conn.execute("SELECT COUNT(*) FROM equipment").fetchone()[0]


def import_csv_file(path):
    """CSVファイルをインポート。成功数・失敗数・エラー詳細を返す"""
    path = str(path)
    with open(path, "rb") as f:
        raw = f.read()
    detected = chardet.detect(raw)
    encoding = detected.get("encoding") or "utf-8"
    # BOM付きUTF-8対応
    if encoding.lower() in ("utf-8-sig", "utf-8"):
        encoding = "utf-8-sig"

    try:
        text = raw.decode(encoding, errors="replace")
    except (LookupError, UnicodeDecodeError):
        text = raw.decode("utf-8", errors="replace")

    reader = csv.DictReader(io.StringIO(text))
    success = 0
    errors = []
    for i, row in enumerate(reader, start=2):
        try:
            result = import_csv_row(row)
            if result is not None:
                success += 1
        except Exception as e:
            errors.append({"row": i, "error": str(e)})

    return {"success": success, "errors": errors, "error_count": len(errors)}


def _get_columns():
    """equipmentテーブルのカラム名セットを返す"""
    with get_db() as conn:
        info = conn.execute("PRAGMA table_info(equipment)").fetchall()
    return {r["name"] for r in info}
