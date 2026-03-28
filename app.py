"""
app.py — Application entry point.

Run with:
    python app.py
Then open http://localhost:5000
"""

import logging
import threading
from flask import Flask
from flask_cors import CORS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger(__name__)

from config import Config
from monitor import NetworkMonitor, DeviceScanner, AlertManager
from routes import main_bp, api_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    # ── Register blueprints ──────────────────────────────────────────────────
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # ── Initialise services ──────────────────────────────────────────────────
    monitor = NetworkMonitor()
    scanner = DeviceScanner()
    alerts  = AlertManager()

    app.config["MONITOR"] = monitor
    app.config["SCANNER"] = scanner
    app.config["ALERTS"]  = alerts

    # ── Start background threads ─────────────────────────────────────────────
    monitor.start_monitoring()
    scanner.start()

    # Alert evaluation thread — runs every PING_INTERVAL seconds
    def alert_loop():
        import time
        while True:
            try:
                bw   = monitor.get_bandwidth()
                ping = monitor.get_ping()
                if bw and ping:
                    alerts.evaluate(bw, ping)
            except Exception:
                log.exception("Error in alert evaluation loop")
            time.sleep(Config.PING_INTERVAL)

    threading.Thread(target=alert_loop, daemon=True).start()

    return app


if __name__ == "__main__":
    app = create_app()
    print("\n" + "="*55)
    print("  🖥️  Network Monitor — by Biken Timalsina")
    print(f"  🌐  Dashboard: http://localhost:{Config.PORT}")
    print(f"  📡  API:       http://localhost:{Config.PORT}/api/stats")
    print("  🔑  Admin password: (set via ADMIN_PASSWORD env var)")
    print("="*55 + "\n")
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        use_reloader=False,   # prevent double-start of threads
    )
