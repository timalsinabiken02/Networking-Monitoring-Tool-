"""
api.py — REST API endpoints consumed by the dashboard JavaScript.

All endpoints return JSON. The frontend polls /api/stats every 2 s.
"""

from flask import Blueprint, jsonify, request, current_app

api_bp = Blueprint("api", __name__)


def _get_services(app):
    return (
        app.config["MONITOR"],
        app.config["SCANNER"],
        app.config["ALERTS"],
    )


# ── Main dashboard data ──────────────────────────────────────────────────────

@api_bp.route("/stats")
def stats():
    """Full metrics snapshot: bandwidth, ping, interfaces, system."""
    monitor, scanner, alerts = _get_services(current_app)
    data = monitor.get_all()
    data["alerts"] = alerts.get_active()
    return jsonify(data)


@api_bp.route("/bandwidth")
def bandwidth():
    monitor, _, _ = _get_services(current_app)
    return jsonify(monitor.get_bandwidth())


@api_bp.route("/bandwidth/history")
def bandwidth_history():
    monitor, _, _ = _get_services(current_app)
    return jsonify(monitor.get_bandwidth_history())


@api_bp.route("/ping")
def ping():
    monitor, _, _ = _get_services(current_app)
    return jsonify(monitor.get_ping())


@api_bp.route("/ping/history")
def ping_history():
    monitor, _, _ = _get_services(current_app)
    return jsonify(monitor.get_ping_history())


@api_bp.route("/interfaces")
def interfaces():
    monitor, _, _ = _get_services(current_app)
    return jsonify(monitor.get_interfaces())


# ── Devices ──────────────────────────────────────────────────────────────────

@api_bp.route("/devices")
def devices():
    _, scanner, _ = _get_services(current_app)
    return jsonify(scanner.get_devices())


@api_bp.route("/devices/scan", methods=["POST"])
def scan_devices():
    """Force an immediate ARP scan (may take a few seconds)."""
    _, scanner, _ = _get_services(current_app)
    result = scanner.scan_now()
    return jsonify({"status": "ok", "devices": result, "count": len(result)})


# ── Alerts ───────────────────────────────────────────────────────────────────

@api_bp.route("/alerts")
def alert_list():
    _, _, alerts = _get_services(current_app)
    return jsonify(alerts.get_all())


@api_bp.route("/alerts/active")
def active_alerts():
    _, _, alerts = _get_services(current_app)
    return jsonify(alerts.get_active())


@api_bp.route("/alerts/<alert_id>/acknowledge", methods=["POST"])
def acknowledge_alert(alert_id):
    _, _, alerts = _get_services(current_app)
    ok = alerts.acknowledge(alert_id)
    return jsonify({"status": "ok" if ok else "not_found"})


@api_bp.route("/alerts/clear", methods=["POST"])
def clear_alerts():
    _, _, alerts = _get_services(current_app)
    alerts.clear_all()
    return jsonify({"status": "cleared"})


# ── System ───────────────────────────────────────────────────────────────────

@api_bp.route("/system")
def system_info():
    monitor, _, _ = _get_services(current_app)
    return jsonify(monitor.get_system_info())


@api_bp.route("/health")
def health():
    return jsonify({"status": "ok", "service": "Network Monitor", "author": "Biken Timalsina"})
