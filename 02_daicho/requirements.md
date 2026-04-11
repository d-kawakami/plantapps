# 機器台帳システム 要求定義書

**バージョン**: 0.1
**作成日**: 2026-03-03
**対象システム**: 07_daicho (機器台帳管理システム 改良版)

---

## 1. 背景と目的

### 1.1 現状の課題

| # | 課題 | 深刻度 |
|---|------|--------|
| 1 | 登録・編集操作が複雑で入力途中のデータを人的ミスで消してしまう | 高 |
| 2 | 施設ごとに2,000件程度のデータを扱うため、検索・絞り込みが困難 | 高 |
| 3 | 日常点検アプリ（05_tenken）・引き継ぎノートアプリ（03_notedb）と連携できていない | 中 |
| 4 | 機器の劣化診断・老朽化予測が台帳データから直接行えない | 中 |
| 5 | 55列超の項目が一覧されており、利用頻度の低い項目が見づらさを招いている | 中 |

### 1.2 目的

- 入力ミス・データ消失リスクを最小化した、安全・直感的な機器台帳システムを構築する
- 既存アプリ（05_tenken / 03_notedb）との連携を実現し、施設管理情報を統合的に参照可能にする
- 将来の機器劣化診断・設備更新計画機能への拡張基盤を整備する

---

## 2. システム概要

### 2.1 システム名

**機器台帳管理システム（daicho）**

### 2.2 対象ユーザー

| ロール | 説明 |
|--------|------|
| 管理者 | 全施設のデータ参照・登録・更新・削除 |
| 担当者 | 担当施設のデータ参照・更新 |
| 閲覧者 | 参照のみ（将来対応） |

### 2.3 システム全体像

```
┌─────────────────────────────────────────────────────┐
│                 機器台帳管理システム                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ 機器一覧  │  │ 機器詳細 │  │  劣化診断ダッシュ  │  │
│  │ 検索・絞込│  │ 登録・編集│  │  ボード（将来）   │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────┘
           ↕ API / 共有DB
┌──────────────────┐    ┌─────────────────────┐
│  05_tenken       │    │  03_notedb          │
│  日常点検アプリ    │    │  引き継ぎノートアプリ │
│  (機器名/設置場所  │    │  (機器異常メモ参照)  │
│   参照)          │    │                     │
└──────────────────┘    └─────────────────────┘
```

---

## 3. 機能要求

### 3.1 機器台帳 CRUD

#### 3.1.1 一覧表示・検索

- **FR-01**: 機器一覧をページネーション付きで表示する（1ページ50件）
- **FR-02**: 以下の条件で絞り込み検索ができる
  - 施設名称 / 工種 / 大分類 / 中分類 / 小分類
  - 機器名称（部分一致）/ 製造所
  - 稼働状況（稼働中 / 停止 / 撤去）
  - 設置年月日の範囲
- **FR-03**: 一覧表示列をユーザーが選択・保存できる（表示列カスタマイズ）
- **FR-04**: CSVエクスポート機能（現在のフィルタ結果を出力）

#### 3.1.2 登録・編集

- **FR-05**: 入力フォームは項目をタブ（基本情報 / 資産情報 / 分類 / 書類 / 備考）に分けて表示し、一度に全項目を見せない
- **FR-06**: 登録・編集は**自動下書き保存**（ローカルストレージ or IndexedDB）を行い、誤操作によるデータ消失を防ぐ
- **FR-07**: 保存前に確認ダイアログを表示する
- **FR-08**: 入力値のバリデーション
  - 設置年月日 > 撤去年月日 の場合はエラー
  - 耐用年数・目標耐用年数は正の整数
  - 取得価額・再取得価額は0以上の数値
- **FR-09**: 既存CSVからの一括インポート機能（文字コード自動判定）
- **FR-10**: 削除は論理削除（削除フラグ）とし、物理削除は管理者のみ可能

#### 3.1.3 複製・テンプレート

- **FR-11**: 既存機器を複製して新規登録を効率化する機能
- **FR-12**: 大分類/中分類/小分類の組み合わせをテンプレートとして保存できる

### 3.2 劣化診断支援（フェーズ2）

- **FR-13**: 設置年月日と耐用年数から**経過年数・残存耐用年数・老朽化率**を自動計算・表示する
- **FR-14**: 施設内の機器を老朽化率でソート・グラフ表示するダッシュボードを提供する
- **FR-15**: 老朽化率が閾値（例: 80%）を超えた機器をハイライト・アラート表示する
- **FR-16**: 設備重要度 × 老朽化率のマトリクスで更新優先度を可視化する
- **FR-17**: 複数回測定値を時系列で記録・グラフ化し、劣化トレンドを確認できる
- **FR-18**: 更新計画シート（年度別更新予定・再取得価額積算）をPDF/Excel出力する（将来）

### 3.3 他アプリとの連携

#### 3.3.1 05_tenken（日常点検アプリ）との連携

- **FR-19**: 台帳の機器ID・機器名称・設置場所を点検アプリの点検項目マスタに同期するAPIエンドポイントを提供する
- **FR-20**: 点検アプリ側から機器IDを指定して台帳情報（形式・製造所・設置年月日）を参照できるAPIを提供する

