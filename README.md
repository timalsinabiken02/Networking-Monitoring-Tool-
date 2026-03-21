# 🖥️ Network Monitoring Dashboard

**Author:** Biken Timalsina
**Stack:** Python · Flask · psutil · Chart.js
**Live at:** `http://localhost:5000` after setup

---

## Features

| Feature | Description |
|---|---|
| 📊 Real-time Bandwidth | Upload/Download Mbps sampled every 2 seconds |
| 📡 Ping Latency | Pings Google DNS, Cloudflare, OpenDNS every 5 s |
| ⊞ Device Scanner | Reads ARP table to list devices on your LAN |
| ⊟ Interface Monitor | Shows all network interfaces, IPs, MTU, traffic |
| ⚑ Smart Alerts | Auto-fires on high latency, packet loss, unreachable hosts |
| 📈 Historical Charts | 60-datapoint rolling chart for bandwidth and latency |
| 🌙 Dark Dashboard | Professional dark UI with Chart.js line graphs |

---

## Quick Start

### 1. Clone / copy the project
```bash
git clone https://github.com/bikentimalsina/network-monitor
cd network-monitor
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the server
```bash
python app.py
```

### 5. Open the dashboard
Navigate to **http://localhost:5000** in your browser.

---

## Project Structure

```
network-monitor/
│
├── app.py                  # Entry point — creates Flask app, starts threads
├── config.py               # All configurable settings
├── requirements.txt
│
├── monitor/
│   ├── __init__.py
│   ├── network.py          # NetworkMonitor — bandwidth + latency sampling
│   ├── devices.py          # DeviceScanner — ARP table parsing
│   └── alerts.py           # AlertManager — threshold evaluation
│
├── routes/
│   ├── __init__.py
│   ├── main.py             # Serves index.html
│   └── api.py              # REST API endpoints (/api/stats, /api/devices, ...)
│
├── templates/
│   └── index.html          # Single-page dashboard
│
└── static/
    ├── css/style.css
    └── js/dashboard.js     # Chart.js charts + live polling logic
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/stats` | Full snapshot: bandwidth, ping, interfaces, system, alerts |
| GET | `/api/bandwidth` | Current bandwidth (Mbps) |
| GET | `/api/bandwidth/history` | Rolling bandwidth history for charts |
| GET | `/api/ping` | Latest ping results per target |
| GET | `/api/ping/history` | Rolling latency history for charts |
| GET | `/api/interfaces` | All network interfaces |
| GET | `/api/devices` | Devices from ARP table |
| POST | `/api/devices/scan` | Force immediate device scan |
| GET | `/api/alerts` | Full alert log |
| GET | `/api/alerts/active` | Currently active (unresolved) alerts |
| POST | `/api/alerts/{id}/acknowledge` | Acknowledge an alert |
| POST | `/api/alerts/clear` | Clear all alerts |
| GET | `/api/system` | CPU, RAM, hostname |
| GET | `/api/health` | Health check |

---

## Configuration (`config.py`)

| Setting | Default | Description |
|---|---|---|
| `BANDWIDTH_INTERVAL` | `2` | Bandwidth sample rate (seconds) |
| `PING_INTERVAL` | `5` | Ping check interval (seconds) |
| `DEVICE_SCAN_INTERVAL` | `30` | ARP scan interval (seconds) |
| `HISTORY_LENGTH` | `60` | Number of datapoints per chart |
| `PING_TARGETS` | Google / Cloudflare / OpenDNS | Hosts to ping |
| `ALERT_LATENCY_MS` | `150` | Latency warning threshold (ms) |
| `ALERT_PACKET_LOSS` | `20` | Packet loss warning threshold (%) |
| `ALERT_BANDWIDTH_MBPS` | `90` | Bandwidth warning threshold (Mbps) |

---

## Notes

- **Root/Admin not required** — uses the OS ARP cache (`arp -a`) for device discovery.
- **Cross-platform** — tested on Windows, Linux, and macOS. Ping commands adjust automatically.
- **No database** — all data is kept in memory (rolling window). Restart clears history.
- For deeper device scanning (active ARP probing), you can extend `devices.py` with `scapy`.

---

## Technologies

- **Flask** — lightweight Python web framework
- **psutil** — cross-platform system/network stats
- **Chart.js** — beautiful, animated line charts (loaded from CDN)
- **Bootstrap-free** — fully custom dark CSS, no heavy dependencies

---

*Built with ♡ by Biken Timalsina — Nepal*
