#!/usr/bin/env python
"""
sonic_app.py
Main Flask app for Sonic Dashboard.
"""



import os
import sys
import json
import asyncio
import logging
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, current_app
from flask_socketio import SocketIO
from config.config_constants import DB_PATH, CONFIG_PATH, BASE_DIR
#from config.config_manager import UnifiedConfigManager
from data.data_locker import DataLocker
from utils.json_manager import JsonManager
from utils.console_logger import ConsoleLogger as log  # 🚀 NEW
from cyclone.cyclone import Cyclone
from routes.theme_routes import theme_bp
from positions.positions_bp import positions_bp
from alerts.alerts_bp import alerts_bp
from prices.prices_bp import prices_bp
from dashboard.dashboard_bp import dashboard_bp
from portfolio.portfolio_bp import portfolio_bp
from sonic_labs.sonic_labs_bp import sonic_labs_bp
from cyclone.cyclone_bp import cyclone_bp
from utils.startup_checker import verify_paths
from utils.unified_logger import UnifiedLogger

# Flask App Initialization
app = Flask(__name__)
app.debug = False
app.secret_key = "i-like-lamp"
socketio = SocketIO(app)

# Banner
log.banner("SONIC DASHBOARD STARTUP")

# Startup Checks
log.info(f"Verifying paths...", source="Startup")
#verify_paths()

# Setup JSON Manager
unified_logger = UnifiedLogger()
app.json_manager = JsonManager(logger=unified_logger)

# Register Blueprints
log.info(f"Registering blueprints...", source="Startup")
app.register_blueprint(positions_bp, url_prefix="/positions")
app.register_blueprint(alerts_bp, url_prefix="/alerts")
app.register_blueprint(prices_bp, url_prefix="/prices")
app.register_blueprint(dashboard_bp)
app.register_blueprint(portfolio_bp, url_prefix="/portfolio")
app.register_blueprint(sonic_labs_bp, url_prefix="/sonic_labs")
app.register_blueprint(cyclone_bp)
app.register_blueprint(theme_bp)

# Aliases
if "dashboard.index" in app.view_functions:
    app.add_url_rule("/dashboard", endpoint="dash", view_func=app.view_functions["dashboard.index"])

log.success(f"Flask app initialized successfully.", source="Startup")

# Flask Routes
@app.route("/")
def index():
    return redirect(url_for('dashboard.dash_page'))

@app.route("/assets")
def assets():
    dl = DataLocker.get_instance(DB_PATH)
    balances = dl.get_balance_vars()
    brokers = dl.read_brokers()
    wallets = dl.read_wallets()
    return render_template("assets.html", **balances, brokers=brokers, wallets=wallets)

@app.route("/add_wallet", methods=["POST"])
def add_wallet():
    try:
        dl = DataLocker.get_instance(DB_PATH)
        balance_value = float(request.form.get("balance", "0") or 0.0)
        wallet = {
            "name": request.form.get("name"),
            "public_address": request.form.get("public_address"),
            "private_address": request.form.get("private_address"),
            "image_path": request.form.get("image_path"),
            "balance": balance_value
        }
        dl.create_wallet(wallet)
        flash(f"Wallet {wallet['name']} added successfully!", "success")
        log.success(f"Wallet {wallet['name']} added.", source="Wallets")
    except Exception as e:
        flash(f"Error adding wallet: {e}", "danger")
        log.error(f"Failed to add wallet: {e}", source="Wallets")
    return redirect(url_for("assets"))

@app.route("/delete_wallet/<wallet_name>", methods=["POST"])
def delete_wallet(wallet_name):
    try:
        dl = DataLocker.get_instance(DB_PATH)
        wallet = dl.get_wallet_by_name(wallet_name)
        if wallet:
            dl.cursor.execute("DELETE FROM wallets WHERE name=?", (wallet_name,))
            dl.conn.commit()
            flash(f"Wallet '{wallet_name}' deleted!", "success")
            log.success(f"Wallet '{wallet_name}' deleted.", source="Wallets")
        else:
            flash(f"Wallet '{wallet_name}' not found.", "danger")
            log.warning(f"Wallet '{wallet_name}' not found.", source="Wallets")
    except Exception as e:
        flash(f"Error deleting wallet: {e}", "danger")
        log.error(f"Error deleting wallet: {e}", source="Wallets")
    return redirect(url_for("assets"))

