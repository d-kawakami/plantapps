# Plant Apps

産業プラント向けのプラントエンジニア日常業務支援アプリ群です。
4つのWebアプリを個別に使うことも、共有ナビゲーションとクロスアプリ連携で組み合わせて使うこともできます。

**リポジトリ:** https://github.com/d-kawakami/plantapps

[English → README.md](README.md)

---

## アプリ一覧

| # | アプリ名 | ポート | 概要 |
|---|---------|--------|------|
| 01 | **日常点検アプリ** | `5001` | 曜日別の設備点検結果を記録するPWA |
| 02 | **機器台帳** | `5002` | 施設内全機器の情報を一元管理するデータベース |
| 03 | **引継ぎノート** | `5003` | シフト引継ぎログ（キーワード検索・音声読み上げ対応） |
| 04 | **写真管理** | `5400` | 現場で撮影した写真・動画のアップロードと閲覧 |

4つのアプリには共通の**ボトムナビゲーションバー**が搭載されており、どの画面からでも別アプリへ瞬時に切り替えられます。

---

## アプリ間連携の仕組み

```
┌─────────────────────────────────┐
│  ヘッダー（アプリ名 ＋ コンテキストアクション）  │
├─────────────────────────────────┤
│                                 │
│  メインコンテンツ                          │
│                                 │
│  ┌─────────────────────────┐   │
│  │ コンテキストリンク          │   │
│  │ 例：「機器台帳で詳細確認→」  │   │
│  └─────────────────────────┘   │
│                                 │
├─────────────────────────────────┤
│  ボトムタブバー                          │
│  [引継ぎ] [機器台帳] [点検] [写真]        │
└─────────────────────────────────┘
```

### 共有コンポーネント（`common_templates/`）

| ファイル | 役割 |
|---------|------|
| `bottom_nav.html` | 固定ボトムナビゲーションバー（Jinja2 インクルード） |
| `context_link.html` | 関連アプリへのコンテキストリンクカード |

### クロスアプリ API

| アプリ | エンドポイント | 利用元 |
|--------|--------------|--------|
| 機器台帳 | `GET /api/equipment/search?name=<機器名>` | 引継ぎノート・点検アプリ（CORS対応） |
| 写真管理 | `POST /api/upload` | 点検アプリ（現場写真を直接保存、CORS対応） |

#### 使用例

```javascript
// 引継ぎノートから機器台帳を検索
const res = await fetch(`http://${host}:5002/api/equipment/search?name=ポンプA`);
const { items } = await res.json();

// 点検アプリから写真管理へ写真を送信
const fd = new FormData();
fd.append('image', photoFile);
fd.append('source', 'inspection');
fd.append('memo', '5号ポンプ軸受部');
await fetch(`http://${host}:5400/api/upload`, { method: 'POST', body: fd });
```

---

## 動作要件

- Python 3.10 以上
- pip

各アプリの依存パッケージをインストールします：

```bash
pip install -r 01_tenken/requirements.txt
pip install -r 02_daicho/requirements.txt
pip install flask openpyxl          # 03_note
pip install flask                   # 04_photo
```

まとめてインストールする場合：

```bash
pip install flask openpyxl chardet
```

---

## 一括起動

### Windows

`start_all.bat` をダブルクリック、またはターミナルで：

```bat
start_all.bat
```

各アプリが別のコマンドプロンプトウィンドウで起動します。

### Linux / macOS / Termux（Android）

```bash
bash start_all.sh
```

4つのアプリがバックグラウンドで起動します。`Ctrl+C` で全停止。

---

## 個別起動

### 01 日常点検アプリ（ポート 5001）

```bash
cd 01_tenken
python app.py
```

ブラウザで `http://localhost:5001` を開く。

### 02 機器台帳（ポート 5002）

```bash
cd 02_daicho
python app.py
```

ブラウザで `http://localhost:5002` を開く。

### 03 引継ぎノート（ポート 5003）

```bash
cd 03_note
python app.py
```

ブラウザで `http://localhost:5003` を開く。

### 04 写真管理（ポート 5400）

```bash
cd 04_photo
python app.py
```

ブラウザで `http://localhost:5400/media` を開く。

---

## モバイル端末からのアクセス（LAN）

全アプリは `0.0.0.0` にバインドしているため、同一Wi-Fiネットワーク内の端末からアクセスできます。
`localhost` をサーバーのIPアドレスに置き換えてください：

```
http://192.168.1.xxx:5001    ← 日常点検
http://192.168.1.xxx:5002    ← 機器台帳
http://192.168.1.xxx:5003    ← 引継ぎノート
http://192.168.1.xxx:5400/media    ← 写真管理
```

ボトムナビゲーションバーは `window.location.hostname` を自動取得して各タブのURLを構成するため、IPアドレスが変わっても設定変更不要です。

---

## ディレクトリ構成

