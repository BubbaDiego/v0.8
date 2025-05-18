#!/usr/bin/env python
"""
sonic_app.py
Main Flask app for Sonic Dashboard.
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))
# This ensures you can import anything from c:\v0.8\app\ easily

from flask import Flask, redirect, url_for, current_app, jsonify
from flask_socketio import SocketIO
from jinja2 import ChoiceLoader, FileSystemLoader

from core.core_imports import log, configure_console_log, DB_PATH, BASE_DIR, retry_on_locked
from data.data_locker import DataLocker
from system.system_core import SystemCore

# --- Monitor & Cyclone Core Integration ---
from monitor.monitor_core import MonitorCore
from cyclone.cyclone_engine import Cyclone

# --- Flask Setup ---
app = Flask(__name__)
app.debug = False
app.secret_key = "i-like-lamp"
socketio = SocketIO(app)

# Template folder support (new structure!)
app.jinja_loader = ChoiceLoader([
    FileSystemLoader('templates'),
    FileSystemLoader('app/dashboard'),
    FileSystemLoader('app/positions'),
    # Add more as needed!
])

# --- SINGLETON BACKEND ---
app.data_locker = DataLocker(str(DB_PATH))
app.system_core = SystemCore(app.data_locker)
app.monitor_core = MonitorCore()
app.cyclone = Cyclone(monitor_core=app.monitor_core)

# --- Logging Setup ---
log.banner("SONIC DASHBOARD STARTUP")
log.enable_all()
log.init_status()
configure_console_log()

# --- Blueprints ---
from positions_bp import positions_bp
from alerts_bp import alerts_bp
from prices_bp import prices_bp
from dashboard_bp import dashboard_bp
# from portfolio_bp import portfolio_bp
# from sonic_labs_bp import sonic_labs_bp
from cyclone.cyclone_bp import cyclone_bp
# from theme_routes import theme_bp
from system_bp import system_bp
# from settings_bp import settings_bp

log.info("Registering blueprints...", source="Startup")
app.register_blueprint(positions_bp, url_prefix="/positions")
app.register_blueprint(alerts_bp, url_prefix="/alerts")
app.register_blueprint(prices_bp, url_prefix="/prices")
app.register_blueprint(dashboard_bp)
# app.register_blueprint(portfolio_bp, url_prefix="/portfolio")
# app.register_blueprint(sonic_labs_bp, url_prefix="/sonic_labs")
app.register_blueprint(cyclone_bp)
# app.register_blueprint(theme_bp)
app.register_blueprint(system_bp)
# app.register_blueprint(settings_bp)

# --- Set Default Email Provider for XCom ---
with app.app_context():
    providers = app.data_locker.system.get_var("xcom_providers") or {}
    providers["email"] = {
        "enabled": False,  # Set to True if you want to enable email
        "smtp": {
            "server": "smtp.gmail.com",
            "port": 587,
            "username": "bubba.diego@gmail.com",
            "password": "pzix taan afbe igxb",
            "default_recipient": "bubba.diego@gmail.com"
        }
    }
    app.data_locker.system.set_var("xcom_providers", providers)
    print("✅ Default email provider set in xcom_providers")

# --- Heartbeat API Route for Countdown ---
@app.route("/api/heartbeat")
def api_heartbeat():
    dl = app.data_locker
    cursor = dl.db.get_cursor()
    cursor.execute("SELECT monitor_name, last_run, interval_seconds FROM monitor_heartbeat")
    rows = cursor.fetchall()
    result = []
    for row in rows:
        result.append({
            "name": row["monitor_name"],
            "last_run": row["last_run"],
            "interval_seconds": row["interval_seconds"],
        })
    return jsonify({"monitors": result})

# --- Simple Root Redirect ---
@app.route("/")
@retry_on_locked()
def index():
    log.info(f"📂 DB path in use: {current_app.data_locker.db.db_path}", source="DBPath")
    return redirect(url_for('dashboard.dash_page'))

# --- Optional: System Config (if needed by admin panel) ---
# ... (Keep any routes you actually want for config/admin or special actions)

# --- Context: Theme Profile (optional, for templates) ---
@app.context_processor
def inject_theme_profile():
    try:
        core = SystemCore(current_app.data_locker)
        active_theme = core.get_active_profile()
        return {"active_theme_profile": active_theme or {}}
    except Exception:
        return {"active_theme_profile": {}}

# --- Server Entry Point ---
if __name__ == "__main__":
    monitor = "--monitor" in sys.argv
    if monitor:
        try:
            import subprocess
            CREATE_NEW_CONSOLE = 0x00000010
            monitor_script = os.path.join(BASE_DIR, "local_monitor.py")
            subprocess.Popen(["python", monitor_script], creationflags=CREATE_NEW_CONSOLE)
            log.info("Launched local monitor in new console window.", source="Startup")
        except Exception as e:
            log.error(f"Failed to launch local monitor: {e}", source="Startup")

    host = "0.0.0.0"
    port = 5001
    log.success(f"Starting Flask server at {host}:{port}", source="Startup")
    log.print_dashboard_link(host="127.0.0.1", port=port, route="/")
    app.run(debug=False, host=host, port=port)
