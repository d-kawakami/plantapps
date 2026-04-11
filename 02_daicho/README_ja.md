# 機器台帳管理システム

設備・機器の情報を一元管理するための Web アプリケーションです。Flask + SQLite で動作し、ブラウザから機器の登録・検索・編集・CSV エクスポートが行えます。データベースモデルはデモ用に匿名化しています。

[English version here](README.md)

## 機能

- **機器一覧・検索** — 施設番号・施設名・大/中/小分類・稼働状況・製造所などで絞り込み。類義語による自然言語検索にも対応
- **機器詳細・編集** — 機器情報の登録・更新・削除・複製
- **測定値管理** — 機器ごとの測定履歴を記録
- **CSV インポート** — Shift-JIS / UTF-8 などの文字コードを自動判定してインポート
- **CSV エクスポート** — 現在の検索条件でフィルタした結果を CSV (UTF-8 BOM付き) でダウンロード
- **ダッシュボード** — 機器台数・稼働状況の集計、老朽化上位機器の表示
- **オートコンプリート** — 入力フォームの候補補完

## 技術スタック

| 要素 | 内容 |
|------|------|
| バックエンド | Python 3.x / Flask |
| データベース | SQLite (`daicho.db`) |
| フロントエンド | HTML / CSS / JavaScript (テンプレート: Jinja2) |
| 文字コード検出 | chardet |

## セットアップ

### 必要環境

- Python 3.9 以上

### インストール

```bash
pip install -r requirements.txt
```

### 起動

**Linux / macOS:**
```bash
./start.sh
```

**Windows:**
```bat
start.bat
```

または直接:
```bash
python app.py
```

起動後、ブラウザで `http://localhost:5007` を開いてください。

## 初期データ

起動時に機器テーブルが空の場合、同ディレクトリの `kikilist.csv` を自動インポートします。

## ディレクトリ構成

```
02_daicho/
├── app.py              # Flask アプリ本体・ルーティング
├── models.py           # データアクセス層 (CRUD / CSV マッピング)
├── database.py         # DB 接続・スキーマ初期化
├── requirements.txt    # Python 依存パッケージ
├── kikilist.csv        # 初期データ (機器一覧)
├── start.sh            # 起動スクリプト (Linux/macOS)
├── start.bat           # 起動スクリプト (Windows)
├── static/             # CSS などの静的ファイル
└── templates/          # Jinja2 テンプレート
```

## API エンドポイント

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/api/equipment` | 機器一覧取得 (フィルタ・ページネーション対応) |
| POST | `/api/equipment` | 機器新規登録 |
| GET | `/api/equipment/:id` | 機器1件取得 |
| PUT | `/api/equipment/:id` | 機器更新 |
| DELETE | `/api/equipment/:id` | 機器削除 |
| POST | `/api/equipment/:id/duplicate` | 機器複製 |
| GET | `/api/equipment/:id/measurements` | 測定値一覧 |
| POST | `/api/equipment/:id/measurements` | 測定値登録 |
| GET | `/api/facilities` | 施設一覧 |
| GET | `/api/categories` | 分類一覧 |
| GET | `/api/autocomplete` | フィールド補完候補 |
| POST | `/api/import/csv` | CSV インポート |
| GET | `/api/export/csv` | CSV エクスポート |
| GET | `/api/dashboard/stats` | ダッシュボード統計 |
