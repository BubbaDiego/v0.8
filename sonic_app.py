#!/usr/bin/env python
"""
sonic_app.py
Description:
  The main Flask application for the Sonic Dashboard. This file:
    - Loads configuration and sets up logging.
    - Initializes the Flask app and SocketIO.
    - Registers blueprints for positions, alerts, prices, dashboard, portfolio, ChatGPT, and simulator dashboard.
    - Defines global routes for non-dashboard-specific functionality (e.g., assets, exchanges, etc.).
    - Optionally launches a local monitor (local_monitor.py) in a new console window if
      the '--monitor' command-line flag is provided.

Usage:
  To run normally:
      python sonic_app.py
  To run with the local monitor:
      python sonic_app.py --monitor
"""

import os
import sys
import json
import logging
import sqlite3
import asyncio
import pytz
import requests
from datetime import datetime, timedelta
from uuid import uuid4
import asyncio
from flask import jsonify
from cyclone.cyclone import Cyclone


from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, current_app
from flask_socketio import SocketIO, emit
from config.config_constants import DB_PATH, CONFIG_PATH, BASE_DIR
from config.config_manager import UnifiedConfigManager
from data.data_locker import DataLocker
from utils.json_manager import JsonManager
from positions.positions_bp import positions_bp
from alerts.alerts_bp import alerts_bp
from prices.prices_bp import prices_bp
from dashboard.dashboard_bp import dashboard_bp
from portfolio.portfolio_bp import portfolio_bp
#from simulator.simulator_bp import simulator_bp as simulator_bp
#from jupiter.jupiter_bp import jupiter_bp
from cyclone.cyclone_bp import cyclone_bp
from utils.unified_logger import UnifiedLogger
from sonic_labs.sonic_labs_bp import sonic_labs_bp
#from chat_gpt.chat_gpt_bp import chat_gpt_bp
#from aave.aave_bp import aave_bp
#from aave import aave_api

from cyclone.cyclone_bp import cyclone_bp




# Setup logging
logger = logging.getLogger("WebAppLogger")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(name)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

# Load configuration
#with open(CONFIG_PATH, "r") as f:
#    config = json.load(f)

# Initialize Flask app and SocketIO
app = Flask(__name__)
app.debug = False
app.secret_key = "i-like-lamp"
socketio = SocketIO(app)

# Register Blueprints
app.register_blueprint(positions_bp, url_prefix="/positions")
app.register_blueprint(alerts_bp, url_prefix="/alerts")
app.register_blueprint(prices_bp, url_prefix="/prices")
app.register_blueprint(dashboard_bp)  # Dashboard-specific routes and API endpoints

app.register_blueprint(sonic_labs_bp, url_prefix="/sonic_labs")
#app.register_blueprint(cyclone_bp, url_prefix="/cyclone")
app.register_blueprint(cyclone_bp)

#app.register_blueprint(chat_gpt_bp, url_prefix='/chat_gpt')
#app.register_blueprint(aave_bp, url_prefix="/aave")

#app.register_blueprint(jupiter_bp, url_prefix="/jupiter")

app.register_blueprint(portfolio_bp, url_prefix="/portfolio")

#app.register_blueprint(simulator_bp, url_prefix="/simulator")


unified_logger = UnifiedLogger()
unified_logger.log_operation("Start Launch Pad", "Launch Pad - Started", source="System")


app.json_manager = JsonManager(logger=unified_logger)

# --- Alias endpoints if needed ---
if "dashboard.index" in app.view_functions:
    app.add_url_rule("/dashboard", endpoint="dash", view_func=app.view_functions["dashboard.index"])

# Global Routes for non-dashboard-specific functionality

@app.route("/")
def index():
    # Currently redirects to dash.html

    return redirect(url_for('dashboard.dash_page'))

    #return redirect(url_for('dashboard.dashboard'))  # OLD AND BUSTED


@app.route("/2")
def index2():
    # Extract the new theme configuration from the config file.
    theme = {}
    theme_config = config.get("theme_config", {})
    selected = theme_config.get("selected_profile", "")
    if selected:
        theme = theme_config.get("profiles", {}).get(selected, {})

    # Provide default parameters for the simulation template with numeric defaults.
    params = {
        'entry_price': 0.0,
        'liquidation_price': 0.0,
        'position_size': 0.0,
        'position_side': 'long',
        'rebalance_threshold': 0.0,
        'hedging_cost_pct': 0.0,
        'simulation_duration': 0.0,
        'dt_minutes': 0.0,
        'drift': 0.0,
        'volatility': 0.0,
        'collateral': 0.0
    }
    results = {
        'cumulative_profit': 0,
        'final_price': 0,
        'simulation_log': []
    }
    baseline_compare = []
    tweaked_compare = []
    leverage = 0.0  # Default leverage value

    return redirect(url_for('dashboard.dashboard'))




@app.route("/add_broker", methods=["POST"])
def add_broker():
    dl = DataLocker.get_instance(DB_PATH)
    broker_dict = {
        "name": request.form.get("name"),
        "image_path": request.form.get("image_path"),
        "web_address": request.form.get("web_address"),
        "total_holding": float(request.form.get("total_holding", 0.0))
    }
    try:
        dl.create_broker(broker_dict)
    except Exception as e:
        print("")
    return redirect(url_for("assets"))


