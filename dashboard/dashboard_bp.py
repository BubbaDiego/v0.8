# dashboard_bp.py
# dashboard_bp.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from flask import Blueprint, render_template, jsonify, request
from data.data_locker import DataLocker
from positions.position_service import PositionService
#from monitor.price_ledger import PriceLedger
#from monitor.position_ledger import PositionLedger
#from monitor.sonic_ledger import SonicLedger
#from monitor.ledger_reader import get_ledger_age_seconds
from utils.json_manager import JsonManager, JsonType
from monitor.ledger_reader import get_ledger_status
from datetime import datetime
from zoneinfo import ZoneInfo
from dashboard.dashboard_service import get_dashboard_context
from utils.fuzzy_wuzzy import fuzzy_match_key



from config.config_constants import DB_PATH, THEME_CONFIG_PATH
import os, json

dashboard_bp = Blueprint('dashboard', __name__, template_folder='templates')



# ✅ NEW WALLET IMAGE MAP
WALLET_IMAGE_MAP = {
    "ObiVault": "obivault.jpg",
    "R2Vault": "r2vault.jpg",
    "LandoVault": "landovault.jpg",
}
DEFAULT_WALLET_IMAGE = "unknown_wallet.jpg"



# ---------------------------------
# Database Viewer
# ---------------------------------
@dashboard_bp.route("/database_viewer")
def database_viewer():
    dl = DataLocker.get_instance()
    datasets = dl.get_all_tables_as_dict()
    return render_template('database_viewer.html', datasets=datasets)

# ---------------------------------
# Theme Setup Page
# ---------------------------------
@dashboard_bp.route("/theme_setup")
def theme_setup():
    dl = DataLocker.get_instance()
    theme_data = dl.load_theme_data()
    return render_template('theme_setup.html', theme=theme_data)

# ---------------------------------
# Save Theme Settings
# ---------------------------------
@dashboard_bp.route("/save_theme_mode", methods=["POST"])
def save_theme_mode():
    theme_mode = request.json.get("theme_mode")
    dl = DataLocker.get_instance()
    dl.set_theme_mode(theme_mode)
    return jsonify({"success": True})

@dashboard_bp.route("/save_theme", methods=["POST"])
def save_theme():
    theme_data = request.json
    with open(THEME_CONFIG_PATH, "w") as f:
        json.dump(theme_data, f, indent=2)
    return jsonify({"success": True})

