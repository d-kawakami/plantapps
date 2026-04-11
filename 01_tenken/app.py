"""
Flask 日常点検アプリ
起動: python app.py
"""
import io
import json
import os
import shutil
import contextlib
import tempfile
from pathlib import Path
from flask import Flask, render_template, request, jsonify, abort, send_file
from jinja2 import ChoiceLoader, FileSystemLoader
from database import init_db
import models

app = Flask(__name__)

# 共通テンプレートディレクトリを追加（ボトムナビ等の共有コンポーネント）
_common_tpl = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'common_templates'))
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    FileSystemLoader(_common_tpl),
])

# ─── 棟→曜日マップ読み込み ─────────────────────────────────
_DAY_MAP_PATH = Path(__file__).parent / "building_day_map.json"
_DAY_MAP_DEFAULT_PATH = Path(__file__).parent / "building_day_map.default.json"

def _ensure_day_map():
    """building_day_map.json がなければ default.json からコピーして作成する"""
    if not _DAY_MAP_PATH.exists():
        if _DAY_MAP_DEFAULT_PATH.exists():
            shutil.copy(_DAY_MAP_DEFAULT_PATH, _DAY_MAP_PATH)
            print(f"building_day_map.json が見つからないため {_DAY_MAP_DEFAULT_PATH.name} からコピーしました。")
        else:
            raise FileNotFoundError(
                "building_day_map.json も building_day_map.default.json も見つかりません。"
            )

def _load_day_buildings() -> dict:
    """building_day_map.json を読み込み、曜日番号→施設名リストの辞書を返す"""
    _ensure_day_map()
    with open(_DAY_MAP_PATH, encoding="utf-8") as f:
        data = json.load(f)
    day_buildings: dict = {}
    for building, day in data["buildings"].items():
        day_buildings.setdefault(day, []).append(building)
    return day_buildings


# ─── 起動時にDB初期化 ──────────────────────────────────────
with app.app_context():
    init_db()


# ─── ページルート ──────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", day_buildings=_load_day_buildings())


@app.route("/inspect/<int:day>")
def inspect(day: int):
    if day not in range(1, 6):
        abort(404)
    return render_template("inspect.html", day=day)


# ─── REST API ─────────────────────────────────────────────

@app.route("/api/health")
def health():
    """オフライン検知用 死活確認エンドポイント"""
    return jsonify({"status": "ok"})


@app.route("/api/senpatu")
def api_senpatu():
    """
    GET /api/senpatu?day=1
    指定曜日の先発グループ一覧を返す
    """
    day = request.args.get("day", type=int)
    if day is None or day not in range(1, 6):
        return jsonify({"error": "day パラメータが不正です (1〜5)"}), 400
    groups = models.get_senpatu_groups(day)
    return jsonify(groups)


@app.route("/api/items")
def api_items():
    """
    GET /api/items?day=1&week=2
    指定曜日・週番号の点検項目一覧を返す
    """
    day = request.args.get("day", type=int)
    week = request.args.get("week", type=int, default=1)

    if day is None or day not in range(1, 6):
        return jsonify({"error": "day パラメータが不正です (1〜5)"}), 400

    items = models.get_items(day, week)
    return jsonify(items)


@app.route("/api/results")
def api_results():
    """
    GET /api/results?date=YYYY-MM-DD
    指定日の点検結果一覧を返す
    """
    date = request.args.get("date")
    if not date:
        return jsonify({"error": "date パラメータが必要です"}), 400

    results = models.get_results(date)
    return jsonify(results)


