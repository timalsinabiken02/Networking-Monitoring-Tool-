"""
network.py — Core network monitoring engine.
Continuously samples bandwidth, latency, and interface statistics
using psutil. Stores a rolling history window for charting.
"""

import time
import platform
import subprocess
import threading
import psutil
from collections import deque
from datetime import datetime
from config import Config


def _ping(host: str, count: int = 3) -> dict:
    """
    Ping a host and return latency + packet-loss stats.
    Works cross-platform (Windows / Linux / macOS).
    """
    system = platform.system().lower()
    if system == "windows":
        cmd = ["ping", "-n", str(count), "-w", "2000", host]
    else:
        cmd = ["ping", "-c", str(count), "-W", "2", host]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=count * 3 + 2,
        )
        output = result.stdout + result.stderr

        # --- Parse average latency ---
        latency = None
        if system == "windows":
            for line in output.splitlines():
                if "Average" in line or "average" in line:
                    parts = line.split("=")
                    if len(parts) >= 2:
                        latency_str = parts[-1].strip().replace("ms", "").strip()
                        try:
                            latency = float(latency_str)
                        except ValueError:
                            pass
        else:
            for line in output.splitlines():
                if "avg" in line or "rtt" in line:
                    parts = line.split("/")
                    if len(parts) >= 5:
                        try:
                            latency = float(parts[4])
                        except (ValueError, IndexError):
                            pass

        # --- Parse packet loss ---
        packet_loss = 0.0
        for line in output.splitlines():
            if "%" in line and ("loss" in line.lower() or "lost" in line.lower()):
                for token in line.split():
                    if "%" in token:
                        try:
                            packet_loss = float(token.replace("%", "").replace("(", ""))
                        except ValueError:
                            pass

        reachable = result.returncode == 0 and latency is not None
        return {
            "host":        host,
            "reachable":   reachable,
            "latency_ms":  round(latency, 2) if latency is not None else None,
            "packet_loss": packet_loss,
        }

    except subprocess.TimeoutExpired:
        return {"host": host, "reachable": False, "latency_ms": None, "packet_loss": 100.0}
    except Exception as e:
        return {"host": host, "reachable": False, "latency_ms": None, "packet_loss": 100.0, "error": str(e)}


