"""
Flask 日常点検アプリ
起動: python app.py
"""
import io
import json
import os
import shutil
import contextlib
import subprocess
import tempfile
import uuid
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, abort, send_file, Response
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

# ─── 同期設定 ──────────────────────────────────────────────
_SYNC_CONFIG_PATH = Path(__file__).parent / "sync_config.json"
_SYNC_CONFIG_DEFAULT = {
    "server_ip": "192.168.10.1",
    "server_port": 5400,
    "db_path": str(Path.home() / "plantapps/01_tenken/tenken.db"),
}

def _load_sync_config() -> dict:
    if _SYNC_CONFIG_PATH.exists():
        with open(_SYNC_CONFIG_PATH, encoding="utf-8") as f:
            return {**_SYNC_CONFIG_DEFAULT, **json.load(f)}
    return dict(_SYNC_CONFIG_DEFAULT)


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
    """曜日番号→施設名リストの辞書を返す。
    inspection_items にデータがあればそちらを優先（インポート済みの実際の施設名）。
    データがなければ building_day_map.json にフォールバック。"""
    try:
        with models.get_db() as conn:
            rows = conn.execute(
                """SELECT day_of_week, building
                   FROM inspection_items
                   GROUP BY day_of_week, building
                   ORDER BY day_of_week, MIN(sort_order)"""
            ).fetchall()
        if rows:
            day_buildings: dict = {}
            seen: set = set()
            for row in rows:
                key = (row["day_of_week"], row["building"])
                if key not in seen:
                    seen.add(key)
                    day_buildings.setdefault(row["day_of_week"], []).append(row["building"])
            return day_buildings
    except Exception:
        pass
    # フォールバック: building_day_map.json から読み込む
    _ensure_day_map()
    with open(_DAY_MAP_PATH, encoding="utf-8") as f:
        data = json.load(f)
    day_buildings = {}
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

@app.route("/api/sync/config")
def api_sync_config_get():
    return jsonify(_load_sync_config())


@app.route("/api/sync/config", methods=["POST"])
def api_sync_config_save():
    import ipaddress
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSONが必要です"}), 400
    cfg = _load_sync_config()
    if "server_ip" in data:
        raw_ip = str(data["server_ip"]).strip()
        try:
            ip = ipaddress.ip_address(raw_ip)
            if not ip.is_private:
                return jsonify({"error": "server_ip はプライベートIPアドレスのみ指定できます"}), 400
        except ValueError:
            return jsonify({"error": "server_ip が不正なIPアドレスです"}), 400
        cfg["server_ip"] = raw_ip
    if "server_port" in data:
        try:
            port = int(data["server_port"])
            if not (1 <= port <= 65535):
                raise ValueError
            cfg["server_port"] = port
        except (ValueError, TypeError):
            return jsonify({"error": "server_port は1〜65535の整数で指定してください"}), 400
    if "db_path" in data:
        raw_path = str(data["db_path"]).strip()
        allowed_base = Path.home() / "plantapps"
        try:
            resolved = Path(raw_path).resolve()
            resolved.relative_to(allowed_base)
        except ValueError:
            return jsonify({"error": f"db_path は {allowed_base} 内のパスのみ指定できます"}), 400
        cfg["db_path"] = raw_path
    with open(_SYNC_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    return jsonify({"ok": True, "config": cfg})


@app.route("/api/sync/run", methods=["POST"])
def api_sync_run():
    cfg = _load_sync_config()
    server_ip  = cfg["server_ip"]
    server_port = cfg["server_port"]
    db_path    = cfg["db_path"]
    upload_url = f"http://{server_ip}:{server_port}/api/tenken/upload"
    status_url = f"http://{server_ip}:{server_port}/api/tenken/status"

    def generate():
        def log(msg):
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"data: [{ts}] {msg}\n\n"

        yield log("=== DB同期開始 ===")

        r = subprocess.run(["ping", "-c", "1", "-W", "2", server_ip], capture_output=True)
        if r.returncode != 0:
            yield log(f"エラー: {server_ip} に到達できません。Wi-Fi接続を確認してください")
            yield "data: [DONE:error]\n\n"
            return
        yield log(f"サーバ到達確認OK: {server_ip}")

        if not os.path.exists(db_path):
            yield log(f"エラー: DBファイルが見つかりません: {db_path}")
            yield "data: [DONE:error]\n\n"
            return
        size_kb = os.path.getsize(db_path) // 1024
        yield log(f"DBファイル確認OK: {db_path} ({size_kb}KB)")

        yield log("サーバ側DB状態を確認中...")
        r = subprocess.run(
            ["curl", "-s", "--connect-timeout", "5", status_url],
            capture_output=True, text=True
        )
        if r.stdout.strip():
            yield log(f"サーバ状態: {r.stdout.strip()}")
        else:
            yield log("警告: サーバ状態の取得に失敗しました（続行します）")

        yield log(f"DBをアップロード中: {upload_url}")
        r = subprocess.run(
            ["curl", "-s", "-o", "/tmp/tenken_sync_resp.txt",
             "-w", "%{http_code}", "--connect-timeout", "10",
             "-F", f"db=@{db_path}", upload_url],
            capture_output=True, text=True
        )
        http_code = r.stdout.strip()
        try:
            resp_body = Path("/tmp/tenken_sync_resp.txt").read_text()
        except Exception:
            resp_body = ""

        if http_code == "200":
            yield log(f"同期成功: {resp_body.strip()}")
            yield log("=== DB同期完了 ===")
            yield "data: [DONE:ok]\n\n"
        else:
            yield log(f"エラー: HTTPコード={http_code} レスポンス={resp_body.strip()}")
            yield "data: [DONE:error]\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"})


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


