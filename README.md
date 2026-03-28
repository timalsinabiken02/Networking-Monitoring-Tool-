# Network Monitoring Dashboard

A real-time network monitoring tool for your home or local network — bandwidth, ping, connected devices, alerts, and packet stats all in one dark-themed web dashboard.

**Stack:** Python · Flask · psutil · Chart.js
**Default URL:** `http://localhost:8080`

---

## Features

**Live Metrics (auto-refreshes every 2s)**
- Upload & download speed in Mbps
- CPU usage and RAM consumption
- Total bytes sent / received since boot
- Packet errors and drop counters

**Charts**
- Rolling bandwidth history (upload + download)
- Ping latency history for all targets

**Network Interfaces**
- Lists every interface with status (up/down), speed, MTU, and IP addresses

**Connected Devices**
- Reads the OS ARP cache to show devices on your LAN
- Search / filter by IP, MAC, hostname, or type
- Force an immediate re-scan with one click
- Export device list as CSV

**Alerts**
- Fires automatically when latency, packet loss, or bandwidth cross thresholds
- Active alerts tab + full history tab
- Dismiss individual alerts or clear all
- Browser push notifications for new alerts (opt-in)

**Dashboard Controls**
- Pause / Resume live polling
- Light / Dark theme toggle (preference saved)
- Offline banner when the server is unreachable
- Configurable thresholds and ping targets (saved to localStorage)
- Uptime counter

---

## Getting started

```bash
# Clone the repo
git clone https://github.com/bikentimalsina/Networking-Monitoring-Tool-
cd Networking-Monitoring-Tool-

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

Then open **http://localhost:8080** in your browser.

---

## Project structure

```
Networking-Monitoring-Tool-/
│
├── app.py                  # Entry point — creates Flask app, starts threads
├── config.py               # All configurable settings
├── requirements.txt
├── .gitignore
│
├── monitor/
│   ├── __init__.py
│   ├── network.py          # Bandwidth + latency sampling
│   ├── devices.py          # ARP table parsing + device scanning
│   └── alerts.py           # Threshold-based alert logic
│
├── routes/
│   ├── __init__.py
│   ├── main.py             # Serves the dashboard HTML
│   └── api.py              # REST API endpoints
│
└── templates/
    └── index.html          # Single-page dashboard (charts, tables, controls)
```

---

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/stats` | Full snapshot: bandwidth, ping, interfaces, system, alerts |
| GET | `/api/bandwidth` | Current bandwidth (Mbps) |
| GET | `/api/bandwidth/history` | Rolling bandwidth history |
| GET | `/api/ping` | Latest ping results per target |
| GET | `/api/ping/history` | Rolling latency history |
| GET | `/api/interfaces` | All network interfaces |
| GET | `/api/devices` | Devices from ARP table |
| POST | `/api/devices/scan` | Force an immediate device scan |
| GET | `/api/alerts` | Full alert log (active + resolved) |
| GET | `/api/alerts/active` | Active alerts only |
| POST | `/api/alerts/{id}/acknowledge` | Dismiss an alert |
| POST | `/api/alerts/clear` | Clear all alerts |
| GET | `/api/system` | CPU, RAM, hostname, platform |
| GET | `/api/health` | Health check |

---

## Configuration

Settings in `config.py` can be overridden with environment variables:

| Setting | Default | Description |
|---------|---------|-------------|
| `PORT` | `8080` | Server port |
| `HOST` | `0.0.0.0` | Bind address |
| `DEBUG` | `false` | Flask debug mode |
| `SECRET_KEY` | — | Set via env var in production |
| `BANDWIDTH_INTERVAL` | `2s` | Bandwidth sample rate |
| `PING_INTERVAL` | `5s` | Ping check frequency |
| `DEVICE_SCAN_INTERVAL` | `30s` | ARP scan frequency |
| `HISTORY_LENGTH` | `60` | Datapoints kept per chart |
| `PING_TARGETS` | Google / Cloudflare / OpenDNS | Hosts to monitor |
| `ALERT_LATENCY_MS` | `150` | Latency warning threshold (ms) |
| `ALERT_PACKET_LOSS` | `20` | Packet loss warning threshold (%) |
| `ALERT_BANDWIDTH_MBPS` | `90` | Bandwidth spike threshold (Mbps) |

---

## Notes

**No root/admin needed.** Device discovery reads the OS ARP cache (`arp -a`) — no elevated permissions required.

**Cross-platform.** Tested on Windows, Linux, and macOS. Ping commands adjust per OS automatically.

**No database.** All data is kept in memory as rolling windows. History clears on server restart.

---

## Built with

- **Flask** — lightweight Python web framework
- **psutil** — cross-platform system and network stats
- **Chart.js** — animated line charts via CDN
- Vanilla HTML/CSS/JS — no heavy frontend frameworks

---

*Built by Biken Timalsina*
