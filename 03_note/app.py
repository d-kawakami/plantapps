import os
import sqlite3
import openpyxl
import json
import hashlib
import subprocess
import tempfile
import urllib.request
import urllib.error
import urllib.parse
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from jinja2 import ChoiceLoader, FileSystemLoader
from datetime import datetime
from markupsafe import Markup, escape as html_escape

app = Flask(__name__)
app.secret_key = 'note2_secret_key'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 共通テンプレートディレクトリを追加
_common_tpl = os.path.abspath(os.path.join(BASE_DIR, '..', 'common_templates'))
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(BASE_DIR, 'templates')),
    FileSystemLoader(_common_tpl),
])
DB_PATH = os.path.join(BASE_DIR, 'note.db')
# 同ディレクトリの note.xlsx → なければ親ディレクトリの 引継ぎノート電子版.xlsx を探す
XLSX_PATH = os.path.join(BASE_DIR, 'note.xlsx')
if not os.path.exists(XLSX_PATH):
    XLSX_PATH = os.path.join(BASE_DIR, '..', '引継ぎノート電子版.xlsx')
MEDIA_DIR = os.path.join(BASE_DIR, 'media')
PER_PAGE = 50
MAX_SCORE_ROWS = 3000  # 関連度計算の対象上限（メモリ節約）

# VOICEVOX 設定
# スピーカーID一覧（主要なもの）:
#   1=四国めたん(ノーマル)  3=ずんだもん(ノーマル)  8=春日部つむぎ
#  13=青山龍星             14=冥鳴ひまり            16=九州そら(ノーマル)
# .env の VOICEVOX_SPEAKER で変更可能
def _load_env_key(key: str) -> str:
    """環境変数または .env ファイルから値を取得する。"""
    val = os.environ.get(key)
    if val:
        return val
    for env_path in [
        os.path.join(BASE_DIR, '.env'),
        os.path.join(BASE_DIR, '..', '05_tenken', '.env'),
    ]:
        if os.path.exists(env_path):
            with open(env_path, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f'{key}='):
                        return line[len(key) + 1:].strip()
    return ''


VOICEVOX_URL     = _load_env_key('VOICEVOX_URL') or 'http://localhost:50021'
VOICEVOX_SPEAKER = int(_load_env_key('VOICEVOX_SPEAKER') or '13')  # デフォルト: 青山龍星（落ち着いた男性）

YOUBI = ['月', '火', '水', '木', '金', '土', '日']

# ============================================================
# 同義語辞書（施設管理・設備保守ドメイン向け）
# 運用に合わせてグループを追加・編集してください
# ============================================================
SYNONYM_GROUPS = [
    ['故障', 'トラブル', '不具合', '障害', '異常'],
    ['エラー', 'アラーム', '警報', 'アラート'],
    ['停電', '電源断', '復電', '停電復旧', '停電発生'],
    ['漏水', '水漏れ', '漏れ'],
    ['修理', '修繕', '補修', '修復'],
    ['点検', 'チェック', '巡視', '巡回', '検査'],
    ['交換', '取替', '取替え', '取換'],
    ['清掃', '清拭', '掃除', '洗浄'],
    ['復旧', '回復', '復帰', '正常復帰'],
    ['再起動', 'リスタート', 'リセット'],
]

_SYNONYM_MAP: dict = {}
for _grp in SYNONYM_GROUPS:
    for _t in _grp:
        _SYNONYM_MAP[_t] = _grp[:]


def expand_term(term: str) -> list:
    """単語を同義語グループに展開する。未登録語はそのまま返す。"""
    return _SYNONYM_MAP.get(term, [term])


