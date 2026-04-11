# ThinkPad X260 サーバー構築ガイド

ThinkPad X260 に Ubuntu Server をインストールし、以下のサービスをまとめて構築する手順です。

- **DHCPサーバー** (dnsmasq)
- **Wi-Fi アクセスポイント** (hostapd)
- **ファイルサーバー** (Samba)
- **Python Webアプリ** (Flask + Gunicorn + nginx)

---

## 動作確認環境

| 項目 | 内容 |
|---|---|
| ハードウェア | Lenovo ThinkPad X260 |
| 有線LAN | Intel I219-LM |
| 無線LAN | Intel Dual Band Wireless-AC 8260 |
| OS | Ubuntu Server 24.04 LTS |

---

## 全体構成

```
[インターネット]
      |
   eth0 (WAN / 上位ルーターからDHCP取得)
      |
  [ThinkPad X260]
   ├── dnsmasq        → DHCP + DNS (192.168.10.1)
   ├── hostapd        → Wi-Fi AP (wlan0)
   ├── Samba          → ファイルサーバー
   └── nginx + Gunicorn → Python Webアプリ
      |
   wlan0 (AP) → クライアント端末 (192.168.10.100〜200)
```

---

## ステップ 0: Ubuntu Server のインストール

### ISOダウンロード