class NetworkMonitor:
    """
    Runs two background threads:
      1. Bandwidth sampler  — updates every BANDWIDTH_INTERVAL seconds
      2. Ping sampler       — updates every PING_INTERVAL seconds
    Stores rolling history for the dashboard charts.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._running = False

        # Rolling history deques
        self._bw_history     = deque(maxlen=Config.HISTORY_LENGTH)
        self._ping_history   = {name: deque(maxlen=Config.HISTORY_LENGTH) for name in Config.PING_TARGETS}
        self._timestamps_bw  = deque(maxlen=Config.HISTORY_LENGTH)
        self._timestamps_ping = deque(maxlen=Config.HISTORY_LENGTH)

        # Latest snapshots
        self._latest_bandwidth  = {}
        self._latest_ping       = {}
        self._latest_interfaces = []
        self._latest_system     = {}

        # Track previous io counters for delta calculation
        self._prev_io    = None
        self._prev_time  = None

    # ─── Public API ──────────────────────────────────────────────────────────

    def start_monitoring(self):
        """Start all background monitoring threads. Call once."""
        self._running = True
        bw_thread   = threading.Thread(target=self._bandwidth_loop,  daemon=True)
        ping_thread = threading.Thread(target=self._ping_loop,       daemon=True)
        bw_thread.start()
        ping_thread.start()

    def stop(self):
        self._running = False

    def get_bandwidth(self) -> dict:
        with self._lock:
            return dict(self._latest_bandwidth)

    def get_bandwidth_history(self) -> dict:
        with self._lock:
            return {
                "timestamps": list(self._timestamps_bw),
                "download":   [p.get("download_mbps", 0) for p in self._bw_history],
                "upload":     [p.get("upload_mbps", 0)   for p in self._bw_history],
            }

    def get_ping(self) -> dict:
        with self._lock:
            return dict(self._latest_ping)

    def get_ping_history(self) -> dict:
        with self._lock:
            return {
                "timestamps": list(self._timestamps_ping),
                "targets": {
                    name: [p.get("latency_ms") for p in hist]
                    for name, hist in self._ping_history.items()
                },
            }

    def get_interfaces(self) -> list:
        with self._lock:
            return list(self._latest_interfaces)

    def get_system_info(self) -> dict:
        with self._lock:
            return dict(self._latest_system)

    def get_all(self) -> dict:
        """Return everything in a single dict for the dashboard."""
        with self._lock:
            return {
                "bandwidth":          dict(self._latest_bandwidth),
                "bandwidth_history":  {
                    "timestamps": list(self._timestamps_bw),
                    "download":   [p.get("download_mbps", 0) for p in self._bw_history],
                    "upload":     [p.get("upload_mbps", 0)   for p in self._bw_history],
                },
                "ping":               dict(self._latest_ping),
                "ping_history":       {
                    "timestamps": list(self._timestamps_ping),
                    "targets": {
                        name: [p.get("latency_ms") for p in hist]
                        for name, hist in self._ping_history.items()
                    },
                },
                "interfaces":         list(self._latest_interfaces),
                "system":             dict(self._latest_system),
                "server_time":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

    # ─── Private loops ───────────────────────────────────────────────────────

    def _bandwidth_loop(self):
        """Sample bandwidth and interfaces every BANDWIDTH_INTERVAL seconds."""
        while self._running:
            try:
                self._sample_bandwidth()
                self._sample_interfaces()
                self._sample_system()
            except Exception:
                pass
            time.sleep(Config.BANDWIDTH_INTERVAL)

    def _ping_loop(self):
        """Ping all targets every PING_INTERVAL seconds."""
        while self._running:
            try:
                results = {}
                ts = datetime.now().strftime("%H:%M:%S")
                for name, host in Config.PING_TARGETS.items():
                    r = _ping(host)
                    results[name] = r
                    with self._lock:
                        self._ping_history[name].append(r)

                with self._lock:
                    self._latest_ping = results
                    self._timestamps_ping.append(ts)
            except Exception:
                pass
            time.sleep(Config.PING_INTERVAL)

    def _sample_bandwidth(self):
        """Calculate upload/download Mbps since last sample."""
        io = psutil.net_io_counters()
        now = time.time()

        if self._prev_io is not None:
            elapsed = now - self._prev_time
            if elapsed > 0:
                bytes_sent     = io.bytes_sent     - self._prev_io.bytes_sent
                bytes_recv     = io.bytes_recv     - self._prev_io.bytes_recv
                upload_mbps    = round((bytes_sent  / elapsed) / 1_000_000 * 8, 4)
                download_mbps  = round((bytes_recv  / elapsed) / 1_000_000 * 8, 4)
                ts = datetime.now().strftime("%H:%M:%S")

                snap = {
                    "upload_mbps":   upload_mbps,
                    "download_mbps": download_mbps,
                    "bytes_sent_total":  io.bytes_sent,
                    "bytes_recv_total":  io.bytes_recv,
                    "packets_sent":      io.packets_sent,
                    "packets_recv":      io.packets_recv,
                    "errors_in":         io.errin,
                    "errors_out":        io.errout,
                    "drop_in":           io.dropin,
                    "drop_out":          io.dropout,
                }

                with self._lock:
                    self._latest_bandwidth = snap
                    self._bw_history.append(snap)
                    self._timestamps_bw.append(ts)

        self._prev_io   = io
        self._prev_time = now

    def _sample_interfaces(self):
        """Collect per-interface stats and addresses."""
        addrs   = psutil.net_if_addrs()
        stats   = psutil.net_if_stats()
        io_per  = psutil.net_io_counters(pernic=True)

        interfaces = []
        for name in addrs:
            stat = stats.get(name)
            io   = io_per.get(name)
            addr_list = []
            for a in addrs[name]:
                if a.family.name in ("AF_INET", "AF_INET6"):
                    addr_list.append({"family": a.family.name, "address": a.address, "netmask": a.netmask})

            interfaces.append({
                "name":     name,
                "is_up":    stat.isup if stat else False,
                "speed":    stat.speed if stat else 0,
                "mtu":      stat.mtu if stat else 0,
                "addresses": addr_list,
                "bytes_sent": io.bytes_sent if io else 0,
                "bytes_recv": io.bytes_recv if io else 0,
            })

        with self._lock:
            self._latest_interfaces = interfaces

    def _sample_system(self):
        """Collect CPU, RAM, and general system info."""
        mem = psutil.virtual_memory()
        with self._lock:
            self._latest_system = {
                "cpu_percent":    psutil.cpu_percent(interval=0.5),
                "cpu_count":      psutil.cpu_count(),
                "ram_total_gb":   round(mem.total     / 1e9, 2),
                "ram_used_gb":    round(mem.used      / 1e9, 2),
                "ram_percent":    mem.percent,
                "platform":       platform.system(),
                "hostname":       platform.node(),
            }