@app.route("/api/get_config")
def api_get_config():
    try:
        conf = UnifiedConfigManager.load_config()
        log.success(f"Loaded config.", source="API")
        return jsonify(conf)
    except Exception as e:
        log.error(f"Error loading config: {e}", source="API")
        return jsonify({"error": str(e)}), 500


@app.route('/api/update_row', methods=['POST'])
def api_update_row():
    try:
        data = request.get_json()
        table = data.get('table')
        pk_field = data.get('pk_field')
        pk_value = data.get('pk_value')
        row_data = data.get('row')

        dl = DataLocker.get_instance()

        if table == 'wallets':
            dl.update_wallet(pk_value, row_data)
        elif table == 'positions':
            pass
        else:
            pass

        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.exception("Error updating row")
        return jsonify({"error": str(e)}), 500


@app.route('/api/delete_row', methods=['POST'])
def api_delete_row():
    try:
        data = request.get_json()
        table = data.get('table')
        pk_field = data.get('pk_field')
        pk_value = data.get('pk_value')

        dl = DataLocker.get_instance()

        if table == 'wallets':
            return jsonify({"error": "Wallet deletion is disabled"}), 400
        elif table == 'positions':
            dl.delete_position(pk_value)
        else:
            pass

        return jsonify({"status": "success"}), 200
    except Exception as e:
        logger.exception("Error deleting row")
        return jsonify({"error": str(e)}), 500


@app.route("/system_config", methods=["GET"])
def system_config_page():
    dl = DataLocker.get_instance(DB_PATH)
    db_conn = dl.get_db_connection()
    config_manager = UnifiedConfigManager(CONFIG_PATH, db_conn=db_conn)
    config = config_manager.load_config()
    return render_template("system_config.html", config=config)


@app.route("/update_system_config", methods=["POST"])
def update_system_config():
    dl = DataLocker.get_instance(DB_PATH)
    db_conn = dl.get_db_connection()
    config_manager = UnifiedConfigManager(CONFIG_PATH, db_conn=db_conn)
    new_config = {}
    new_config.setdefault("system_config", {})["db_path"] = request.form.get("db_path")
    new_config["system_config"]["log_file"] = request.form.get("log_file")
    new_config["twilio_config"] = {
        "account_sid": request.form.get("account_sid"),
        "auth_token": request.form.get("auth_token"),
        "flow_sid": request.form.get("flow_sid"),
        "to_phone": request.form.get("to_phone"),
        "from_phone": request.form.get("from_phone")
    }
    config_manager.update_config(new_config)
    flash("Configuration updated successfully!", "success")
    return redirect(url_for("system_config_page"))

@app.context_processor
def update_theme_context():
    config_path = current_app.config.get("CONFIG_PATH", CONFIG_PATH)
    try:
        with open(config_path, 'r') as f:
            conf = json.load(f)
    except Exception as e:
        conf = {}
    theme_config = conf.get("theme_config", {})
    return dict(theme=theme_config)

@app.route('/test_twilio', methods=["POST"])
def send_test_twilio():
    from twilio_message_api import trigger_twilio_flow
    # Using UnifiedLogger here as well.
    unified_logger = UnifiedLogger()
    try:
        message = request.form.get("message", "Test message from system config")
        execution_sid = trigger_twilio_flow(message)
        unified_logger.log_operation("Notification Sent", "Testing Twilio", source="system test")
        return jsonify({"success": True, "sid": execution_sid})
    except Exception as e:
        unified_logger.log_operation("Notification Failed", "Testing Twilio Failed", source="system test")
        return jsonify({"success": False, "error": str(e)}), 500

# NEW: Global update route alias using the update_jupiter function from positions_bp.
@app.route("/update", methods=["GET"])
def update():
    from positions.positions_bp import update_jupiter
    return update_jupiter()

# NEW: Additional alias to allow "/dashboard/update" as well.
@app.route("/dashboard/update", methods=["GET"])
def dashboard_update():
    return update()

# NEW: Debug endpoint to manually trigger check_alerts for testing.
@app.route("/debug_check_alerts")
def debug_check_alerts():
    from alerts.alert_service_manager import AlertServiceManager
    import asyncio
    service = AlertServiceManager.get_instance()
    asyncio.run(service.process_all_alerts())
    return "check_alerts executed; please check the logs for debug messages."


# Main
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
    app.run(debug=False, host=host, port=port)
