"""機器台帳管理システム Flask アプリ"""
import csv
import io
import os
from datetime import datetime
from pathlib import Path

import chardet
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
    Response,
)
from jinja2 import ChoiceLoader, FileSystemLoader

from database import init_db
import models

app = Flask(__name__)
app.secret_key = "daicho-secret-2024"

# 共通テンプレートディレクトリを追加
_common_tpl = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'common_templates'))
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    FileSystemLoader(_common_tpl),
])

# DB初期化 & 初期データインポート
with app.app_context():
    init_db()
    if models.count_equipment() == 0:
        csv_path = Path(__file__).parent / "kikilist.csv"
        if csv_path.exists():
            result = models.import_csv_file(str(csv_path))
            print(f"[INFO] kikilist.csv インポート完了: 成功={result['success']}, エラー={result['error_count']}")


# ──────────────────────────────────────────────
# ページルート
# ──────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/equipment")
def equipment_list():
    return render_template("equipment_list.html")


@app.route("/equipment/new")
def equipment_new():
    return render_template("equipment_form.html", mode="new", equipment=None, equipment_id=None)


@app.route("/equipment/<int:eq_id>")
def equipment_detail(eq_id):
    equipment = models.get_equipment(eq_id)
    if equipment is None:
        return render_template("equipment_list.html"), 404
    return render_template("equipment_detail.html", equipment=equipment)


@app.route("/equipment/<int:eq_id>/edit")
def equipment_edit(eq_id):
    equipment = models.get_equipment(eq_id)
    if equipment is None:
        return redirect(url_for("equipment_list"))
    return render_template("equipment_form.html", mode="edit", equipment=equipment, equipment_id=eq_id)


@app.route("/import")
def import_page():
    return render_template("import.html")


# ──────────────────────────────────────────────
# API ルート
# ──────────────────────────────────────────────

def _ok(data):
    return jsonify({"success": True, "data": data})


def _err(msg, status=400):
    return jsonify({"success": False, "error": msg}), status


def _request_filters():
    args = request.args
    return {
        "facility_no": args.get("facility_no", ""),
        "facility_name": args.get("facility_name", ""),
        "work_type": args.get("work_type", ""),
        "category_l": args.get("category_l", ""),
        "category_m": args.get("category_m", ""),
        "category_s": args.get("category_s", ""),
        "q": args.get("q", ""),
        "manufacturer": args.get("manufacturer", ""),
        "op_status": args.get("op_status", ""),
        "installed_from": args.get("installed_from", ""),
        "installed_to": args.get("installed_to", ""),
        "sort": args.get("sort", "id"),
    }


@app.route("/api/equipment", methods=["GET"])
def api_list_equipment():
    filters = _request_filters()
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 50))
    except ValueError:
        page, per_page = 1, 50
    items, total = models.list_equipment(filters, page, per_page)
    return _ok({"items": items, "total": total, "page": page, "per_page": per_page})


@app.route("/api/equipment/<int:eq_id>", methods=["GET"])
def api_get_equipment(eq_id):
    eq = models.get_equipment(eq_id)
    if eq is None:
        return _err("Not found", 404)
    return _ok(eq)


@app.route("/api/equipment", methods=["POST"])
def api_create_equipment():
    data = request.get_json(force=True)
    if not data:
        return _err("No data")
    if not data.get("equipment_name"):
        return _err("equipment_name は必須です")
    data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        new_id = models.create_equipment(data)
        return _ok({"id": new_id}), 201
    except Exception as e:
        return _err(str(e))


@app.route("/api/equipment/<int:eq_id>", methods=["PUT"])
def api_update_equipment(eq_id):
    eq = models.get_equipment(eq_id)
    if eq is None:
        return _err("Not found", 404)
    data = request.get_json(force=True)
    if not data:
        return _err("No data")
    try:
        models.update_equipment(eq_id, data)
        return _ok({"id": eq_id})
    except Exception as e:
        return _err(str(e))


@app.route("/api/equipment/<int:eq_id>", methods=["DELETE"])
def api_delete_equipment(eq_id):
    eq = models.get_equipment(eq_id)
    if eq is None:
        return _err("Not found", 404)
    updated_by = request.args.get("updated_by")
    models.delete_equipment(eq_id, updated_by)
    return _ok({"id": eq_id})


@app.route("/api/equipment/<int:eq_id>/duplicate", methods=["POST"])
def api_duplicate_equipment(eq_id):
    new_id = models.duplicate_equipment(eq_id)
    if new_id is None:
        return _err("Not found", 404)
    return _ok({"id": new_id}), 201


@app.route("/api/equipment/<int:eq_id>/measurements", methods=["GET"])
def api_list_measurements(eq_id):
    items = models.list_measurements(eq_id)
    return _ok(items)


