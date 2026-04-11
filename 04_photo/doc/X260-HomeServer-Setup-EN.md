# ThinkPad X260 Server Setup Guide

A step-by-step guide to installing Ubuntu Server on a ThinkPad X260 and setting up the following services:

- **DHCP Server** (dnsmasq)
- **Wi-Fi Access Point** (hostapd)
- **File Server** (Samba)
- **Python Web App** (Flask + Gunicorn + nginx)

---

## Tested Environment

| Item | Details |
|---|---|
| Hardware | Lenovo ThinkPad X260 |
| Wired NIC | Intel I219-LM |
| Wireless NIC | Intel Dual Band Wireless-AC 8260 |
| OS | Ubuntu Server 24.04 LTS |

---

## Architecture Overview

```
[Internet]
      |
   eth0 (WAN / DHCP from upstream router)
      |
  [ThinkPad X260]
   ├── dnsmasq        → DHCP + DNS (192.168.10.1)
   ├── hostapd        → Wi-Fi AP (wlan0)
   ├── Samba          → File Server
   └── nginx + Gunicorn → Python Web App
      |
   wlan0 (AP) → Client devices (192.168.10.100–200)
```

---

## Step 0: Install Ubuntu Server

### Download the ISO

1. Download `ubuntu-24.04-live-server-amd64.iso` from the [Ubuntu Server official site](https://ubuntu.com/download/server)
2. Write it to a USB drive using [Rufus](https://rufus.ie/) (Windows) or `dd` (Linux/Mac)

```bash
# Linux/Mac example (replace /dev/sdX with your actual USB device)
sudo dd if=ubuntu-24.04-live-server-amd64.iso of=/dev/sdX bs=4M status=progress
sync
```

### Installation Steps

1. Insert the USB drive and power on the X260; press `F12` to open the boot menu
2. Select the USB device to launch the installer
3. Configure language, keyboard, network, and timezone
4. Select "Use entire disk" for storage (optionally enable LVM)
5. Set your username, hostname, and password
6. Check `OpenSSH server` and complete the installation

---

## Step 1: Initial Setup and Package Installation

```bash
# Update the system
sudo apt update && sudo apt upgrade -y

# Install all required packages at once
sudo apt install -y \
  dnsmasq hostapd samba samba-common-bin \
  nginx python3 python3-pip python3-venv \
  net-tools iproute2 iptables-persistent
```

### Check Network Interface Names

```bash
ip link show
```

The following interface names are assumed throughout this guide. Adjust as needed for your environment.

| Role | Interface |
|---|---|
| Wired LAN (WAN) | `eth0` |
| Wireless LAN (AP) | `wlan0` |

---

## Step 2: Network Configuration

### Assign a Static IP to wlan0 (systemd-networkd)

Create `/etc/systemd/network/10-wlan0.network`:

```ini
[Match]
Name=wlan0

[Network]
Address=192.168.10.1/24
```

```bash
sudo systemctl restart systemd-networkd
```

### Netplan Configuration

Edit `/etc/netplan/01-netcfg.yaml` (exclude wlan0 since hostapd manages it):

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

## Step 3: hostapd (Wi-Fi Access Point)

### Verify AP Mode Support

```bash
iw list | grep -A 10 "Supported interface modes"
# Output should include "AP"
```

### Create the Configuration File

Create `/etc/hostapd/hostapd.conf`:

```ini
interface=wlan0
driver=nl80211
ssid=YourSSID              # Change to your preferred Wi-Fi name
hw_mode=g
channel=6
ieee80211n=1
wmm_enabled=1
auth_algs=1
wpa=2
wpa_passphrase=YourPassword    # Use a strong password
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP
```

### Enable the Service

```bash
sudo sed -i 's|#DAEMON_CONF=""|\DAEMON_CONF="/etc/hostapd/hostapd.conf"|' /etc/default/hostapd
sudo systemctl unmask hostapd
sudo systemctl enable --now hostapd
sudo systemctl status hostapd
```

---

## Step 4: dnsmasq (DHCP + DNS)

```bash
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.bak
```

Create `/etc/dnsmasq.conf`:

```ini
interface=wlan0
bind-interfaces

# DHCP range and lease time
dhcp-range=192.168.10.100,192.168.10.200,255.255.255.0,12h

# Set the X260 itself as the gateway and DNS server
dhcp-option=3,192.168.10.1
dhcp-option=6,192.168.10.1

# Upstream DNS servers
server=8.8.8.8
server=8.8.4.4

# Resolve the X260's own hostname
address=/x260.local/192.168.10.1
```

```bash
sudo systemctl enable --now dnsmasq
sudo systemctl status dnsmasq
```

---

## Step 5: IP Masquerading (NAT)

Allow Wi-Fi clients to access the internet through the X260.

```bash
# Enable IP forwarding
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Add NAT rules
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables -A FORWARD -i wlan0 -o eth0 -j ACCEPT
sudo iptables -A FORWARD -i eth0 -o wlan0 -m state --state RELATED,ESTABLISHED -j ACCEPT

# Persist the rules
sudo netfilter-persistent save
```

---

## Step 6: Samba (File Server)

```bash
sudo mkdir -p /srv/share
sudo chmod 777 /srv/share
```

Append the following to `/etc/samba/smb.conf`:

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

Access from Windows: `\\192.168.10.1\Share`  
Access from Linux:

```bash
smbclient //192.168.10.1/Share -N
```

---

## Step 7: Python Web App (Flask + Gunicorn)

### Create the Application

```bash
sudo mkdir -p /opt/webapp
cd /opt/webapp
python3 -m venv venv
source venv/bin/activate
pip install flask gunicorn
```

Create `/opt/webapp/app.py` (sample):

```python
from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "<h1>Home Server</h1>"

if __name__ == "__main__":
    app.run()
```

### Create the systemd Service

Create `/etc/systemd/system/webapp.service`:

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

### Common Issue: `/var/www/.gunicorn` Permission Denied

```
[ERROR] Control server error: [Errno 13] Permission denied: '/var/www/.gunicorn'
```

Fix with either of the following approaches:

**Option A: Create the directory and grant ownership**
```bash
sudo mkdir -p /var/www/.gunicorn
sudo chown -R www-data:www-data /var/www/.gunicorn
```

**Option B: Set `HOME` explicitly in the service file (already included above)**
```ini
Environment="HOME=/opt/webapp"
```

---

## Step 8: nginx (Reverse Proxy)

Create `/etc/nginx/sites-available/webapp`:

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

## Verify Everything Is Working

```bash
# Check all service statuses
sudo systemctl status hostapd dnsmasq smbd webapp nginx

# Check listening ports
sudo ss -tlnp | grep -E '80|8000'

# Test the web app
curl http://127.0.0.1:8000/
curl http://192.168.10.1/
```

---

## Troubleshooting

| Symptom | Command |
|---|---|
| Wi-Fi AP not appearing | `sudo journalctl -u hostapd -f` |
| DHCP not assigning addresses | `sudo journalctl -u dnsmasq -f` |
| Web app returns 502 | `sudo journalctl -u webapp -f` |
| Cannot connect to Samba | `sudo journalctl -u smbd -f` |
| No internet on Wi-Fi clients | `sudo iptables -t nat -L -n -v` |
| Gunicorn fails to start | `sudo journalctl -u webapp -n 50 --no-pager` |

---

## Notes

- Always change `wpa_passphrase` to a strong, unique password before use
- The Samba share with `guest ok = yes` is accessible by any device on the network — configure user authentication if needed
- While `wlan0` is used as an AP, it cannot simultaneously act as a Wi-Fi client
- For long-term operation, clean the fan regularly and consider installing `thermald`

```bash
sudo apt install -y thermald
sudo systemctl enable --now thermald
```

---

## License

MIT
