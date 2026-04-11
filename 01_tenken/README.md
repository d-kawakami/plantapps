# 日常点検アプリ

Flask + PWA で構築した水処理施設向け日常点検記録システムです。
オンライン・オフラインどちらの環境でも動作し、結果はサーバー（SQLite）とブラウザ（IndexedDB）の両方に保存されます。

---

## システム概要

| 項目 | 内容 |
|------|------|
| バックエンド | Python 3.13 / Flask 3.x |
| データベース | SQLite 3（`tenken.db`） |
| フロントエンド | Vanilla JS（ES Modules） |
| オフライン対応 | Service Worker + IndexedDB（PWA） |
| Excel連携 | openpyxl（書き出し・インポート） |

### 主な機能

- **曜日別点検入力** — 月〜金の各曜日に対応した点検項目を表示し、〇/△/× で結果を記録
- **水曜日の週別対応** — 第1〜4週で点検項目が切り替わる週別フィルタ
- **先発グループ表示** — A/B/C グループ・月別号機を自動表示
- **オフライン動作** — ネットワーク切断時はブラウザに保存し、復帰後に自動同期
- **Excel 書き出し** — 指定日の点検結果を既存フォーマットの `.xlsm` に転記してダウンロード
- **Excel インポート** — 点検表 Excel（マスタシート）から点検項目を一括更新
- **結果リセット** — 点検ページ単位、またはトップページから指定日の全結果を一括リセット
- **音声入力** — Web Speech API を使った音声コマンドで〇/△/× の入力・項目移動・メモ入力をハンズフリーで操作

---

## ファイル構造

```
05_tenken/
├── app.py              # Flask 本体・REST API ルート定義
├── database.py         # DB 初期化・テーブル作成・シードデータ投入
├── models.py           # SQLite CRUD 関数
├── seed_data.py        # 点検項目マスタ（初期データ）
├── export_excel.py     # Excel 書き出し処理
├── import_excel.py     # Excel 点検表インポート処理
├── generate_icons.py   # PWA アイコン生成スクリプト
├── requirements.txt    # Python 依存パッケージ
├── start.bat           # Windows 用起動スクリプト
├── start.sh            # Linux / macOS 用起動スクリプト
├── tenken.db           # SQLite データベース（初回起動時に自動生成）
├── templates/
│   ├── index.html      # トップページ（曜日選択・書き出し・リセット）
│   └── inspect.html    # 点検入力ページ
└── static/
    ├── manifest.json   # PWA マニフェスト
    ├── sw.js           # Service Worker（オフラインキャッシュ・同期）
    ├── css/
    │   └── style.css   # スタイルシート
    ├── icons/
    │   ├── icon-192.png
    │   └── icon-512.png
    └── js/
        ├── app.js      # メイン JavaScript（点検ロジック・同期処理）
        ├── db.js       # IndexedDB ラッパー
        └── voice.js    # 音声認識エンジン（Web Speech API ラッパー）
```

### データベーステーブル

| テーブル | 内容 |
|----------|------|
| `inspection_items` | 点検項目マスタ（曜日・建物・場所・週フィルタ等） |
| `senpatu_groups` | 先発グループ定義（A/B/C・月別号機） |
| `inspection_results` | 点検結果（item_id + 日付でユニーク） |

### REST API

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/api/health` | 死活確認（オフライン検知用） |
| GET | `/api/items?day=&week=` | 指定曜日・週の点検項目一覧 |
| GET | `/api/senpatu?day=` | 指定曜日の先発グループ一覧 |
| GET | `/api/results?date=` | 指定日の点検結果一覧 |
| POST | `/api/results` | 点検結果の単件保存（UPSERT） |
| POST | `/api/results/batch` | 点検結果のバッチ保存（オフライン同期用） |
| POST | `/api/results/reset` | 指定日の全点検結果を削除 |
| GET | `/api/export?date=` | 指定日の結果を Excel にして返す |
| POST | `/api/import-excel` | 点検表 Excel からマスタを更新 |

---

## セットアップ

### 必要環境

- Python 3.10 以上
- pip

### インストール

```bash
# リポジトリのルートへ移動
cd 05_tenken

