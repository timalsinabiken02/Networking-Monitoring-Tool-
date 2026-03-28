# Network Monitoring Dashboard

A Python dashboard I built to keep an eye on my home network in real time — bandwidth, ping, connected devices, and alerts, all in one place.

**Stack:** Python · Flask · psutil · Chart.js  
**Run it:** `http://localhost:5000` after setup

---

## What it does

- Tracks upload/download speed in Mbps, sampled every 2 seconds
- Pings Google DNS, Cloudflare, and OpenDNS every 5 seconds to monitor latency
- Reads your ARP table to show devices currently on your LAN
- Lists all network interfaces with IPs, MTU, and traffic stats
- Fires alerts automatically when latency spikes, packet loss is high, or a host goes unreachable
- Keeps a 60-point rolling history for bandwidth and latency charts
- Dark UI built with Chart.js — no Bootstrap, just custom CSS

---

## Getting started
```bash
# Clone the repo
git clone https://github.com/bikentimalsina/network-monitor
cd network-monitor

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Start the server
python app.py
```

Then open **http://localhost:5000** in your browser.

---

## Project structure
```
network-monitor/
│
├── app.py                  # Entry point — creates Flask app, starts threads
├── config.py               # All configurable settings
├── requirements.txt
│
├── monitor/
│   ├── network.py          # Bandwidth + latency sampling
│   ├── devices.py          # ARP table parsing
│   └── alerts.py           # Threshold-based alert logic
│
├── routes/
│   ├── main.py             # Serves index.html
│   └── api.py              # REST API endpoints
│
├── templates/
│   └── index.html          # Single-page dashboard
│
└── static/
    ├── css/style.css
    └── js/dashboard.js     # Chart.js + polling logic
```

---

## API endpoints

| Method | Endpoint | What it returns |
|--------|----------|-----------------|
| GET | `/api/stats` | Full snapshot: bandwidth, ping, interfaces, system, alerts |
| GET | `/api/bandwidth` | Current bandwidth (Mbps) |
| GET | `/api/bandwidth/history` | Rolling bandwidth history |
| GET | `/api/ping` | Latest ping results per target |
| GET | `/api/ping/history` | Rolling latency history |
| GET | `/api/interfaces` | All network interfaces |
| GET | `/api/devices` | Devices from ARP table |
| POST | `/api/devices/scan` | Force an immediate device scan |
| GET | `/api/alerts` | Full alert log |
| GET | `/api/alerts/active` | Active (unresolved) alerts only |
| POST | `/api/alerts/{id}/acknowledge` | Acknowledge an alert |
| POST | `/api/alerts/clear` | Clear all alerts |
| GET | `/api/system` | CPU, RAM, hostname |
| GET | `/api/health` | Health check |

---

## Configuration

All settings live in `config.py`. Key ones to know:

| Setting | Default | What it controls |
|---------|---------|-----------------|
| `BANDWIDTH_INTERVAL` | `2s` | How often bandwidth is sampled |
| `PING_INTERVAL` | `5s` | How often ping checks run |
| `DEVICE_SCAN_INTERVAL` | `30s` | ARP scan frequency |
| `HISTORY_LENGTH` | `60` | Datapoints kept per chart |
| `PING_TARGETS` | Google / Cloudflare / OpenDNS | Hosts to monitor |
| `ALERT_LATENCY_MS` | `150ms` | Latency warning threshold |
| `ALERT_PACKET_LOSS` | `20%` | Packet loss warning threshold |
| `ALERT_BANDWIDTH_MBPS` | `90 Mbps` | Bandwidth spike threshold |

---

## A few things worth knowing

**No root/admin needed.** Device discovery reads the OS ARP cache (`arp -a`), so no elevated permissions required.

**Cross-platform.** Tested on Windows, Linux, and macOS. Ping commands adjust automatically per OS.

**No database.** Everything is in memory as a rolling window. Restart the server and history clears.

If you want active ARP probing instead of just reading the cache, `devices.py` is the place to extend — `scapy` works well for that.

---

## Built with

- **Flask** — lightweight Python web framework
- **psutil** — cross-platform system and network stats
- **Chart.js** — animated line charts, loaded from CDN
- Custom dark CSS — no heavy UI frameworks

---

*Built by Biken Timalsina*