def highlight_text(text, terms):
    """テキスト中の検索語をハイライト表示する（XSS対策済み）。"""
    if not text or not terms:
        return html_escape(text) if text else Markup('')
    result = str(html_escape(text))
    for term in terms:
        safe_term = str(html_escape(term))
        if safe_term:
            result = result.replace(safe_term, f'<mark>{safe_term}</mark>')
    return Markup(result)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            kinmu TEXT,
            shubetsu TEXT,
            jikoku TEXT,
            naiyou TEXT,
            kinyugsha TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ""
        )
    ''')
    conn.commit()

    # 既存DBへのカラム追加（マイグレーション）
    cols = [row[1] for row in conn.execute('PRAGMA table_info(notes)').fetchall()]
    if 'kinyugsha' not in cols:
        conn.execute('ALTER TABLE notes ADD COLUMN kinyugsha TEXT DEFAULT ""')
        conn.commit()

    count = conn.execute('SELECT COUNT(*) FROM notes').fetchone()[0]
    if count == 0:
        import_xlsx(conn)
    conn.close()


# デフォルト設定値
SETTINGS_DEFAULTS = {
    'tts_engine':        'voicevox',   # voicevox / windows_sapi / termux
    'voicevox_speaker':  str(VOICEVOX_SPEAKER),
    'read_date':      '1',
    'read_youbi':     '1',
    'read_kinmu':     '1',
    'read_shubetsu':  '1',
    'read_jikoku':    '1',
    'read_naiyou':    '1',
    'read_labels':    '1',
}


def get_setting(key: str) -> str:
    conn = get_db()
    row = conn.execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
    conn.close()
    if row:
        return row['value']
    return SETTINGS_DEFAULTS.get(key, '')


def get_all_settings() -> dict:
    conn = get_db()
    rows = conn.execute('SELECT key, value FROM settings').fetchall()
    conn.close()
    result = dict(SETTINGS_DEFAULTS)
    for r in rows:
        result[r['key']] = r['value']
    return result


def save_setting(key: str, value: str) -> None:
    conn = get_db()
    conn.execute(
        'INSERT INTO settings (key, value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',
        (key, value)
    )
    conn.commit()
    conn.close()


def import_xlsx(conn, xlsx_source=None):
    """
    Excel 列マッピング（3行目以降がデータ）:
      A列[0] = 記入年月日（日付）
      B列[1] = 曜日（数式、スキップ）
      C列[2] = 勤務
      D列[3] = 種別
      E列[4] = 時刻
      F列[5] = 内容
      G列[6] = 記入者（省略可）
    """
    try:
        existing = set(
            (r['date'], r['kinmu'], r['jikoku'], r['naiyou'])
            for r in conn.execute('SELECT date, kinmu, jikoku, naiyou FROM notes').fetchall()
        )

        wb = openpyxl.load_workbook(xlsx_source or XLSX_PATH, data_only=True)
        ws = wb.active
        rows_to_insert = []
        for row in ws.iter_rows(min_row=3, values_only=True):
            # A列（日付）が空の行はスキップ
            if not row[0]:
                continue
            date_val = row[0]                                    # A列 = 日付
            if isinstance(date_val, datetime):
                date_str = date_val.strftime('%Y-%m-%d')
            else:
                date_str = str(date_val).strip()
            kinmu     = str(row[2]).strip() if row[2] else ''   # C列 = 勤務
            shubetsu  = str(row[3]).strip() if row[3] else ''   # D列 = 種別
            jikoku    = str(row[4]).strip() if row[4] else ''   # E列 = 時刻
            naiyou    = str(row[5]).strip() if row[5] else ''   # F列 = 内容
            kinyugsha = str(row[6]).strip() if len(row) > 6 and row[6] else ''  # G列 = 記入者
            if (date_str, kinmu, jikoku, naiyou) not in existing:
                rows_to_insert.append((date_str, kinmu, shubetsu, jikoku, naiyou, kinyugsha))

        conn.executemany(
            'INSERT INTO notes (date, kinmu, shubetsu, jikoku, naiyou, kinyugsha) VALUES (?,?,?,?,?,?)',
            rows_to_insert
        )
        conn.commit()
        print(f'Imported {len(rows_to_insert)} new rows from xlsx.')
        return len(rows_to_insert)
    except Exception as e:
        print(f'Import error: {e}')
        return 0


def youbi_from_date(date_str):
    try:
        d = datetime.strptime(date_str, '%Y-%m-%d')
        return YOUBI[d.weekday()]
    except Exception:
        return ''


# ============================================================
# VOICEVOX TTS
# ============================================================

def build_speak_text(row, cfg: dict) -> str:
    """引継ぎ1件分を読み上げ用日本語テキストに変換する。
    cfg: get_all_settings() の戻り値
    """
    parts = []
    labels = cfg.get('read_labels', '1') == '1'

    # 日付
    date_str = row['date'] or ''
    youbi = youbi_from_date(date_str)
    read_date   = cfg.get('read_date',   '1') == '1'
    read_youbi  = cfg.get('read_youbi',  '1') == '1'
    try:
        d = datetime.strptime(date_str, '%Y-%m-%d')
        date_parts = []
        if read_date:
            date_parts.append(f'{d.year}年{d.month}月{d.day}日')
        if read_youbi and youbi:
            date_parts.append(f'{youbi}曜日')
        if date_parts:
            parts.append('、'.join(date_parts) + '。')
    except Exception:
        if read_date and date_str:
            parts.append(f'{date_str}。')

    # 勤務
    if cfg.get('read_kinmu', '1') == '1':
        kinmu = (row['kinmu'] or '').strip()
        if kinmu:
            label = '勤務、' if labels else ''
            parts.append(f'{label}{kinmu}。')

    # 種別
    if cfg.get('read_shubetsu', '1') == '1':
        shubetsu = (row['shubetsu'] or '').strip()
        if shubetsu:
            label = '種別、' if labels else ''
            parts.append(f'{label}{shubetsu}。')

    # 時刻
    if cfg.get('read_jikoku', '1') == '1':
        jikoku = (row['jikoku'] or '').strip()
        if jikoku:
            label = '時刻、' if labels else ''
            parts.append(f'{label}{jikoku}。')

    # 内容
    if cfg.get('read_naiyou', '1') == '1':
        naiyou = (row['naiyou'] or '').strip()
        if naiyou:
            label = '内容。' if labels else ''
            parts.append(f'{label}{naiyou}')

    return ''.join(parts)


def generate_voicevox_audio(text: str, out_path: str, speaker_id: int = None) -> None:
    """VOICEVOX ローカル API を呼び出して WAV を out_path に書き込む。"""
    if speaker_id is None:
        speaker_id = VOICEVOX_SPEAKER

    # Step1: audio_query
    encoded_text = urllib.parse.quote(text)
    query_url = f'{VOICEVOX_URL}/audio_query?text={encoded_text}&speaker={speaker_id}'
    try:
        req1 = urllib.request.Request(query_url, method='POST')
        with urllib.request.urlopen(req1, timeout=10) as resp:
            query_json = resp.read()
    except OSError:
        raise RuntimeError(
            f'VOICEVOX に接続できません ({VOICEVOX_URL})。'
            'VOICEVOXアプリを起動してから再試行してください。'
        )

    # Step2: synthesis
    synth_url = f'{VOICEVOX_URL}/synthesis?speaker={speaker_id}'
    req2 = urllib.request.Request(
        synth_url,
        data=query_json,
        headers={'Content-Type': 'application/json', 'Accept': 'audio/wav'},
        method='POST',
    )
    with urllib.request.urlopen(req2, timeout=30) as resp:
        audio_data = resp.read()

    os.makedirs(MEDIA_DIR, exist_ok=True)
    with open(out_path, 'wb') as f:
        f.write(audio_data)


def generate_windows_sapi_audio(text: str, out_path: str) -> None:
    """Windows 組み込み SAPI (PowerShell/System.Speech 経由) で WAV を生成する。
    PowerShell は Windows 標準搭載のため追加インストール不要。
    """
    os.makedirs(MEDIA_DIR, exist_ok=True)

    # テキストをテンポラリファイルに書き込む（PowerShell への文字列インジェクション防止）
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.txt', delete=False, encoding='utf-8'
    ) as tf:
        tf.write(text)
        txt_path = tf.name

    try:
        safe_out = out_path.replace("'", "''")
        safe_txt = txt_path.replace("'", "''")
        script = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$s.SetOutputToWaveFile('{safe_out}'); "
            f"$text = [System.IO.File]::ReadAllText('{safe_txt}', [System.Text.Encoding]::UTF8); "
            "$s.Speak($text); "
            "$s.Dispose()"
        )
        result = subprocess.run(
            ['powershell', '-NoProfile', '-NonInteractive', '-Command', script],
            capture_output=True,
            timeout=60,
        )
        if result.returncode != 0:
            err = result.stderr.decode('utf-8', errors='replace').strip()
            raise RuntimeError(f'Windows SAPI エラー: {err}')
        if not os.path.exists(out_path):
            raise RuntimeError('Windows SAPI: 音声ファイルが生成されませんでした。')
    finally:
        try:
            os.unlink(txt_path)
        except OSError:
            pass


def generate_termux_audio(text: str) -> None:
    """Android (Termux) の termux-tts-speak でデバイスのスピーカーから直接再生する。
    termux-api パッケージが必要: pkg install termux-api
    """
    result = subprocess.run(
        ['termux-tts-speak', text],
        capture_output=True,
        timeout=120,
    )
    if result.returncode != 0:
        err = result.stderr.decode('utf-8', errors='replace').strip()
        raise RuntimeError(f'termux-tts-speak エラー: {err}')


def fetch_voicevox_speakers() -> list:
    """VOICEVOX から利用可能なスピーカー一覧を取得する。
    戻り値: [{'id': int, 'label': 'キャラ名 - スタイル名'}, ...]
    """
    try:
        req = urllib.request.Request(f'{VOICEVOX_URL}/speakers')
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        result = []
        for chara in data:
            name = chara.get('name', '')
            for style in chara.get('styles', []):
                sid   = style.get('id')
                sname = style.get('name', '')
                label = f'{name}（{sname}）' if sname else name
                result.append({'id': sid, 'label': label})
        return result
    except Exception:
        return []


@app.route('/')
def index():
    conn = get_db()

    q = request.args.get('q', '').strip()
    kinmu_filter = request.args.get('kinmu', '').strip()
    shubetsu_filter = request.args.get('shubetsu', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    page = int(request.args.get('page', 1))

    conditions = []
    params = []

    # 同義語展開と関連度ソート用
    expanded_terms_map = {}   # {元の語: [展開後リスト]}
    all_search_terms = []     # ハイライト用フラットリスト
    use_relevance_sort = False

    SEARCH_FIELDS = ('naiyou', 'jikoku', 'shubetsu')

    if q:
        use_relevance_sort = True
        for raw_term in q.split():
            synonyms = expand_term(raw_term)
            expanded_terms_map[raw_term] = synonyms
            all_search_terms.extend(synonyms)
            # 同一語グループ内はOR、異なる語グループ間はAND
            syn_or_parts = []
            for syn in synonyms:
                field_or = ' OR '.join(f'{f} LIKE ?' for f in SEARCH_FIELDS)
                syn_or_parts.append(f'({field_or})')
                params.extend(f'%{syn}%' for _ in SEARCH_FIELDS)
            conditions.append(f'({" OR ".join(syn_or_parts)})')

    if kinmu_filter:
        conditions.append('kinmu = ?')
        params.append(kinmu_filter)
    if shubetsu_filter:
        conditions.append('shubetsu = ?')
        params.append(shubetsu_filter)
    if date_from:
        conditions.append('date >= ?')
        params.append(date_from)
    if date_to:
        conditions.append('date <= ?')
        params.append(date_to)

    where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''

    if use_relevance_sort:
        # 関連度スコアでソート：全マッチ行を取得してPythonでランキング
        all_rows = conn.execute(
            f'SELECT * FROM notes {where} ORDER BY date DESC, id DESC LIMIT {MAX_SCORE_ROWS}',
            params
        ).fetchall()
        total = conn.execute(f'SELECT COUNT(*) FROM notes {where}', params).fetchone()[0]

        raw_terms_set = set(q.split())

        def score_row(row):
            text = ' '.join(filter(None, [row['naiyou'] or '', row['jikoku'] or '', row['shubetsu'] or '']))
            s = 0
            for t in all_search_terms:
                cnt = text.count(t)
                if cnt:
                    s += cnt * (3 if t in raw_terms_set else 1)
            return s

        ranked = sorted(all_rows, key=score_row, reverse=True)
        offset = (page - 1) * PER_PAGE
        rows = ranked[offset:offset + PER_PAGE]
    else:
        total = conn.execute(f'SELECT COUNT(*) FROM notes {where}', params).fetchone()[0]
        offset = (page - 1) * PER_PAGE
        rows = conn.execute(
            f'SELECT * FROM notes {where} ORDER BY date, id LIMIT ? OFFSET ?',
            params + [PER_PAGE, offset]
        ).fetchall()

    kinmu_list = [r[0] for r in conn.execute('SELECT DISTINCT kinmu FROM notes WHERE kinmu != "" ORDER BY kinmu').fetchall()]
    shubetsu_list = [r[0] for r in conn.execute('SELECT DISTINCT shubetsu FROM notes WHERE shubetsu != "" ORDER BY shubetsu').fetchall()]
    conn.close()

    total_pages = (total + PER_PAGE - 1) // PER_PAGE

    def row_class(row):
        classes = []
        if row['kinmu'] == '夜勤':
            classes.append('yakin')
        if '故障' in (row['shubetsu'] or ''):
            classes.append('kosho')
        return ' '.join(classes)

    return render_template(
        'index.html',
        rows=rows,
        page=page,
        total_pages=total_pages,
        total=total,
        q=q,
        kinmu_filter=kinmu_filter,
        shubetsu_filter=shubetsu_filter,
        date_from=date_from,
        date_to=date_to,
        kinmu_list=kinmu_list,
        shubetsu_list=shubetsu_list,
        youbi_from_date=youbi_from_date,
        row_class=row_class,
        highlight_text=highlight_text,
        all_search_terms=all_search_terms,
        expanded_terms_map=expanded_terms_map,
        use_relevance_sort=use_relevance_sort,
    )


@app.route('/new', methods=['GET', 'POST'])
def new():
    if request.method == 'POST':
        date = request.form.get('date', '').strip()
        kinmu = request.form.get('kinmu', '').strip()
        shubetsu = request.form.get('shubetsu', '').strip()
        jikoku = request.form.get('jikoku', '').strip()
        naiyou = request.form.get('naiyou', '').strip()
        kinyugsha = request.form.get('kinyugsha', '').strip()
        if not date:
            flash('日付は必須です。', 'error')
            return render_template('form.html', action='new', record=request.form,
                                   kinmu_options=['日勤', '夜勤'],
                                   shubetsu_options=['報告', '故障', '処置', '故障処置'],
                                   rec_date=date, rec_kinmu=kinmu, rec_shubetsu=shubetsu,
                                   rec_jikoku=jikoku, rec_naiyou=naiyou, rec_kinyugsha=kinyugsha)
        conn = get_db()
        conn.execute(
            'INSERT INTO notes (date, kinmu, shubetsu, jikoku, naiyou, kinyugsha) VALUES (?,?,?,?,?,?)',
            (date, kinmu, shubetsu, jikoku, naiyou, kinyugsha)
        )
        conn.commit()
        conn.close()
        flash('登録しました。', 'success')
        return redirect(url_for('index'))
    return render_template('form.html', action='new', record={},
                           kinmu_options=['日勤', '夜勤'],
                           shubetsu_options=['報告', '故障', '処置', '故障処置'],
                           rec_date='', rec_kinmu='', rec_shubetsu='', rec_jikoku='', rec_naiyou='', rec_kinyugsha='')


@app.route('/edit/<int:rid>', methods=['GET', 'POST'])
def edit(rid):
    conn = get_db()
    record = conn.execute('SELECT * FROM notes WHERE id=?', (rid,)).fetchone()
    if not record:
        conn.close()
        flash('レコードが見つかりません。', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        date = request.form.get('date', '').strip()
        kinmu = request.form.get('kinmu', '').strip()
        shubetsu = request.form.get('shubetsu', '').strip()
        jikoku = request.form.get('jikoku', '').strip()
        naiyou = request.form.get('naiyou', '').strip()
        kinyugsha = request.form.get('kinyugsha', '').strip()
        if not date:
            flash('日付は必須です。', 'error')
            conn.close()
            return render_template('form.html', action='edit', record=request.form, rid=rid,
                                   kinmu_options=['日勤', '夜勤'],
                                   shubetsu_options=['報告', '故障', '処置', '故障処置'],
                                   rec_date=date, rec_kinmu=kinmu, rec_shubetsu=shubetsu,
                                   rec_jikoku=jikoku, rec_naiyou=naiyou, rec_kinyugsha=kinyugsha)
        conn.execute(
            'UPDATE notes SET date=?, kinmu=?, shubetsu=?, jikoku=?, naiyou=?, kinyugsha=? WHERE id=?',
            (date, kinmu, shubetsu, jikoku, naiyou, kinyugsha, rid)
        )
        conn.commit()
        conn.close()
        flash('更新しました。', 'success')
        return redirect(url_for('index'))

    conn.close()
    return render_template('form.html', action='edit', record=record, rid=rid,
                           kinmu_options=['日勤', '夜勤'],
                           shubetsu_options=['報告', '故障', '処置', '故障処置'],
                           rec_date=record['date'], rec_kinmu=record['kinmu'],
                           rec_shubetsu=record['shubetsu'], rec_jikoku=record['jikoku'],
                           rec_naiyou=record['naiyou'], rec_kinyugsha=record['kinyugsha'] or '')


@app.route('/delete/<int:rid>', methods=['POST'])
def delete(rid):
    conn = get_db()
    conn.execute('DELETE FROM notes WHERE id=?', (rid,))
    conn.commit()
    conn.close()
    flash('削除しました。', 'success')
    return redirect(url_for('index'))


@app.route('/import_xlsx', methods=['POST'])
def import_xlsx_route():
    f = request.files.get('xlsx_file')
    if not f or not f.filename:
        flash('ファイルを選択してください。', 'error')
        return redirect(url_for('index'))
    if not f.filename.lower().endswith('.xlsx'):
        flash('.xlsx ファイルを選択してください。', 'error')
        return redirect(url_for('index'))
    conn = get_db()
    added = import_xlsx(conn, f)
    conn.close()
    if added:
        flash(f'{added} 件の新規レコードをインポートしました。', 'success')
    else:
        flash('新規レコードはありませんでした。', 'success')
    return redirect(url_for('index'))


@app.route('/speak/<int:rid>', methods=['POST'])
def speak(rid):
    """指定 ID の引継ぎレコードを TTS で読み上げ、音声 URL を返す。
    tts_engine 設定により動作が変わる:
      voicevox     → VOICEVOX で WAV 生成 → ブラウザ再生
      windows_sapi → Windows SAPI で WAV 生成 → ブラウザ再生
      termux       → termux-tts-speak でデバイス直接再生 → {'played': true}
    """
    conn = get_db()
    row = conn.execute('SELECT * FROM notes WHERE id=?', (rid,)).fetchone()
    conn.close()

    if not row:
        return jsonify({'error': 'レコードが見つかりません。'}), 404

    cfg = get_all_settings()
    speak_text = build_speak_text(row, cfg)
    if not speak_text.strip():
        return jsonify({'error': '読み上げ対象のフィールドがすべてオフになっています。設定を確認してください。'}), 400

    tts_engine = cfg.get('tts_engine', 'voicevox')

    # ---- Termux (Android デバイス直接再生) ----
    if tts_engine == 'termux':
        try:
            generate_termux_audio(speak_text)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        return jsonify({'played': True, 'text': speak_text})

    # ---- WAV ファイルを生成してブラウザで再生 ----
    speaker_id = cfg.get('voicevox_speaker', str(VOICEVOX_SPEAKER))
    if tts_engine == 'windows_sapi':
        cache_key = f'{speak_text}_windows_sapi'
    else:
        cache_key = f'{speak_text}_voicevox_{speaker_id}'

    content_hash = hashlib.md5(cache_key.encode('utf-8')).hexdigest()[:8]
    filename = f'note_{rid}_{content_hash}.wav'
    out_path = os.path.join(MEDIA_DIR, filename)

    if not os.path.exists(out_path):
        try:
            if tts_engine == 'windows_sapi':
                generate_windows_sapi_audio(speak_text, out_path)
            else:
                generate_voicevox_audio(
                    speak_text, out_path,
                    speaker_id=int(speaker_id),
                )
        except urllib.error.HTTPError as e:
            body = e.read().decode('utf-8', errors='replace')
            return jsonify({'error': f'VOICEVOX API エラー ({e.code}): {body}'}), 502
        except Exception as e:
            return jsonify({'error': f'音声生成エラー: {str(e)}'}), 500

    audio_url = url_for('serve_media', filename=filename)
    return jsonify({'url': audio_url, 'text': speak_text})


@app.route('/media/<path:filename>')
def serve_media(filename):
    """media/ フォルダの音声ファイルを配信する。"""
    return send_from_directory(MEDIA_DIR, filename)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        # TTS エンジン
        tts_engine = request.form.get('tts_engine', 'voicevox')
        if tts_engine in ('voicevox', 'windows_sapi', 'termux'):
            save_setting('tts_engine', tts_engine)
        # VOICEVOX スピーカー
        speaker = request.form.get('voicevox_speaker', '').strip()
        if speaker.isdigit():
            save_setting('voicevox_speaker', speaker)
        # 読み上げフィールド
        bool_keys = [
            'read_date', 'read_youbi', 'read_kinmu',
            'read_shubetsu', 'read_jikoku', 'read_naiyou', 'read_labels',
        ]
        for key in bool_keys:
            save_setting(key, '1' if request.form.get(key) else '0')
        flash('設定を保存しました。', 'success')
        return redirect(url_for('settings'))

    cfg = get_all_settings()
    speakers = fetch_voicevox_speakers()
    media_files = get_media_files()
    return render_template('settings.html', cfg=cfg, speakers=speakers, media_files=media_files)


def get_media_files() -> list:
    """media/ 内の WAV ファイル一覧を返す（新しい順）。"""
    if not os.path.isdir(MEDIA_DIR):
        return []
    files = []
    for fname in os.listdir(MEDIA_DIR):
        if not fname.lower().endswith('.wav'):
            continue
        fpath = os.path.join(MEDIA_DIR, fname)
        try:
            stat = os.stat(fpath)
            files.append({
                'name': fname,
                'size': stat.st_size,
                'mtime': stat.st_mtime,
            })
        except OSError:
            pass
    files.sort(key=lambda f: f['mtime'], reverse=True)
    return files


def _safe_media_filename(filename: str) -> bool:
    """パストラバーサル対策: media/ 直下の .wav ファイル名のみ許可。"""
    return (
        filename == os.path.basename(filename)
        and filename.lower().endswith('.wav')
        and '..' not in filename
        and '/' not in filename
        and '\\' not in filename
    )


@app.route('/settings/delete_media', methods=['POST'])
def delete_media():
    """指定ファイルを media/ から削除する。"""
    filename = request.form.get('filename', '').strip()
    if not _safe_media_filename(filename):
        flash('無効なファイル名です。', 'error')
        return redirect(url_for('settings'))
    fpath = os.path.join(MEDIA_DIR, filename)
    if os.path.exists(fpath):
        os.remove(fpath)
        flash(f'{filename} を削除しました。', 'success')
    else:
        flash('ファイルが見つかりません。', 'error')
    return redirect(url_for('settings') + '#media')


@app.route('/settings/clear_media', methods=['POST'])
def clear_media():
    """media/ 内の WAV ファイルをすべて削除する。"""
    deleted = 0
    if os.path.isdir(MEDIA_DIR):
        for fname in os.listdir(MEDIA_DIR):
            if fname.lower().endswith('.wav'):
                try:
                    os.remove(os.path.join(MEDIA_DIR, fname))
                    deleted += 1
                except OSError:
                    pass
    flash(f'{deleted} 件の音声ファイルを削除しました。', 'success')
    return redirect(url_for('settings') + '#media')


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5003, host="0.0.0.0")
