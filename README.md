# Plant Apps

An integrated suite of four web applications designed for plant engineers working at industrial facilities.
Each app works independently but gains additional value when used together through shared navigation and cross-app data links.

**Repository:** https://github.com/d-kawakami/plantapps

[日本語版はこちら → README.ja.md](README.ja.md)

---

## Applications at a Glance

| # | App | Port | Description |
|---|-----|------|-------------|
| 01 | **Daily Inspection** | `5001` | Record daily equipment checks by day of the week |
| 02 | **Equipment Register** | `5002` | Master database for all facility equipment |
| 03 | **Handover Notes** | `5003` | Shift handover log with keyword search and TTS |
| 04 | **Photo Manager** | `5004` | Upload and browse on-site photos and videos |

All four apps share a **fixed bottom navigation bar** so you can switch between them instantly from any screen on a mobile device.

---

## Cross-App Integration

```
┌──────────────────────────────────────────────┐
│  Header  (app title + context actions)        │
├──────────────────────────────────────────────┤
│                                              │
│  Main Content                                │
│                                              │
│  ┌────────────────────────────────────┐      │
│  │ Context Link                       │      │
│  │ e.g. "Check equipment register →" │      │
│  └────────────────────────────────────┘      │
│                                              │
├──────────────────────────────────────────────┤
│  Bottom Tab Bar                              │
│  [Handover] [Equipment] [Inspection] [Photo] │
└──────────────────────────────────────────────┘
```

### Shared Components (`common_templates/`)

| File | Purpose |
|------|---------|
| `bottom_nav.html` | Fixed bottom navigation bar (Jinja2 include) |
| `context_link.html` | In-page card links to related apps |

### Cross-App API Endpoints

| App | Endpoint | Used by |
|-----|----------|---------|
| Equipment Register | `GET /api/equipment/search?name=<keyword>` | Handover Notes, Inspection (CORS-enabled) |
| Photo Manager | `POST /api/upload` | Inspection — saves on-site photos directly to Photo Manager (CORS-enabled) |

---

## Requirements

- Python 3.10 or higher
- pip

Install dependencies for each app:

```bash
pip install -r 01_tenken/requirements.txt
pip install -r 02_daicho/requirements.txt
pip install flask openpyxl          # 03_note
pip install flask                   # 04_photo
```

Or install everything at once if you have a combined `requirements.txt`:

```bash
pip install flask openpyxl chardet
```

---

## Quick Start — All Apps Together

### Windows

Double-click `start_all.bat`, or run from a terminal:

```bat
start_all.bat
```

Each app opens in its own Command Prompt window.

### Linux / macOS / Termux (Android)

```bash
bash start_all.sh
```

All four apps run in the background. Press `Ctrl+C` to stop all of them.

---

## Quick Start — Individual Apps

### 01 Daily Inspection (port 5001)

```bash
cd 01_tenken
python app.py
```

Open `http://localhost:5001` in your browser.

### 02 Equipment Register (port 5002)

```bash
cd 02_daicho
python app.py
```

Open `http://localhost:5002` in your browser.

### 03 Handover Notes (port 5003)

```bash
cd 03_note
python app.py
```

Open `http://localhost:5003` in your browser.

### 04 Photo Manager (port 5004)

```bash
cd 04_photo
python app.py
```

Open `http://localhost:5004/photo` in your browser.

---

## Accessing from Mobile Devices (LAN)

All apps bind to `0.0.0.0`, so any device on the same Wi-Fi network can connect.
Replace `localhost` with the server's IP address:

```
http://192.168.1.xxx:5001    ← Daily Inspection
http://192.168.1.xxx:5002    ← Equipment Register
http://192.168.1.xxx:5003    ← Handover Notes
http://192.168.1.xxx:5004    ← Photo Manager
```

The bottom navigation bar automatically detects the hostname and constructs the correct URLs for all tabs.

---

## Repository Structure

```
plantapps/
├── README.md               ← This file (English)
├── README.ja.md            ← Japanese version
├── start_all.bat           ← Launch all apps (Windows)
├── start_all.sh            ← Launch all apps (Linux/macOS)
│
├── common_templates/       ← Shared Jinja2 components
│   ├── bottom_nav.html     ← Bottom navigation bar
│   └── context_link.html   ← Cross-app context link cards
│
├── 01_tenken/              ← Daily Inspection app
│   ├── app.py              ← Flask app (port 5001)
│   ├── database.py
│   ├── models.py
│   ├── templates/
│   └── static/
│
├── 02_daicho/              ← Equipment Register app
│   ├── app.py              ← Flask app (port 5002)
│   ├── database.py
│   ├── models.py
│   └── templates/
│
├── 03_note/                ← Handover Notes app
│   ├── app.py              ← Flask app (port 5003)
│   └── templates/
│
└── 04_photo/               ← Photo Manager app
    ├── app.py              ← Flask app (port 5004)
    ├── uploads/            ← Uploaded files
    └── templates/
```

---

## App Details

### 01 Daily Inspection

- Select the day of the week (Mon–Fri) and record pass/fail/caution results for each inspection item
- Wednesday supports week-number filtering (Week 1–4)
- Offline-capable PWA — results are saved locally and synced when back online
- Voice input via Web Speech API (hands-free operation)
- Excel export and import of inspection master data
- **Context links**: Jump to Equipment Register to look up the equipment being inspected, or send an inspection photo directly to Photo Manager

### 02 Equipment Register

- Search and manage all facility equipment (name, location, category, status, manufacturer, etc.)
- Record measurement history per equipment
- CSV import (auto-detects Shift-JIS / UTF-8) and export
- Dashboard with aging analysis
- **Cross-app API**: `GET /api/equipment/search?name=<keyword>` — CORS-enabled, callable from any of the other three apps

### 03 Handover Notes

- Record shift handover entries (date, shift, category, time, content, recorder)
- Full-text keyword search with synonym expansion and relevance ranking
- Japanese TTS playback via VOICEVOX (optional — runs locally, no API cost)
- Bulk import from Excel (.xlsx)
- **Context links**: Open Equipment Register to look up equipment mentioned in a note

### 04 Photo Manager

- Upload photos and videos from smartphones via browser or drag & drop
- Thumbnail grid and filename list views
- Full-screen viewer with download button
- **Cross-app API**: `POST /api/upload` — CORS-enabled, lets the Inspection app save on-site photos directly here

---

## Bottom Navigation Bar

The shared `bottom_nav.html` component provides:

- **Fixed positioning** — always visible, even when scrolling
- **Active tab highlight** — the current app's tab is shown in blue with a top indicator bar
- **Icons** (lucide-compatible inline SVG):
  - Handover Notes: ClipboardList
  - Equipment Register: Database
  - Daily Inspection: CheckSquare
  - Photo Manager: Image
- **44 px minimum tap target** (mobile-friendly)
- **Safe area support** — respects iOS notch/home indicator via `env(safe-area-inset-bottom)`
- **Dynamic URLs** — uses `window.location.hostname` so the same code works on any IP address

---

## License

MIT License — see individual app directories for details.