@app.route("/api/results", methods=["POST"])
def api_save_result():
    """
    POST /api/results
    Body: {"item_id": int, "inspection_date": "YYYY-MM-DD", "result": "〇", "memo": ""}
    単件保存（UPSERT）
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSONボディが必要です"}), 400

    item_id = data.get("item_id")
    date = data.get("inspection_date")
    result = data.get("result", "")
    memo = data.get("memo", "")

    if not item_id or not date:
        return jsonify({"error": "item_id と inspection_date は必須です"}), 400

    saved = models.upsert_result(item_id, date, result, memo)
    return jsonify(saved), 200


@app.route("/api/results/batch", methods=["POST"])
def api_batch_results():
    """
    POST /api/results/batch
    Body: [{"item_id": int, "inspection_date": "YYYY-MM-DD", "result": "〇", "memo": ""}, ...]
    IndexedDBからのオフライン同期用バッチ保存
    """
    data = request.get_json(silent=True)
    if not isinstance(data, list):
        return jsonify({"error": "配列形式のJSONが必要です"}), 400

    # 必須フィールドバリデーション
    for i, rec in enumerate(data):
        if not rec.get("item_id") or not rec.get("inspection_date"):
            return jsonify({"error": f"records[{i}]: item_id と inspection_date は必須です"}), 400
        rec.setdefault("result", "")
        rec.setdefault("memo", "")

    count = models.batch_upsert_results(data)
    return jsonify({"saved": count}), 200


@app.route("/api/export")
def api_export():
    """
    GET /api/export?date=YYYY-MM-DD
    指定日の点検結果をExcelに書き込んでダウンロードさせる
    """
    date = request.args.get("date")
    if not date:
        return jsonify({"error": "date パラメータが必要です"}), 400

    # DB から結果取得（結果が入力済みのもののみ）
    all_results = models.get_results(date)
    results = [
        {"code": r["code"], "result": r["result"], "memo": r["memo"] or ""}
        for r in all_results if r.get("result")
    ]

    if not results:
        return (
            "<p style='font-family:sans-serif;padding:2rem'>"
            f"{date} の点検結果がありません。<br>"
            "<a href='javascript:history.back()'>← 戻る</a></p>"
        ), 404

    try:
        from export_excel import export_to_excel
        excel_bytes, written, src_name = export_to_excel(results, date)
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Excel生成エラー: {e}"}), 500

    # ダウンロードファイル名（例: 点検結果_2026-02-20.xlsm）
    ext = src_name.rsplit(".", 1)[-1] if "." in src_name else "xlsm"
    dl_name = f"点検結果_{date}.{ext}"
    mimetype = (
        "application/vnd.ms-excel.sheet.macroEnabled.12"
        if ext == "xlsm"
        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    return send_file(
        io.BytesIO(excel_bytes),
        mimetype=mimetype,
        as_attachment=True,
        download_name=dl_name,
    )


@app.route("/api/export/week")
def api_export_week():
    """
    GET /api/export/week?date=YYYY-MM-DD
    指定日を含む週（月〜金）の点検結果をExcelに書き込んでダウンロードさせる
    """
    from datetime import datetime as dt, timedelta

    date = request.args.get("date")
    if not date:
        return jsonify({"error": "date パラメータが必要です"}), 400

    try:
        base = dt.strptime(date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "date の形式が不正です (YYYY-MM-DD)"}), 400

    # 月曜日を起点に月〜金の日付リストを作成
    monday = base - timedelta(days=base.weekday())
    dates = [(monday + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(5)]

    all_results = models.get_results_for_dates(dates)
    results = [
        {"code": r["code"], "result": r["result"], "memo": r["memo"] or ""}
        for r in all_results if r.get("result")
    ]

    if not results:
        friday = monday + timedelta(days=4)
        return (
            "<p style='font-family:sans-serif;padding:2rem'>"
            f"{monday.strftime('%Y-%m-%d')} 〜 {friday.strftime('%Y-%m-%d')} の点検結果がありません。<br>"
            "<a href='javascript:history.back()'>← 戻る</a></p>"
        ), 404

    friday = monday + timedelta(days=4)
    date_label = f"{monday.month}月{monday.day}日〜{friday.month}月{friday.day}日"

    try:
        from export_excel import export_to_excel
        excel_bytes, written, src_name = export_to_excel(
            results, dates[0], date_label=date_label
        )
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"Excel生成エラー: {e}"}), 500

    ext = src_name.rsplit(".", 1)[-1] if "." in src_name else "xlsm"
    dl_name = f"点検結果_{monday.strftime('%Y-%m-%d')}週.{ext}"
    mimetype = (
        "application/vnd.ms-excel.sheet.macroEnabled.12"
        if ext == "xlsm"
        else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    return send_file(
        io.BytesIO(excel_bytes),
        mimetype=mimetype,
        as_attachment=True,
        download_name=dl_name,
    )


@app.route("/api/results/reset", methods=["POST"])
def api_reset_results():
    """
    POST /api/results/reset
    Body: {"date": "YYYY-MM-DD"}
    指定日の全点検結果を削除する
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSONボディが必要です"}), 400

    date = data.get("date")
    if not date:
        return jsonify({"error": "date は必須です"}), 400

    count = models.delete_results_for_date(date)
    return jsonify({"deleted": count}), 200


@app.route("/api/import-excel", methods=["POST"])
def api_import_excel():
    """
    POST /api/import-excel
    multipart/form-data: file=<Excel file>
    点検表Excelを読み込み、inspection_itemsテーブルを更新する
    """
    if "file" not in request.files:
        return jsonify({"error": "ファイルが選択されていません"}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "ファイルが選択されていません"}), 400

    suffix = Path(f.filename).suffix.lower()
    if suffix not in (".xlsx", ".xlsm"):
        return jsonify({"error": "Excel ファイル (.xlsx / .xlsm) を選択してください"}), 400

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            f.save(tmp.name)
            tmp_path = tmp.name

        from import_excel import import_from_excel
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                import_from_excel(tmp_path, no_confirm=True)
        except SystemExit as e:
            output = buf.getvalue()
            return jsonify({"error": output or "インポートに失敗しました"}), 500

        output = buf.getvalue()
        return jsonify({"message": output}), 200

    except Exception as e:
        return jsonify({"error": f"サーバーエラー: {e}"}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