1. [Ubuntu Server 公式サイト](https://ubuntu.com/download/server) から `ubuntu-24.04-live-server-amd64.iso` をダウンロード
2. [Rufus](https://rufus.ie/)（Windows）または `dd` コマンド（Linux/Mac）でUSBに書き込む

```bash
# Linux/Mac での書き込み例（/dev/sdX は実際のUSBデバイス名に変更）
sudo dd if=ubuntu-24.04-live-server-amd64.iso of=/dev/sdX bs=4M status=progress
sync
```

### インストール手順

1. USBを挿してX260を起動し、`F12` でブートメニューを開く
2. USBデバイスを選択してインストーラーを起動
3. 言語・キーボード・ネットワーク・タイムゾーンを設定
4. ストレージは「Use entire disk」を選択（必要に応じてLVMも選択可）
5. ユーザー名・ホスト名・パスワードを設定
6. `OpenSSH server` にチェックを入れてインストール完了

---

## ステップ 1: 初期設定とパッケージインストール

```bash
# システム更新
sudo apt update && sudo apt upgrade -y

# 必要パッケージを一括インストール
sudo apt install -y \
  dnsmasq hostapd samba samba-common-bin \
  nginx python3 python3-pip python3-venv \
  net-tools iproute2 iptables-persistent
```

### ネットワークインターフェース名の確認

```bash
ip link show
```

以降の手順では以下の名前を前提にしています。環境に合わせて読み替えてください。

| 用途 | インターフェース名 |
|---|---|
| 有線LAN (WAN) | `eth0` |
| 無線LAN (AP) | `wlan0` |

---

## ステップ 2: ネットワーク設定

### wlan0 に固定IPを設定（systemd-networkd）

`/etc/systemd/network/10-wlan0.network` を作成します。

```ini
[Match]
Name=wlan0

[Network]
Address=192.168.10.1/24
```

```bash
sudo systemctl restart systemd-networkd
```

### /etc/netplan の設定

`/etc/netplan/01-netcfg.yaml` を編集します（wlan0 はhostapdが管理するため除外）。

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:
      dhcp4: true
```

```bash
sudo netplan apply
```

---

## ステップ 3: hostapd（Wi-Fi アクセスポイント）

### APモード対応確認

```bash
iw list | grep -A 10 "Supported interface modes"
# 出力に "AP" が含まれていればOK
```

### 設定ファイルの作成

`/etc/hostapd/hostapd.conf` を作成します。

```ini
interface=wlan0
driver=nl80211
ssid=YourSSID              # Wi-Fi名を変更してください
hw_mode=g
channel=6
ieee80211n=1
wmm_enabled=1
auth_algs=1
wpa=2
wpa_passphrase=YourPassword    # 十分に強いパスワードに変更してください
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
```

### 有効化

```bash
sudo sed -i 's|#DAEMON_CONF=""|\DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd
sudo systemctl unmask hostapd
sudo systemctl enable --now hostapd
sudo systemctl status hostapd
```

---

## ステップ 4: dnsmasq（DHCP + DNS）

```bash
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.bak
```

`/etc/dnsmasq.conf` を作成します。

```ini
interface=wlan0
bind-interfaces

# DHCPの割り当て範囲とリース時間
dhcp-range=192.168.10.100,192.168.10.200,255.255.255.0,12h

# ゲートウェイ・DNSをX260自身に設定
dhcp-option=3,192.168.10.1
dhcp-option=6,192.168.10.1

# 上位DNS
server=8.8.8.8
server=8.8.4.4

# X260自身のホスト名
address=/x260.local/192.168.10.1
```

```bash
sudo systemctl enable --now dnsmasq
sudo systemctl status dnsmasq
```

---

## ステップ 5: IPマスカレード（NAT）

Wi-Fiクライアントがインターネットに出られるようにします。

```bash
# IPフォワーディングを有効化
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# NATルールを追加
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT
sudo iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT

# ルールを永続化
sudo netfilter-persistent save
```

---

## ステップ 6: Samba（ファイルサーバー）

```bash
sudo mkdir -p /srv/share
sudo chmod 777 /srv/share
```

`/etc/samba/smb.conf` の末尾に追記します。

```ini
[Share]
   comment = File Share
   path = /srv/share
   browseable = yes
   read only = no
   guest ok = yes
   create mask = 0664
   directory mask = 0775
```

```bash
sudo systemctl enable --now smbd nmbd
sudo systemctl status smbd
```

Windowsからは `\\192.168.10.1\Share` でアクセスできます。  
Linuxからは以下でアクセスできます。

```bash
smbclient //192.168.10.1/Share -N
```

---

## ステップ 7: Python Webアプリ（Flask + Gunicorn）

### アプリの作成

```bash
sudo mkdir -p /opt/webapp
cd /opt/webapp
python3 -m venv venv
source venv/bin/activate
pip install flask gunicorn
```

`/opt/webapp/app.py` を作成します（サンプル）。

```python
from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "<h1>Home Server</h1>"

if __name__ == "__main__":
    app.run()
```

### systemd サービスの設定

`/etc/systemd/system/webapp.service` を作成します。

```ini
[Unit]
Description=Python Web App
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/webapp
Environment="HOME=/opt/webapp"
ExecStart=/opt/webapp/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now webapp
sudo systemctl status webapp
```

### よくあるトラブル: `/var/www/.gunicorn` パーミッションエラー

```
[ERROR] Control server error: [Errno 13] Permission denied: '/var/www/.gunicorn'
```

このエラーが出た場合は以下のどちらかで対処します。

**方法A: ディレクトリを作成して権限を付与**
```bash
sudo mkdir -p /var/www/.gunicorn
sudo chown -R www-data:www-data /var/www/.gunicorn
```

**方法B: サービスに `HOME` を明示する（上記サービスファイルに記載済み）**
```ini
Environment="HOME=/opt/webapp"
```

---

## ステップ 8: nginx（リバースプロキシ）

`/etc/nginx/sites-available/webapp` を作成します。

```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/webapp /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable --now nginx
```

---

## 動作確認

```bash
# 全サービスの状態確認
sudo systemctl status hostapd dnsmasq smbd webapp nginx

# ポートの確認
sudo ss -tlnp | grep -E '80|8000'

# Webアプリの疎通確認
curl http://127.0.0.1:8000/
curl http://192.168.10.1/
```

---

## トラブルシュート

| 症状 | 確認コマンド |
|---|---|
| Wi-Fiが出ない | `sudo journalctl -u hostapd -f` |
| DHCPが配れない | `sudo journalctl -u dnsmasq -f` |
| Webアプリ502エラー | `sudo journalctl -u webapp -f` |
| Sambaに繋がらない | `sudo journalctl -u smbd -f` |
| インターネット不通 | `sudo iptables -t nat -L -n -v` |
| gunicornが起動しない | `sudo journalctl -u webapp -n 50 --no-pager` |

---

## 注意事項

- `wpa_passphrase` は必ず強いパスワードに変更してください
- `guest ok = yes` のSamba共有はネットワーク内のすべての端末からアクセスできます。必要に応じてユーザー認証を設定してください
- `wlan0` をAPとして使用中は、同じNICでWi-Fiクライアントにはなれません
- 長期運用時はファンの清掃と `thermald` の導入を推奨します

```bash
sudo apt install -y thermald
sudo systemctl enable --now thermald
```

---

## ライセンス

MIT