@app.route("/api/equipment/<int:eq_id>/measurements", methods=["POST"])
def api_create_measurement(eq_id):
    eq = models.get_equipment(eq_id)
    if eq is None:
        return _err("Not found", 404)
    data = request.get_json(force=True)
    if not data or not data.get("measured_at"):
        return _err("measured_at は必須です")
    try:
        new_id = models.create_measurement(eq_id, data)
        return _ok({"id": new_id}), 201
    except Exception as e:
        return _err(str(e))


@app.route("/api/facilities", methods=["GET"])
def api_facilities():
    return _ok(models.get_facilities())


@app.route("/api/categories", methods=["GET"])
def api_categories():
    return _ok(models.get_categories())


@app.route("/api/autocomplete", methods=["GET"])
def api_autocomplete():
    field = request.args.get("field", "")
    q = request.args.get("q", "")
    results = models.get_autocomplete(field, q)
    return _ok(results)


@app.route("/api/import/csv", methods=["POST"])
def api_import_csv():
    if "file" not in request.files:
        return _err("ファイルが指定されていません")
    f = request.files["file"]
    if not f.filename:
        return _err("ファイルが指定されていません")
    raw = f.read()
    detected = chardet.detect(raw)
    encoding = detected.get("encoding") or "utf-8"
    if encoding.lower() in ("utf-8-sig", "utf-8"):
        encoding = "utf-8-sig"

    try:
        text = raw.decode(encoding, errors="replace")
    except (LookupError, UnicodeDecodeError):
        text = raw.decode("utf-8", errors="replace")

    reader = csv.DictReader(io.StringIO(text))
    success_count = 0
    error_list = []
    for i, row in enumerate(reader, start=2):
        try:
            result = models.import_csv_row(row)
            if result is not None:
                success_count += 1
        except Exception as e:
            error_list.append({"row": i, "error": str(e)})

    return _ok({
        "success_count": success_count,
        "error_count": len(error_list),
        "errors": error_list,
        "encoding": detected.get("encoding"),
        "confidence": detected.get("confidence"),
    })


@app.route("/api/export/csv", methods=["GET"])
def api_export_csv():
    filters = _request_filters()
    rows = models.export_equipment(filters)

    # DBカラム順 & 日本語ヘッダ
    db_cols = [
        "work_type", "record_id", "customer_code", "facility_no", "facility_name",
        "equipment_id", "equipment_name", "model", "form_no", "completion_docs",
        "maintenance_manual", "instruction_manual", "spare_parts_list", "location",
        "asset_category1", "asset_category2", "asset_category3", "asset_category4",
        "asset_category5", "installed_at", "removed_at", "prev_facility_no",
        "prev_equipment_id", "main_equipment", "category_l", "category_m", "category_s",
        "service_life", "series_no", "unit_no", "notes1", "notes2", "manufacturer",
        "op_status", "maintenance_method", "dept_code", "asset_group", "fixed_asset_no",
        "spec", "multi_measurement", "threshold", "disposal_limit", "legal_inspection",
        "importance", "degradation_flag", "cost_impact", "upgrade_target",
        "high_degradation", "maintenance_form_id", "drainage_class", "deleted",
        "updated_at", "updated_by", "acquisition_cost", "target_life", "replacement_cost",
    ]
    jp_headers = [models.DB_TO_CSV_MAP.get(c, c) for c in db_cols]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(jp_headers)
    for row in rows:
        writer.writerow([row.get(c, "") for c in db_cols])

    csv_bytes = output.getvalue().encode("utf-8-sig")
    return Response(
        csv_bytes,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=equipment_export.csv"},
    )


@app.route("/api/dashboard/stats", methods=["GET"])
def api_dashboard_stats():
    stats = models.get_dashboard_stats()
    aging = models.get_aging_summary()
    # 上位10件
    top_aging = aging[:10]
    return _ok({"stats": stats, "top_aging": top_aging})


@app.route("/api/equipment/search", methods=["GET", "OPTIONS"])
def api_search_equipment():
    """他アプリからの機器名検索（CORS対応）。
    GET /api/equipment/search?name=ポンプA&limit=10
    """
    if request.method == "OPTIONS":
        resp = Response("", status=200)
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    name = request.args.get("name", "").strip()
    limit = min(int(request.args.get("limit", 10)), 50)
    if not name:
        resp = _err("name パラメータが必要です")
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp

    filters = {"q": name}
    items, total = models.list_equipment(filters, page=1, per_page=limit)
    resp = _ok({"items": items, "total": total, "query": name})
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


if __name__ == "__main__":
    app.run(debug=True, port=5002, host="0.0.0.0")
