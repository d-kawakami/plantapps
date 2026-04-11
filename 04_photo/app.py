# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, send_from_directory, flash, redirect, url_for
from jinja2 import ChoiceLoader, FileSystemLoader
import os
import socket

app = Flask(
    __name__,
    template_folder='templates'  # templates フォルダが app.py と同じ階層にある場合
)
app.secret_key = os.urandom(24)  # Generate a unique secret key
# テンプレート検索パスを複数設定
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    FileSystemLoader(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'common_templates')))
])

# グローバル変数でクライアントのIPアドレスを保持
client_ip = None

# 画像を保存するディレクトリ
#UPLOAD_FOLDER = 'uploads' # 相対パスで指定する場合
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'uploads')) # 絶対パスで指定する場合
# 追加で参照するメディアディレクトリ

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
# 追加のメディアフォルダも存在確認 (もし存在しない場合は作成するか、エラーハンドリングを考慮)

def get_server_ipv4():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    except Exception as e:
        ip_address = '127.0.0.1'
    finally:
        s.close()
    return ip_address

def get_client_ip():
    x_forwarded_for = request.environ.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.environ.get('REMOTE_ADDR')
    return ip

def get_displayed_ip():
    client_ip = get_client_ip()
    server_ip = get_server_ipv4()

    if client_ip == '127.0.0.1':
        return 'localhost'
    else:
        return server_ip

@app.route('/photo')
def index():
    ip_address = get_displayed_ip()
    # 両方のフォルダからファイルを取得
    photos = []
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        photos.extend(os.listdir(app.config['UPLOAD_FOLDER']))
    # 重複を排除し、ソートするなど、必要に応じてリストを整形してください
    photos = sorted(list(set(photos))) # 重複排除とソート
    return render_template('index.html', ip_address=ip_address, photos=photos)

@app.route('/upload', methods=['POST'])
def upload():
    if 'image' in request.files:
        image_file = request.files['image']
        # 画像を保存する（UPLOAD_FOLDERに保存するように変更なし）
        image_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
        image_file.save(image_path)
        return jsonify({'message': 'Upload successful', 'image_path': image_path})
    else:
        return jsonify({'error': 'No image provided'})

@app.route('/list')
def list_file():
    # 重複を避けるためにセットを使用
    unique_filenames = set()
    
    # 最終的にテンプレートに渡すリスト
    files_to_pass = []
    full_paths_to_pass = [] # これがファイル名表示用のリストになる

    # 各フォルダからファイルを収集
    for folder_path in [
        app.config['UPLOAD_FOLDER'],
    ]:
        if os.path.exists(folder_path):
            for filename in os.listdir(folder_path):
                # ファイルであることを確認し、重複を避ける
                full_item_path = os.path.join(folder_path, filename)
                if os.path.isfile(full_item_path) and filename not in unique_filenames:
                    unique_filenames.add(filename)
                    files_to_pass.append(filename)                   
                    full_paths_to_pass.append(full_item_path) 

    # ファイル名をアルファベット順にソート（必要であれば）
    # ソートする際に、files_to_pass と full_paths_to_pass の対応関係を維持する必要があります。
    # ここでは、タプルのリストとして保持し、ソート後に分解する方法が安全です。
    combined_list = sorted(zip(files_to_pass, full_paths_to_pass))
    files_to_pass = [item[0] for item in combined_list]
    full_paths_to_pass = [item[1] for item in combined_list]

    ip_address = get_displayed_ip()
    return render_template('list.html', files=files_to_pass, full_paths=full_paths_to_pass, ip_address=ip_address)

@app.route('/image/<filename>')
def display_image(filename):
    # 画像と動画を処理するための条件分岐
    if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
        media_type = 'image'
    elif filename.lower().endswith(('.mp4', '.mov', '.avi', '.webm')):
        media_type = 'video'
    else:
        media_type = None
    ip_address = get_displayed_ip()
    return render_template('image.html', filename=filename, media_type=media_type, ip_address=ip_address)

@app.route('/download/<filename>')
def download_file(filename):
    for folder in [app.config['UPLOAD_FOLDER']]:
        if os.path.exists(os.path.join(folder, filename)):
            return send_from_directory(folder, filename, as_attachment=True)
    flash(f'File {filename} not found.')
    return redirect(url_for('list_file'))

@app.route('/media/<filename>') # パス名を変更しました
def send_media(filename): # 関数名も変更しました
    # まずUPLOAD_FOLDER内でファイルを探す
    if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    else:
        # ファイルが見つからない場合のエラーハンドリング
        flash(f'File {filename} not found.')
        return redirect(url_for('list_file')) # または適切なエラーページへリダイレクト

@app.route('/delete', methods=['POST'])
def delete_photo():
    photo = request.form['photo']
    view_type = request.form.get('view_type', 'thumbnails')

    # UPLOAD_FOLDERからの削除のみを許可（または両方から削除するか選択できるようにする）
    photo_path_upload = os.path.join(app.config['UPLOAD_FOLDER'], photo)

    deleted_from = []
    try:
        if os.path.exists(photo_path_upload):
            os.remove(photo_path_upload)
            deleted_from.append('uploads')

        if deleted_from:
            flash(f'Photo {photo} deleted successfully from: {", ".join(deleted_from)}.')
        else:
            flash(f'Photo {photo} does not exist in any managed folders.')
    except PermissionError as e:
        flash(f'Permission error: {str(e)}')
    return redirect(url_for('list_file', view_type=view_type))

@app.route('/api/upload', methods=['POST', 'OPTIONS'])
def api_upload():
    """他アプリ（点検アプリなど）からの写真受信エンドポイント（CORS対応）。
    POST /api/upload  multipart: image=<file>, source=<app名>, memo=<メモ>
    """
    if request.method == 'OPTIONS':
        resp = app.make_response('')
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp

    if 'image' not in request.files:
        resp = jsonify({'error': 'image フィールドが必要です'})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp, 400

    image_file = request.files['image']
    source = request.form.get('source', 'unknown')
    memo   = request.form.get('memo', '')

    # ファイル名にソース情報を付加（例: inspection_20240101_120000_photo.jpg）
    from datetime import datetime as _dt
    import werkzeug.utils as _wu
    ts   = _dt.now().strftime('%Y%m%d_%H%M%S')
    safe = _wu.secure_filename(image_file.filename) or 'photo.jpg'
    fname = f"{source}_{ts}_{safe}"
    save_path = os.path.join(UPLOAD_FOLDER, fname)
    image_file.save(save_path)

    resp = jsonify({'message': 'Upload successful', 'filename': fname, 'memo': memo})
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5004)