#### 3.3.2 03_notedb（引き継ぎノートアプリ）との連携

- **FR-21**: ノートアプリの記事に機器IDを紐付けられる（タグ機能）
- **FR-22**: 台帳の機器詳細画面から、その機器に紐付いたノート記事の一覧を表示できる

### 3.4 アクセス・認証

- **FR-23**: ログイン認証（施設コードとパスワード or セッション管理）
- **FR-24**: 施設単位でのアクセス制限（担当者は自施設のみ編集可）

---

## 4. 非機能要求

| ID | 項目 | 要件 |
|----|------|------|
| NFR-01 | レスポンス | 一覧検索: 1秒以内（全施設20,000件・インデックス使用時） |
| NFR-02 | 可用性 | 庁内LAN環境での常時稼働 |
| NFR-03 | データ保全 | 編集中の自動下書き保存（最大5分ごと） |
| NFR-04 | インポート | 現行CSVの全列を損失なく取り込み可能 |
| NFR-05 | 移植性 | Windows Server / Linux 両対応（Python + SQLite） |
| NFR-06 | UI | スマートフォン・タブレットでも閲覧可能なレスポンシブデザイン |
| NFR-07 | ログ | 更新者・更新日時の自動記録（監査ログ） |

---

## 5. データモデル（主要テーブル）

### 5.0 データ規模とパフォーマンス設計

| 項目 | 値 |
|------|----|
| 施設数 | 約10施設 |
| 施設あたり件数 | 約2,000件 |
| 総レコード数 | **約20,000件** |
| 推定DBサイズ | 約50〜100MB（添付ファイルなし） |

SQLiteは数百万件まで実用的に動作する。20,000件はパフォーマンス上の懸念は不要。
以下のインデックスを必ず作成し、検索速度を担保する。

```sql
-- 必須インデックス
CREATE INDEX idx_equipment_facility  ON equipment(facility_no);
CREATE INDEX idx_equipment_category  ON equipment(category_l, category_m, category_s);
CREATE INDEX idx_equipment_status    ON equipment(op_status);
CREATE INDEX idx_equipment_installed ON equipment(installed_at);
CREATE INDEX idx_equipment_deleted   ON equipment(deleted);
-- 複合インデックス（施設絞り込み + 削除フラグは頻出パターン）
CREATE INDEX idx_equipment_facility_active ON equipment(facility_no, deleted);
```

> **備考**: 機器名称の部分一致（`LIKE '%xxx%'`）はインデックス不使用だが、
> 20,000件の全件スキャンでも実測〜数十ms程度であり実用上問題ない。
> 将来的に高速化が必要な場合は **SQLite FTS5（全文検索拡張）** で対応可能。

### 5.1 機器台帳テーブル（equipment）

現行CSVの全列を保持しつつ、以下を追加・整理する。

