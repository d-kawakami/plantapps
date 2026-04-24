# 点検DB同期 サーバ側セットアップガイド

## 1. DB受信エンドポイント仕様

### POST /api/tenken/upload

点検DBファイル（tenken.db）をサーバへアップロードします。

| 項目 | 内容 |
|---|---|
| メソッド | POST |
| Content-Type | multipart/form-data |
| パラメータ | `db` : SQLiteファイル |

**レスポンス (200 OK):**
```json
{
  "status": "ok",
  "backup": "/opt/media-kanri/tenken_db/tenken.db.20250419_103000.bak",
  "saved_at": "2025-04-19T10:30:00.123456"
}
```
※ 既存DBがない場合は `"backup": null`

**エラーレスポンス:**
```json
{"error": "db フィールドが必要です"}
```

---

### GET /api/tenken/status

サーバ側の tenken.db の状態を確認します。

| 項目 | 内容 |
|---|---|
| メソッド | GET |
| パラメータ | なし |

**レスポンス (200 OK):**
```json
{
  "exists": true,
  "size_bytes": 40960,
  "last_modified": "2025-04-19T10:30:00",
  "backup_count": 3
}
```

---

## 2. セットアップ手順

### 前提条件

- Ubuntu Server 24.04
- hostapd AP 設定済み（IP: 192.168.10.1）
- Python 3.10 以上

### 実行順序

```bash
# リポジトリ配置
sudo git clone https://github.com/d-kawakami/media-kanri /opt/media-kanri

# venv作成・依存インストール
cd /opt/media-kanri
python3 -m venv venv
sudo /opt/media-kanri/venv/bin/pip install flask gunicorn

# DB保存用ディレクトリ
sudo mkdir -p /opt/media-kanri/tenken_db
sudo chown -R www-data:www-data /opt/media-kanri

# systemd サービス配置・有効化
sudo cp doc/tenken-media-kanri.service /etc/systemd/system/media-kanri.service
sudo systemctl daemon-reload
sudo systemctl enable --now media-kanri
sudo systemctl status media-kanri

# nginx 設定（S-Task 3）
sudo cp doc/nginx-media-kanri.conf /etc/nginx/sites-available/media-kanri
sudo ln -s /etc/nginx/sites-available/media-kanri /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

# iptables（S-Task 4）
bash doc/iptables-setup.sh

# X260上の plantapps サービス（S-Task 5）
sudo cp doc/x260-plantapps-tenken.service /etc/systemd/system/plantapps-tenken.service
sudo systemctl daemon-reload
sudo systemctl enable --now plantapps-tenken
```

---

## 3. Samba 共有設定

`tenken_db` フォルダをWindowsからも参照できるよう、`/etc/samba/smb.conf` に以下を追記します。

```ini
[tenken_db]
   comment = Tenken DB Sync
   path = /opt/media-kanri/tenken_db
   browseable = yes
   read only = yes
   guest ok = yes
   force user = www-data
```

```bash
# Samba インストール・有効化
sudo apt install -y samba
sudo systemctl enable --now smbd
sudo systemctl reload smbd
```

Windowsからは `\\192.168.10.1\tenken_db` でアクセスできます。

---

## 4. トラブルシューティング

| 症状 | 確認方法 | 対処 |
|---|---|---|
| アップロードが失敗する | `sudo systemctl status media-kanri` | サービスが起動しているか確認 |
| 接続できない | `ping 192.168.10.1` | Wi-Fi がX260 APに接続されているか確認 |
| 503 エラー | `sudo nginx -t` | nginx 設定を確認 |
| DB保存ディレクトリがない | `ls /opt/media-kanri/tenken_db/` | `sudo mkdir -p /opt/media-kanri/tenken_db && sudo chown www-data:www-data /opt/media-kanri/tenken_db` |
| バックアップが増えすぎた | `ls /opt/media-kanri/tenken_db/*.bak` | 古い `.bak` ファイルを手動削除 |
| ログ確認 | `journalctl -u media-kanri -f` | エラーメッセージを確認 |