_BUILDING_MAP_PATH = Path(__file__).parent / "building_day_map.json"
_pending_scans: dict = {}  # {scan_id: tmp_path}


@app.route("/api/building-day-map", methods=["GET"])
def api_get_building_day_map():
    if not _BUILDING_MAP_PATH.exists():
        return jsonify({"buildings": {}}), 200
    with open(_BUILDING_MAP_PATH, encoding="utf-8") as f:
        return jsonify(json.load(f)), 200


@app.route("/api/building-day-map", methods=["POST"])
def api_save_building_day_map():
    data = request.get_json(silent=True) or {}
    new_buildings = data.get("buildings")
    if not isinstance(new_buildings, dict):
        return jsonify({"error": "buildings が不正です"}), 400

    existing = {}
    if _BUILDING_MAP_PATH.exists():
        with open(_BUILDING_MAP_PATH, encoding="utf-8") as f:
            existing = json.load(f)
    existing.setdefault("buildings", {}).update(new_buildings)

    with open(_BUILDING_MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    from import_excel import reload_building_map
    reload_building_map()
    return jsonify({"ok": True}), 200


def _download_excel(file_url: str):
    """URLからExcelをダウンロードして一時ファイルパスを返す。失敗時は例外。"""
    parsed = urllib.parse.urlsplit(file_url)
    encoded_url = urllib.parse.urlunsplit((
        parsed.scheme, parsed.netloc,
        urllib.parse.quote(parsed.path, safe="/"),
        parsed.query, parsed.fragment,
    ))
    req = urllib.request.Request(encoded_url, headers={"User-Agent": "plantapps-tenken/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    if not data:
        raise ValueError("ダウンロードしたファイルが空です。")
    suffix = Path(urllib.parse.urlsplit(file_url).path).suffix.lower()
    if suffix not in (".xlsx", ".xlsm"):
        suffix = ".xlsx"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        return tmp.name


@app.route("/api/net-import/scan", methods=["POST"])
def api_net_import_scan():
    """URLからExcelをDLし建物名と現在の曜日設定を返す（DBには書かない）"""
    data = request.get_json(silent=True) or {}
    file_url = data.get("file_url", "").strip()
    if not file_url:
        return jsonify({"error": "file_url が指定されていません"}), 400

    try:
        tmp_path = _download_excel(file_url)
    except urllib.error.URLError as e:
        return jsonify({"error": f"ダウンロードエラー: {e.reason}"}), 502
    except Exception as e:
        return jsonify({"error": f"ダウンロードに失敗しました: {e}"}), 502

    from import_excel import scan_building_names, get_day_of_week, reload_building_map
    reload_building_map()  # マップを最新状態に更新してからスキャン
    names = scan_building_names(tmp_path)

    scan_id = str(uuid.uuid4())
    _pending_scans[scan_id] = tmp_path

    def _day_or_none(name):
        d = get_day_of_week(name)
        return d if d >= 0 else None

    buildings = [{"name": n, "day": _day_or_none(n)} for n in names]
    has_unknown = any(b["day"] is None for b in buildings)
    return jsonify({"ok": True, "scan_id": scan_id, "buildings": buildings, "has_unknown": has_unknown})


@app.route("/api/net-import/commit", methods=["POST"])
def api_net_import_commit():
    """スキャン済みExcelをインポート。building_days が渡されたら先にマップを更新する。"""
    data = request.get_json(silent=True) or {}
    scan_id = data.get("scan_id", "").strip()
    building_days = data.get("building_days")  # {name: day} or None

    tmp_path = _pending_scans.pop(scan_id, None)
    if not tmp_path or not os.path.exists(tmp_path):
        return jsonify({"error": "セッションが無効です。もう一度ネットから取得してください。"}), 400

    try:
        if isinstance(building_days, dict) and building_days:
            existing = {}
            if _BUILDING_MAP_PATH.exists():
                with open(_BUILDING_MAP_PATH, encoding="utf-8") as f:
                    existing = json.load(f)
            existing.setdefault("buildings", {}).update(
                {k: int(v) for k, v in building_days.items() if v is not None}
            )
            with open(_BUILDING_MAP_PATH, "w", encoding="utf-8") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
            from import_excel import reload_building_map
            reload_building_map()

        from import_excel import import_from_excel
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                import_from_excel(tmp_path, no_confirm=True)
        except SystemExit:
            output = buf.getvalue()
            return jsonify({"error": output or "インポートに失敗しました"}), 500

        return jsonify({"message": buf.getvalue()}), 200

    except Exception as e:
        return jsonify({"error": f"サーバーエラー: {e}"}), 500
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.route("/api/net_xlsx/list")
def api_net_xlsx_list():
    list_url = request.args.get("url", "").strip()
    if not list_url:
        return jsonify({"error": "url パラメータが必要です。"}), 400
    try:
        req = urllib.request.Request(
            list_url,
            headers={"Accept": "application/json", "User-Agent": "plantapps-tenken/1.0"},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read().decode("utf-8")
        data = json.loads(raw)
        if not isinstance(data, list):
            return jsonify({"error": "サーバーが配列を返しませんでした。"}), 502
        return jsonify({"ok": True, "files": data})
    except urllib.error.URLError as e:
        return jsonify({"error": f"接続エラー: {e.reason}"}), 502
    except json.JSONDecodeError:
        return jsonify({"error": "レスポンスがJSONではありませんでした。"}), 502
    except Exception as e:
        return jsonify({"error": str(e)}), 502


@app.route("/api/import-excel-from-net", methods=["POST"])
def api_import_excel_from_net():
    data = request.get_json(silent=True) or {}
    file_url = data.get("file_url", "").strip()
    if not file_url:
        return jsonify({"error": "file_url が指定されていません"}), 400

    parsed = urllib.parse.urlsplit(file_url)
    encoded_url = urllib.parse.urlunsplit((
        parsed.scheme, parsed.netloc,
        urllib.parse.quote(parsed.path, safe="/"),
        parsed.query, parsed.fragment,
    ))

    tmp_path = None
    try:
        req = urllib.request.Request(
            encoded_url,
            headers={"User-Agent": "plantapps-tenken/1.0"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            file_data = resp.read()
    except urllib.error.URLError as e:
        return jsonify({"error": f"ダウンロードエラー: {e.reason}"}), 502
    except Exception as e:
        return jsonify({"error": f"ダウンロードに失敗しました: {e}"}), 502

    if not file_data:
        return jsonify({"error": "ダウンロードしたファイルが空です。"}), 502

    suffix = Path(urllib.parse.urlsplit(file_url).path).suffix.lower()
    if suffix not in (".xlsx", ".xlsm"):
        suffix = ".xlsx"

    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file_data)
            tmp_path = tmp.name

        from import_excel import import_from_excel
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                import_from_excel(tmp_path, no_confirm=True)
        except SystemExit:
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
