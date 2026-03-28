"""
devices.py — Scans the local network for connected devices using ARP.
Falls back to parsing the system ARP table if scapy is unavailable.
"""

import logging
import subprocess
import platform
import re
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime
from config import Config

log = logging.getLogger(__name__)


def _get_hostname(ip: str) -> str:
    """Reverse-DNS lookup with a 1-second timeout."""
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(socket.gethostbyaddr, ip)
            return future.result(timeout=1)[0]
    except (FuturesTimeoutError, Exception):
        return "Unknown"


def _parse_arp_table() -> list:
    """
    Read the OS ARP cache (works without root/admin).
    Returns a list of dicts: {ip, mac, hostname, type}.
    """
    system = platform.system().lower()
    try:
        result = subprocess.run(
            ["arp", "-a"],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout
    except Exception:
        return []

    devices = []
    # Match lines like: 192.168.1.1   aa:bb:cc:dd:ee:ff   dynamic
    mac_pattern = re.compile(
        r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"   # IP
        r".*?"
        r"(([0-9a-fA-F]{2}[:\-]){5}[0-9a-fA-F]{2})"  # MAC
    )
    seen = set()
    for line in output.splitlines():
        m = mac_pattern.search(line)
        if m:
            ip  = m.group(1)
            mac = m.group(2).upper().replace("-", ":")
            if ip in seen or ip.endswith(".255") or ip == "255.255.255.255":
                continue
            seen.add(ip)

            # Guess device type from MAC OUI (very basic)
            dtype = _guess_type(mac)

            devices.append({
                "ip":       ip,
                "mac":      mac,
                "hostname": _get_hostname(ip),
                "type":     dtype,
                "status":   "online",
                "last_seen": datetime.now().strftime("%H:%M:%S"),
            })
    return devices


def _guess_type(mac: str) -> str:
    """Heuristic device-type guess based on MAC OUI prefix."""
    oui = mac[:8].upper()
    routers  = {"00:50:56", "00:0C:29", "00:1A:11", "B8:27:EB", "DC:A6:32"}
    phones   = {"A4:C3:F0", "3C:5A:B4", "00:1A:2B"}
    printers = {"00:80:77", "00:00:48", "00:00:74"}
    if oui in routers:  return "Router/AP"
    if oui in phones:   return "Mobile"
    if oui in printers: return "Printer"
    return "Computer"


class DeviceScanner:
    """
    Background scanner that refreshes the device list periodically.
    """

    def __init__(self):
        self._lock    = threading.Lock()
        self._devices = []
        self._running = False

    def start(self):
        self._running = True
        t = threading.Thread(target=self._scan_loop, daemon=True)
        t.start()

    def stop(self):
        self._running = False

    def get_devices(self) -> list:
        with self._lock:
            return list(self._devices)

    def _scan_loop(self):
        while self._running:
            try:
                devices = _parse_arp_table()
                with self._lock:
                    self._devices = devices
            except Exception:
                log.exception("Error in device scan loop")
            time.sleep(Config.DEVICE_SCAN_INTERVAL)

    def scan_now(self) -> list:
        """Force an immediate scan and return results."""
        devices = _parse_arp_table()
        with self._lock:
            self._devices = devices
        return devices