@dashboard_bp.route("/api/get_prices")
def get_prices():
    try:
        dl = DataLocker.get_instance()
        prices = dl.get_price_dict()  # Make sure this returns a dict with BTC/ETH/SOL keys
        return jsonify({
            "BTC": prices.get("BTC"),
            "ETH": prices.get("ETH"),
            "SOL": prices.get("SOL")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------
# Main Dashboard Page
# ---------------------------------
def format_monitor_time(iso_str):
    if not iso_str:
        print("DEBUG: iso_str is None or empty")
        return "N/A"
    try:
        print(f"DEBUG: Raw iso_str received: {iso_str}")
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        pacific = dt.astimezone(ZoneInfo("America/Los_Angeles"))

        # Manual components to strip leading 0s
        hour = pacific.strftime("%I").lstrip('0') or '0'
        minute = pacific.strftime("%M")
        ampm = pacific.strftime("%p")
        month = str(pacific.month)
        day = str(pacific.day)

        formatted = f"{hour}:{minute} {ampm} {month}/{day}"
        print(f"DEBUG: Parsed and formatted time: {formatted}")
        return formatted
    except Exception as e:
        print(f"DEBUG: Exception occurred in format_monitor_time: {e}")
        return "N/A"

def apply_color(metric_name, value, limits):
    try:
        # 🔍 Attempt direct match
        thresholds = limits.get(metric_name.lower())

        # 🧠 If no match, apply fuzzy logic
        if thresholds is None:
            matched_key = fuzzy_match_key(metric_name, limits, threshold=65.0)
            thresholds = limits.get(matched_key)
            print(f"[FuzzyMatch] Resolved '{metric_name}' to '{matched_key}'")

        # 🚨 Still nothing? Fail safely
        if thresholds is None or value is None:
            return "red"

        val = float(value)

        if metric_name.lower() == "travel":
            if val >= thresholds["low"]:
                return "green"
            elif val >= thresholds["medium"]:
                return "yellow"
            else:
                return "red"
        else:
            if val <= thresholds["low"]:
                return "green"
            elif val <= thresholds["medium"]:
                return "yellow"
            else:
                return "red"

    except Exception as e:
        print(f"[apply_color ERROR] Metric: {metric_name}, Value: {value}, Error: {e}")
        return "red"

@dashboard_bp.route("/dash", endpoint="dash_page")
def dash_page():
    context = get_dashboard_context()
    return render_template("dashboard.html", **context)
     #return render_template("dashboard.html", **context)



@dashboard_bp.route('/alert_config_page', methods=['GET'])
def alert_config_page():
    # 🛑 Disabled temporarily
    return "🚫 Alert Config is currently disabled.", 410
# ---------------------------------
# API: Graph Data (Real portfolio history)
# ---------------------------------
@dashboard_bp.route("/api/graph_data")
def api_graph_data():
    dl = DataLocker.get_instance()
    portfolio_history = dl.get_portfolio_history() or []
    timestamps = [entry.get("snapshot_time") for entry in portfolio_history]
    values = [float(entry.get("total_value", 0)) for entry in portfolio_history]
    collaterals = [float(entry.get("total_collateral", 0)) for entry in portfolio_history]

    return jsonify({"timestamps": timestamps, "values": values, "collateral": collaterals})

# ---------------------------------
# API: Size Composition Pie (Real positions)
# ---------------------------------

@dashboard_bp.route("/api/size_composition")
def api_size_composition():
    try:
        positions = PositionService.get_all_positions(DB_PATH) or []

        long_total = sum(float(p.get("size", 0)) for p in positions if str(p.get("position_type", "")).upper() == "LONG")
        short_total = sum(float(p.get("size", 0)) for p in positions if str(p.get("position_type", "")).upper() == "SHORT")
        total = long_total + short_total

        if total > 0:
            series = [round(long_total / total * 100), round(short_total / total * 100)]
        else:
            print("⚠️ No LONG/SHORT positions found for size pie.")
            series = [0, 0]

        return jsonify({"series": series})

    except Exception as e:
        print(f"[Pie Chart Error] Size composition: {e}")
        return jsonify({"error": str(e)}), 500


# ---------------------------------
# API: Collateral Composition Pie (Real positions)
# ---------------------------------
@dashboard_bp.route("/api/collateral_composition")
def api_collateral_composition():
    try:
        positions = PositionService.get_all_positions(DB_PATH) or []

        long_total = sum(float(p.get("collateral", 0)) for p in positions if str(p.get("position_type", "")).upper() == "LONG")
        short_total = sum(float(p.get("collateral", 0)) for p in positions if str(p.get("position_type", "")).upper() == "SHORT")
        total = long_total + short_total

        if total > 0:
            series = [round(long_total / total * 100), round(short_total / total * 100)]
        else:
            print("⚠️ No LONG/SHORT positions found for collateral pie.")
            series = [0, 0]

        return jsonify({"series": series})

    except Exception as e:
        print(f"[Pie Chart Error] Collateral composition: {e}")
        return jsonify({"error": str(e)}), 500


@dashboard_bp.route("/api/ledger_ages")
def api_ledger_ages():
    return jsonify({
        "age_price": get_ledger_status('monitor/price_ledger.json')["age_seconds"],
        "last_price_time": get_ledger_status('monitor/price_ledger.json')["last_timestamp"],
        "age_positions": get_ledger_status('monitor/position_ledger.json')["age_seconds"],
        "last_positions_time": get_ledger_status('monitor/position_ledger.json')["last_timestamp"],
        "age_cyclone": get_ledger_status('monitor/sonic_ledger.json')["age_seconds"],
        "last_cyclone_time": get_ledger_status('monitor/sonic_ledger.json')["last_timestamp"]
    })




# ---------------------------------
# API: Get Alert Limits (for title bar timers)
# ---------------------------------
from config.config_constants import ALERT_LIMITS_PATH
import json



@dashboard_bp.route("/get_alert_limits")
def get_alert_limits():
    # 🔕 Temporarily disabled until rework
    return jsonify({
        "call_refractory_period": 1800,
        "call_refractory_start": None,
        "snooze_countdown": 300,
        "snooze_start": None,
        "disabled": True
    })