```sql
CREATE TABLE equipment (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    -- 識別
    record_id       INTEGER UNIQUE,         -- レコードID（現行）
    customer_code   TEXT,                   -- 顧客コード
    facility_no     TEXT,                   -- 施設番号
    facility_name   TEXT,                   -- 施設名称
    equipment_id    INTEGER,                -- 機器ID（施設内連番）
    -- 機器基本情報
    equipment_name  TEXT NOT NULL,          -- 機器名称
    model           TEXT,                   -- 形式
    work_type       TEXT,                   -- 工種番号
    location        TEXT,                   -- 設置場所
    manufacturer    TEXT,                   -- 製造所
    -- 分類
    category_l      TEXT,                   -- 大分類
    category_m      TEXT,                   -- 中分類
    category_s      TEXT,                   -- 小分類
    -- 資産情報
    installed_at    DATE,                   -- 設置年月日
    removed_at      DATE,                   -- 撤去年月日
    service_life    INTEGER,                -- 耐用年数
    target_life     INTEGER,                -- 目標耐用年数
    acquisition_cost INTEGER,              -- 取得価額
    replacement_cost INTEGER,              -- 再取得価額
    asset_group     TEXT,                   -- 資産グループ
    fixed_asset_no  TEXT,                   -- 固定資産番号
    -- 保全情報
    op_status       TEXT DEFAULT '稼働中',  -- 稼働状況
    maintenance_method TEXT,               -- 保全方法
    legal_inspection INTEGER DEFAULT 0,    -- 法定点検有無
    importance      TEXT,                   -- 設備重要度
    -- 劣化診断用
    degradation_flag INTEGER DEFAULT 0,    -- 劣化予兆判断可否
    cost_impact     TEXT,                   -- コストインパクト
    upgrade_target  INTEGER DEFAULT 0,     -- 高度化対象
    high_degradation INTEGER DEFAULT 0,   -- 劣化度大
    -- その他
    spec            TEXT,                   -- 仕様
    notes1          TEXT,                   -- 記事１
    notes2          TEXT,                   -- 記事２
    series_no       TEXT,                   -- 系列番号
    unit_no         TEXT,                   -- 号機番号
    form_id         TEXT,                   -- 保守点検様式ID
    -- 管理
    deleted         INTEGER DEFAULT 0,      -- 削除フラグ
    updated_at      DATETIME,               -- 更新日時
    updated_by      TEXT,                   -- 更新ユーザID
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 5.2 測定値テーブル（measurement）

複数回測定値を時系列で蓄積する。

```sql
CREATE TABLE measurement (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id    INTEGER REFERENCES equipment(id),
    measured_at     DATE NOT NULL,          -- 測定日
    value           REAL,                   -- 測定値
    threshold       REAL,                   -- 許容限界値
    note            TEXT,
    recorded_by     TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 5.3 機器-ノート紐付けテーブル（equipment_note）

```sql
CREATE TABLE equipment_note (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id    INTEGER REFERENCES equipment(id),
    note_id         INTEGER,                -- 03_notedb の記事ID
    note_app        TEXT DEFAULT '03_notedb',
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. API設計（概要）

| メソッド | エンドポイント | 説明 |
|----------|---------------|------|
| GET | `/api/equipment` | 一覧取得（クエリパラメータで検索・絞込） |
| GET | `/api/equipment/<id>` | 機器詳細取得 |
| POST | `/api/equipment` | 新規登録 |
| PUT | `/api/equipment/<id>` | 更新 |
| DELETE | `/api/equipment/<id>` | 論理削除 |
| GET | `/api/equipment/<id>/measurements` | 測定値履歴 |
| POST | `/api/equipment/<id>/measurements` | 測定値登録 |
| GET | `/api/equipment/<id>/notes` | 紐付きノート一覧 |
| GET | `/api/facilities` | 施設一覧 |
| GET | `/api/categories` | 分類マスタ一覧 |
| POST | `/api/import/csv` | CSVインポート |
| GET | `/api/export/csv` | CSVエクスポート |
| GET | `/api/dashboard/aging` | 老朽化ダッシュボードデータ |

---

## 7. UI設計方針

### 7.1 画面構成

```
/ (ダッシュボード)
  ├── 老朽化アラート件数
  ├── 施設別機器台数サマリ
  └── 最近更新した機器
/equipment (機器一覧)
  ├── 検索フィルタパネル
  ├── テーブル一覧（列選択可）
  └── ページネーション
/equipment/new (新規登録)
/equipment/<id> (詳細)
/equipment/<id>/edit (編集)
  ├── タブ: 基本情報
  ├── タブ: 資産・分類
  ├── タブ: 保全情報
  ├── タブ: 書類・仕様
  └── タブ: 測定値履歴
/import (CSVインポート)
/dashboard/aging (劣化診断ダッシュボード) ← フェーズ2
```

### 7.2 入力UXの重点事項

- **自動下書き保存バー**: 画面上部に「下書き保存済み: HH:MM:SS」を常時表示
- **離脱防止**: 未保存変更がある場合、ページ移動時に確認ダイアログを表示
- **段階的入力**: 必須項目（機器名称・施設・設置場所・大分類）のみで保存可能とし、任意項目は後から追記可能
- **オートコンプリート**: 機器名称・製造所・設置場所は過去入力値から候補表示

---

## 8. 技術スタック（案）

| 項目 | 採用技術 |
|------|---------|
| サーバー | Python / Flask（既存環境と統一） |
| DB | SQLite（既存 tenken_xx.db と同様の管理方式） |
| フロントエンド | HTML + CSS + Vanilla JS（ES Module）/ または軽量フレームワーク |
| ORM | なし（models.py で直接 SQL 操作、既存パターンに統一） |
| グラフ | Chart.js（劣化診断ダッシュボード用） |
| PDF出力 | ReportLab または WeasyPrint（フェーズ2） |

---

## 9. 開発フェーズ

### フェーズ1（MVP）

- 機器台帳 CRUD（一覧・登録・編集・削除）
- CSVインポート / エクスポート
- 自動下書き保存・入力保護
- 05_tenken / 03_notedb への参照API

### フェーズ2（劣化診断）

- 老朽化率計算・ダッシュボード
- 測定値履歴グラフ
- 更新優先度マトリクス

### フェーズ3（高度化）

- 更新計画書PDF出力
- 設備重要度 × コスト分析
- 認証・アクセス制御

---

## 10. 未決事項・確認事項

| # | 項目 | 確認相手 |
|---|------|---------|
| Q1 | 複数施設のDBを統合するか、施設ごとにDBを分けるか | 運用担当者 |
| Q2 | 認証はシンプルなパスワード認証で十分か | セキュリティ担当 |
| Q3 | 劣化診断の「劣化予兆判断」アルゴリズムの基準値はどこにあるか | 設備担当者 |
| Q4 | 現行システムのエクスポートCSVは常にUTF-8か、それともShift-JISか | 現行システム担当 |
| Q5 | 05_tenken との連携はリアルタイム同期か、定期バッチか | 運用担当者 |

---

*本文書はフォルダ `07_daicho/requirements.md` に保存。改訂時はバージョン番号を更新すること。*