@app.route("/delete_wallet/<wallet_name>", methods=["POST"])
def delete_wallet(wallet_name):
    dl = DataLocker.get_instance(DB_PATH)
    try:
        wallet = dl.get_wallet_by_name(wallet_name)
        if wallet is None:
            flash(f"Wallet '{wallet_name}' not found.", "danger")
        else:
            dl._init_sqlite_if_needed()
            dl.cursor.execute("DELETE FROM wallets WHERE name=?", (wallet_name,))
            dl.conn.commit()
            flash(f"Wallet '{wallet_name}' deleted successfully!", "success")
    except Exception as e:
        flash(f"Error deleting wallet: {e}", "danger")
    return redirect(url_for("assets"))


@app.route("/add_wallet", methods=["POST"])
def add_wallet():
    dl = DataLocker.get_instance(DB_PATH)
    balance_str = request.form.get("balance", "0.0")
    if balance_str.strip() == "":
        balance_str = "0.0"
    try:
        balance_value = float(balance_str)
    except ValueError:
        balance_value = 0.0
    wallet = {
        "name": request.form.get("name"),
        "public_address": request.form.get("public_address"),
        "private_address": request.form.get("private_address"),
        "image_path": request.form.get("image_path"),
        "balance": balance_value
    }
    try:
        dl.create_wallet(wallet)
        flash(f"Wallet {wallet['name']} added successfully!", "success")
    except Exception as e:
        flash(f"Error adding wallet: {e}", "danger")
    return redirect(url_for("assets"))


@app.route("/assets")
def assets():
    dl = DataLocker.get_instance(DB_PATH)
    balance_vars = dl.get_balance_vars()
    total_brokerage_balance = balance_vars.get("total_brokerage_balance", 0.0)
    total_wallet_balance = balance_vars.get("total_wallet_balance", 0.0)
    total_balance = balance_vars.get("total_balance", 0.0)
    brokers = dl.read_brokers()
    wallets = dl.read_wallets()
    return render_template("assets.html",
                           total_brokerage_balance=total_brokerage_balance,
                           total_wallet_balance=total_wallet_balance,
                           total_balance=total_balance,
                           brokers=brokers,
                           wallets=wallets)


@app.route("/exchanges")
def exchanges():
    dl = DataLocker.get_instance(DB_PATH)
    brokers_data = dl.read_brokers()
    return render_template("exchanges.html", brokers=brokers_data)


@app.route("/jupiter_trade", methods=["GET", "POST"])
def jupiter_trade():
    result = None
    if request.method == "POST":
        wallet_address = request.form.get("walletAddress")
        action = request.form.get("action")

        if action == "open":
            leverage = request.form.get("leverage")
            collateral_token_delta = request.form.get("collateralTokenDelta")
            input_mint = request.form.get("inputMint")
            market_mint = request.form.get("marketMint")
            size_usd_delta = request.form.get("sizeUsdDelta")
            side = request.form.get("side")
            max_slippage_bps = request.form.get("maxSlippageBps")
            collateral_mint = request.form.get("collateralMint")
            result = (
                f"Executed open leveraged position for wallet {wallet_address} "
                f"with {side} side, {leverage}x leverage, and size delta {size_usd_delta}."
            )
        elif action == "close":
            result = f"Executed close position for wallet {wallet_address}."
    return render_template("jupiter_trade.html", result=result)

@app.route("/edit_wallet/<wallet_name>", methods=["GET", "POST"])
def edit_wallet(wallet_name):
    dl = DataLocker.get_instance(DB_PATH)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        public_addr = request.form.get("public_address", "").strip()
        private_addr = request.form.get("private_address", "").strip()
        image_path = request.form.get("image_path", "").strip()
        balance_str = request.form.get("balance", "0.0").strip()
        try:
            balance_val = float(balance_str)
        except ValueError:
            balance_val = 0.0
        wallet_dict = {
            "name": name,
            "public_address": public_addr,
            "private_address": private_addr,
            "image_path": image_path,
            "balance": balance_val
        }
        dl.update_wallet(wallet_name, wallet_dict)
        flash(f"Wallet '{name}' updated successfully!", "success")
        return redirect(url_for("assets"))
    else:
        wallet = dl.get_wallet_by_name(wallet_name)
        if not wallet:
            flash(f"Wallet '{wallet_name}' not found.", "danger")
            return redirect(url_for("assets"))
        return render_template("edit_wallet.html", wallet=wallet)


@app.route("/console_view")
def console_view():
    log_url = "https://www.pythonanywhere.com/user/BubbaDiego/files/var/log/www.deadlypanda.com.error.log"
    return render_template("console_view.html", log_url=log_url)


@app.route("/api/get_config")
def api_get_config():
    try:
        conf = UnifiedConfigManager.load_config()  # Assuming load_config is a static method if needed.
        logger.debug("Loaded config: %s", conf)
        return jsonify(conf)
    except Exception as e:
        logger.error("Error loading config: %s", e, exc_info=True)
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
def test_twilio():
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
    from alerts.alert_manager import manager
    manager.check_alerts(source="Debug Endpoint")
    return "check_alerts executed; please check the logs for debug messages."

if __name__ == "__main__":
    monitor = False
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        monitor = True
        # Using UnifiedLogger here instead of OperationsLogger.
        unified_logger = UnifiedLogger()
        unified_logger.log_operation("Manual Launch Pad Start", "Launch Pad - Started MANUAL", source="System")
    if monitor:
        import subprocess
        try:
            CREATE_NEW_CONSOLE = 0x00000010  # Windows flag for new console window
            monitor_script = os.path.join(BASE_DIR, "local_monitor.py")
            subprocess.Popen(["python", monitor_script], creationflags=CREATE_NEW_CONSOLE)
            logger.info("Launched local_monitor.py in a new console window.")
        except Exception as e:
            logger.error(f"Error launching local_monitor.py: {e}", exc_info=True)
    app.run(debug=True, host="0.0.0.0", port=5001)