```
plantapps/
├── README.md               ← 英語版
├── README.ja.md            ← このファイル（日本語版）
├── start_all.bat           ← 一括起動（Windows）
├── start_all.sh            ← 一括起動（Linux/macOS）
│
├── common_templates/       ← 共通Jinja2コンポーネント
│   ├── bottom_nav.html     ← ボトムナビゲーションバー
│   └── context_link.html   ← コンテキストリンクカード
│
├── 01_tenken/              ← 日常点検アプリ
│   ├── app.py              ← Flaskアプリ本体（ポート 5001）
│   ├── database.py
│   ├── models.py
│   ├── templates/
│   └── static/
│
├── 02_daicho/              ← 機器台帳アプリ
│   ├── app.py              ← Flaskアプリ本体（ポート 5002）
│   ├── database.py
│   ├── models.py
│   └── templates/
│
├── 03_note/                ← 引継ぎノートアプリ
│   ├── app.py              ← Flaskアプリ本体（ポート 5003）
│   └── templates/
│
└── 04_photo/               ← 写真管理アプリ
    ├── app.py              ← Flaskアプリ本体（ポート 5400）
    ├── uploads/            ← アップロードファイル保存先
    └── templates/
```

---

## 各アプリの詳細

### 01 日常点検アプリ

- 曜日（月〜金）を選択し、点検項目ごとに〇／△／×を記録
- 水曜日は週番号（第1〜4週）でフィルタ切り替え
- PWA対応 — オフライン時はIndexedDBに保存し、復帰後に自動同期
- Web Speech APIによる音声入力（ハンズフリー操作）
- Excelへの書き出しと点検マスタのインポート
- **コンテキストリンク**：点検中の設備を機器台帳で参照、現場写真を写真管理に直接送信

### 02 機器台帳

- 設備・機器の情報（名称・設置場所・分類・稼働状況・製造所など）を検索・管理
- 機器ごとの測定値履歴を記録
- Shift-JIS / UTF-8自動判定のCSVインポート・エクスポート
- 老朽化分析を含むダッシュボード
- **クロスアプリAPI**：`GET /api/equipment/search?name=<機器名>`（CORS対応、他3アプリから呼び出し可能）

### 03 引継ぎノート

- 日付・勤務区分・種別・時刻・内容・記入者を記録
- 同義語展開付き全文キーワード検索、関連度順ソート
- VOICEVOXによる日本語音声読み上げ（オプション、ローカル動作）
- Excel（.xlsx）からの一括インポート
- **コンテキストリンク**：ノートに登場した機器名を機器台帳で検索・確認

### 04 写真管理

- スマートフォンからブラウザ経由またはドラッグ＆ドロップで写真・動画をアップロード
- エクスプローラー風の一体画面でアップロード、検索、プレビュー、ダウンロード、削除
- サムネイル表示と詳細リスト表示を切り替え
- **クロスアプリAPI**：`POST /api/upload`（CORS対応、点検アプリから現場写真を直接受信）

---

## ボトムナビゲーションバーの仕様

共有コンポーネント `bottom_nav.html` の特徴：

| 項目 | 仕様 |
|------|------|
| 表示位置 | 画面下端に固定（`position: fixed`）、スクロールに追従しない |
| アクティブ状態 | 現在のアプリタブを青色・上部インジケーターバーで表示 |
| アイコン | lucide準拠のインラインSVG（ClipboardList / Database / CheckSquare / Image） |
| タップターゲット | 最小高さ56px（44px以上を確保） |
| iOSセーフエリア | `env(safe-area-inset-bottom)` でホームインジケーターに対応 |
| URL自動解決 | `window.location.hostname` を使用するためIPアドレスが変わっても動作 |

各アプリへの組み込み方法（Jinja2テンプレート内）：

```html
<!-- アプリに対応したIDをactive_appに設定してinclude -->
{% set active_app = 'inspection' %}  {# 'handover' | 'equipment' | 'inspection' | 'photo' #}
{% include 'bottom_nav.html' %}
```

---

## トラブルシューティング

### 「Address already in use」エラー

指定ポートが既に使用されています。以下で確認・停止してください：

```bash
# Linux / macOS
lsof -i :5001   # 使用中のプロセスを確認
kill <PID>

# Windows（PowerShell）
netstat -ano | findstr :5001
taskkill /PID <PID> /F
```

### モバイルからアクセスできない

- サーバーとモバイル端末が同一Wi-Fiに接続されているか確認
- Windowsファイアウォールで各ポート（5001〜5003、5400）の受信を許可
- サーバーのIPアドレスは `ipconfig`（Windows）または `ip a`（Linux）で確認

### ボトムナビのタブURLが正しくない

- 各アプリが正しいポートで起動しているか確認（`start_all.bat` / `start_all.sh` を使用推奨）
- ブラウザのコンソールで `window.location.hostname` が期待通りのIPを返しているか確認

---

## ライセンス

MIT License — 各アプリディレクトリのREADMEを参照してください。