# 依存パッケージをインストール
pip install -r requirements.txt
```

依存パッケージ:

```
Flask>=3.0.0
openpyxl>=3.1.0
```

---

## 起動方法

### Windows

`start.bat` をダブルクリック、または:

```bat
start.bat
```

### Linux / macOS

```bash
bash start.sh
```

### 直接実行

```bash
python app.py
```

起動後、ブラウザで `http://localhost:5000` を開いてください。

> **Note:** DB ファイル（`tenken.db`）は初回起動時に自動で作成されます。
> 手動で初期化したい場合は `python database.py` を実行してください。

---

## 使い方

### 点検の記録

1. トップページで対象の**曜日カード**をタップ
2. 点検番号ごとに **〇 / △ / ×** をタップして結果を入力
3. 追記が必要な場合は **✏️ メモ** ボタンからメモを入力して保存
4. 結果は即時保存されます（オフライン時はローカルに保存し、オンライン復帰後に自動同期）

### 水曜日の週切り替え

水曜日の点検ページには**週選択ボタン**（第1〜4週）が表示されます。
該当週をタップすると、その週の点検項目に切り替わります。

### 一括入力

- **✅ 異常なし** ボタン: 全項目を `result_hint`（基準判定）で一括入力します
- **結果をリセット** ボタン: 当日のページ内全項目の結果をリセットします

### Excel 書き出し

1. トップページの「📥 Excel 書き出し」で対象日を選択
2. **⬇ ダウンロード** をクリックして `.xlsm` ファイルを取得

### 点検表マスタのインポート

1. トップページの「📂 点検表 Excel インポート」を開く
2. `点検表(マスタ)` シートを含む `.xlsm` / `.xlsx` を選択
3. **▶ インポート実行** をクリック（`inspection_items` テーブルが上書きされます）

### 音声入力

点検入力ページのヘッダーにある **🎤 ボタン**をタップすると音声認識が開始されます（ボタンが赤くパルス）。もう一度タップで停止。

| 発話例 | 動作 |
|--------|------|
| 「異常なし」「正常」「まる」「良好」 | 〇 を入力 → 次の未入力項目へ移動 |
| 「要注意」「注意」「さんかく」 | △ を入力 → 次へ |
| 「異常あり」「異常」「ばつ」「不良」 | × を入力 → 次へ |
| 「次」「次へ」 | 次の未入力項目へ移動 |
| 「前」「戻る」 | 前の項目へ移動 |
| 「メモ」 | メモ欄を開く |
| 「メモ 圧力低下」 | メモ欄を開いて「圧力低下」と入力 |
| 「保存」 | メモを保存 |

**動作の詳細**

- フォーカス行（青い左ボーダー）が現在の入力対象。ページ表示時に最初の未入力項目へ自動移動
- **🎤 ボタンをタップすると、現在フォーカス中の項目番号と機器名を音声で読み上げてから認識を開始**
- 認識したテキストは画面下部にトーストで表示（✅ = コマンド認識、❓ = 未認識）
- 過去日の閲覧モードでは結果入力はブロックされる（ナビのみ有効）
- 10 秒間無音で自動停止
- Web Speech API 非対応端末ではボタンが無効化

### 全結果リセット（管理操作）

1. トップページ最下部の「🗑 全結果リセット」で対象日を選択
2. **全結果をリセット** をクリック
3. 確認ダイアログで OK → サーバー DB とブラウザの IndexedDB を両方削除

---

## PWA としてのインストール

モバイル・PC 共に「ホーム画面に追加」でアプリとしてインストールできます。

- **オフライン対応**: アプリシェル（HTML/CSS/JS）は Service Worker がキャッシュし、ネットワーク不通でも画面を開けます
- **オフライン記録**: 記録は IndexedDB に保存され、オンライン復帰時にサーバーへ自動同期されます

---

## ライセンス

MIT License

Copyright (c) 2024 Daisuke Kawakami

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
