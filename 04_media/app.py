# -*- coding: utf-8 -*-
from datetime import datetime
import os
import socket
from pathlib import Path

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)
from jinja2 import ChoiceLoader, FileSystemLoader


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm", ".m4v"}


app = Flask(__name__, template_folder="templates")
app.secret_key = os.environ.get("PLANT_MEDIA_SECRET") or os.urandom(24)
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)

app.jinja_loader = ChoiceLoader(
    [
        FileSystemLoader(str(BASE_DIR / "templates")),
        FileSystemLoader(str(BASE_DIR.parent / "common_templates")),
    ]
)

UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


def get_server_ipv4():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def get_client_ip():
    forwarded = request.environ.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0]
    return request.environ.get("REMOTE_ADDR")


def get_displayed_ip():
    return "localhost" if get_client_ip() == "127.0.0.1" else get_server_ipv4()


def sanitize_filename(filename):
    original = Path(filename or "").name
    cleaned = "".join(ch for ch in original if ch not in '<>:"/\\|?*' and ord(ch) >= 32).strip()
    if cleaned in {"", ".", ".."}:
        cleaned = f"media_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    return cleaned


def unique_filename(filename):
    candidate = sanitize_filename(filename)
    path = UPLOAD_FOLDER / candidate
    if not path.exists():
        return candidate

    stem = Path(candidate).stem or "media"
    suffix = Path(candidate).suffix
    counter = 2
    while True:
        numbered = f"{stem}_{counter}{suffix}"
        if not (UPLOAD_FOLDER / numbered).exists():
            return numbered
        counter += 1


def media_kind(filename):
    ext = Path(filename).suffix.lower()
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    return "file"


def list_media_files():
    files = []
    for item in UPLOAD_FOLDER.iterdir():
        if not item.is_file():
            continue
        stat = item.stat()
        files.append(
            {
                "name": item.name,
                "kind": media_kind(item.name),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
            }
        )
    return sorted(files, key=lambda x: (x["kind"] != "image", x["name"].lower()))


def save_uploaded_file(file_storage, source=None):
    if not file_storage or not file_storage.filename:
        raise ValueError("ファイルが指定されていません")

    filename = sanitize_filename(file_storage.filename)
    if source:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{sanitize_filename(source)}_{ts}_{filename}"
    filename = unique_filename(filename)
    file_storage.save(UPLOAD_FOLDER / filename)
    return filename


@app.route("/")
def root():
    return redirect(url_for("media"))


@app.route("/photo")
@app.route("/list")
def legacy_pages():
    return redirect(url_for("media"))


@app.route("/image/<path:filename>")
def legacy_viewer(filename):
    return redirect(url_for("media", q=sanitize_filename(filename)))


@app.route("/media")
def media():
    return render_template("media.html", files=list_media_files(), ip_address=get_displayed_ip())


@app.route("/upload", methods=["POST"])
def upload():
    uploaded = request.files.getlist("image") or request.files.getlist("file")
    if not uploaded:
        return jsonify({"error": "No file provided"}), 400

    saved = []
    errors = []
    for file_storage in uploaded:
        try:
            saved.append(save_uploaded_file(file_storage))
        except Exception as exc:
            errors.append({"filename": file_storage.filename, "error": str(exc)})

    status = 207 if errors and saved else 400 if errors else 200
    return jsonify({"message": "Upload complete", "files": saved, "errors": errors}), status


@app.route("/media/file/<path:filename>")
def send_media(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], sanitize_filename(filename))


@app.route("/download/<path:filename>")
def download_file(filename):
    safe_name = sanitize_filename(filename)
    path = UPLOAD_FOLDER / safe_name
    if path.exists() and path.is_file():
        return send_from_directory(app.config["UPLOAD_FOLDER"], safe_name, as_attachment=True)
    flash(f"File {safe_name} not found.")
    return redirect(url_for("media"))


@app.route("/delete", methods=["POST"])
def delete_photo():
    safe_name = sanitize_filename(request.form.get("photo", ""))
    path = UPLOAD_FOLDER / safe_name
    try:
        if path.exists() and path.is_file():
            path.unlink()
            flash(f"{safe_name} を削除しました。")
        else:
            flash(f"{safe_name} が見つかりません。")
    except PermissionError as exc:
        flash(f"Permission error: {exc}")
    return redirect(url_for("media"))


@app.route("/api/delete", methods=["POST"])
def api_delete():
    """AJAX削除エンドポイント。JSON {"name": filename} を受け取りファイルを削除する。"""
    data = request.get_json(silent=True) or {}
    safe_name = sanitize_filename(data.get("name", ""))
    if not safe_name:
        return jsonify({"ok": False, "error": "ファイル名が指定されていません"}), 400
    path = UPLOAD_FOLDER / safe_name
    if not path.exists() or not path.is_file():
        return jsonify({"ok": False, "error": f"{safe_name} が見つかりません"}), 404
    try:
        path.unlink()
        return jsonify({"ok": True, "name": safe_name})
    except PermissionError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.route("/api/files")
def api_files():
    """ファイル一覧をJSON配列で返す（01_tenken ネットインポート連携用）。"""
    return jsonify([
        {"name": f["name"], "size": f["size"], "modified": f["modified"], "kind": f["kind"]}
        for f in list_media_files()
    ])


@app.route("/api/upload", methods=["POST", "OPTIONS"])
def api_upload():
    """他アプリからのメディア受信エンドポイント（CORS対応）。"""
    if request.method == "OPTIONS":
        resp = app.make_response("")
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    image_file = request.files.get("image") or request.files.get("file")
    if image_file is None:
        resp = jsonify({"error": "image または file フィールドが必要です"})
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp, 400

    try:
        filename = save_uploaded_file(image_file, source=request.form.get("source", "unknown"))
    except Exception as exc:
        resp = jsonify({"error": str(exc)})
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp, 400

    resp = jsonify(
        {
            "message": "Upload successful",
            "filename": filename,
            "memo": request.form.get("memo", ""),
        }
    )
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=5004, use_reloader=False)
