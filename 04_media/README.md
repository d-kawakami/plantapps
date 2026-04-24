# Media Manager

A lightweight web application for transferring and browsing photos and videos captured on-site at industrial facilities.

[日本語版はこちら / 日本語](README.ja.md)

<img src="doc/images/plantmedia.jpg" width="440" >

---

## Features

- **File Upload**
  - Camera capture and file selection from smartphone
  - Drag & drop support
  - Multi-file simultaneous upload with progress bar
  - API endpoint for uploads from other applications (CORS enabled)

- **File Browser**
  - Thumbnail grid view
  - Filename list view
  - Supports images (JPG, PNG, GIF, BMP, WebP), videos (MP4, MOV, AVI, WebM, M4V), and any other file types

- **Download**
  - Direct download of any file from client devices

- **Delete**
  - Delete files with confirmation dialog

- **Media Viewer**
  - Full-screen image/video viewer with download button

---

## System Architecture

```
Smartphone (Client)
      |
   Wi-Fi AP (hostapd)
      |
   nginx (port 80)  ←→  Flask app (port 5004)
      |
   dnsmasq (DHCP)
```

| Component   | Role                        |
|-------------|-----------------------------|
| hostapd     | Wi-Fi Access Point          |
| dnsmasq     | DHCP server                 |
| nginx       | Reverse proxy (port 80)     |
| Flask       | Web application (port 5004) |

---

## Requirements

- Python 3.10+
- Flask
- Nginx
- hostapd
- dnsmasq

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/d-kawakami/media-kanri.git
cd media-kanri
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install flask
```

### 3. Configure nginx

```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. Configure systemd service

```ini
[Unit]
Description=Plant Media Web App
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/webapp
ExecStart=/opt/webapp/venv/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable webapp
sudo systemctl start webapp
```

### 5. Set upload folder permissions

```bash
sudo chown www-data /opt/webapp/uploads
```

---

## Access

Connect your smartphone to the Wi-Fi AP, then open:

| Page      | URL                          |
|-----------|------------------------------|
| Media manager | `http://192.168.1.250/media` |

> Replace `192.168.1.250` with the IP address of your AP interface.

> **Note:** The URLs above assume nginx is running as a reverse proxy on port 80 (the default HTTP port).
> If you access Flask directly without nginx, append `:5004` to the URL (e.g., `http://192.168.1.250:5004/media`).

---

## Directory Structure

```
/opt/webapp/
├── app.py              # Flask application
├── README.md
├── README.ja.md        # Japanese README
├── doc/                # Documentation and setup guides
├── uploads/            # Uploaded files (www-data writable)
├── templates/
│   └── media.html      # Integrated media manager
└── venv/
```

---

## License

MIT License
