"""
main.py — Serves the single-page dashboard HTML.
"""

from flask import Blueprint, render_template, current_app

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    monitor = current_app.config["MONITOR"]
    system  = monitor.get_system_info()
    return render_template("index.html", system=system)
