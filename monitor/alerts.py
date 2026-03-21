"""
alerts.py — Evaluates current metrics against thresholds and
maintains a rolling log of active/resolved alerts.
"""

import threading
from collections import deque
from datetime import datetime
from config import Config

SEVERITY = {"info": 0, "warning": 1, "critical": 2}


class Alert:
    def __init__(self, alert_id: str, severity: str, title: str, message: str):
        self.id        = alert_id
        self.severity  = severity
        self.title     = title
        self.message   = message
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.resolved  = False

    def to_dict(self) -> dict:
        return {
            "id":        self.id,
            "severity":  self.severity,
            "title":     self.title,
            "message":   self.message,
            "timestamp": self.timestamp,
            "resolved":  self.resolved,
        }


class AlertManager:
    """
    Evaluates metrics snapshots and fires alerts when thresholds are crossed.
    Maintains a deque of the last 50 alerts (active + resolved).
    """

    def __init__(self):
        self._lock   = threading.Lock()
        self._alerts = deque(maxlen=50)
        self._active = {}   # alert_id -> Alert (currently active)

    # ─── Public API ──────────────────────────────────────────────────────────

    def evaluate(self, bandwidth: dict, ping: dict) -> list:
        """
        Call this with the latest metrics snapshot.
        Returns list of newly fired alert dicts.
        """
        new_alerts = []

        # 1. High download bandwidth
        dl = bandwidth.get("download_mbps", 0)
        if dl > Config.ALERT_BANDWIDTH_MBPS:
            a = self._fire(
                "high_download",
                "warning",
                "High Download Bandwidth",
                f"Download is {dl:.2f} Mbps — above threshold ({Config.ALERT_BANDWIDTH_MBPS} Mbps).",
            )
            if a:
                new_alerts.append(a)
        else:
            self._resolve("high_download")

        # 2. High upload bandwidth
        ul = bandwidth.get("upload_mbps", 0)
        if ul > Config.ALERT_BANDWIDTH_MBPS:
            a = self._fire(
                "high_upload",
                "warning",
                "High Upload Bandwidth",
                f"Upload is {ul:.2f} Mbps — above threshold ({Config.ALERT_BANDWIDTH_MBPS} Mbps).",
            )
            if a:
                new_alerts.append(a)
        else:
            self._resolve("high_upload")

        # 3. Ping latency & packet loss per target
        for name, result in ping.items():
            key_lat  = f"latency_{name}"
            key_loss = f"loss_{name}"

            lat = result.get("latency_ms")
            if lat is not None and lat > Config.ALERT_LATENCY_MS:
                a = self._fire(
                    key_lat,
                    "warning",
                    f"High Latency — {name}",
                    f"Ping to {result['host']} is {lat} ms (threshold: {Config.ALERT_LATENCY_MS} ms).",
                )
                if a:
                    new_alerts.append(a)
            else:
                self._resolve(key_lat)

            loss = result.get("packet_loss", 0)
            if loss >= Config.ALERT_PACKET_LOSS:
                severity = "critical" if loss >= 50 else "warning"
                a = self._fire(
                    key_loss,
                    severity,
                    f"Packet Loss — {name}",
                    f"{loss:.0f}% packet loss to {result['host']}.",
                )
                if a:
                    new_alerts.append(a)
            else:
                self._resolve(key_loss)

            # 4. Host unreachable
            key_reach = f"unreachable_{name}"
            if not result.get("reachable", True):
                a = self._fire(
                    key_reach,
                    "critical",
                    f"Host Unreachable — {name}",
                    f"Cannot reach {result['host']}. Check connectivity.",
                )
                if a:
                    new_alerts.append(a)
            else:
                self._resolve(key_reach)

        return new_alerts

    def get_all(self) -> list:
        with self._lock:
            return [a.to_dict() for a in reversed(self._alerts)]

    def get_active(self) -> list:
        with self._lock:
            return [a.to_dict() for a in self._active.values()]

    def acknowledge(self, alert_id: str) -> bool:
        """Mark an active alert as resolved."""
        with self._lock:
            if alert_id in self._active:
                self._active[alert_id].resolved = True
                del self._active[alert_id]
                return True
        return False

    def clear_all(self):
        with self._lock:
            self._active.clear()
            self._alerts.clear()

    # ─── Private helpers ─────────────────────────────────────────────────────

    def _fire(self, alert_id: str, severity: str, title: str, message: str):
        """Fire an alert if it isn't already active."""
        with self._lock:
            if alert_id not in self._active:
                alert = Alert(alert_id, severity, title, message)
                self._active[alert_id] = alert
                self._alerts.append(alert)
                return alert.to_dict()
        return None

    def _resolve(self, alert_id: str):
        with self._lock:
            if alert_id in self._active:
                self._active[alert_id].resolved = True
                del self._active[alert_id]
