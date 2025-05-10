# dashboard_bp.py
# dashboard_bp.py

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from flask import Blueprint, render_template, jsonify, request, current_app
from data.data_locker import DataLocker
#from positions.position_sync_service import PositionSyncService
from positions.position_core_service import PositionCoreService
from monitor.ledger_reader import get_ledger_status
from datetime import datetime
from zoneinfo import ZoneInfo
from dashboard.dashboard_service import get_dashboard_context
from utils.fuzzy_wuzzy import fuzzy_match_key
from core.constants import THEME_CONFIG_PATH
from core.logging import log
from dashboard.dashboard_service import get_dashboard_context
from utils.route_decorators import route_log_alert
#from sonic_app import global_data_locker

dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates/dashboard')






# ✅ NEW WALLET IMAGE MAP
WALLET_IMAGE_MAP = {
    "ObiVault": "obivault.jpg",
    "R2Vault": "r2vault.jpg",
    "LandoVault": "landovault.jpg",
}
DEFAULT_WALLET_IMAGE = "unknown_wallet.jpg"



@dashboard_bp.route("/database_viewer")
@route_log_alert
def database_viewer():

    try:
        datasets = dl.get_all_tables_as_dict()

        log.info(f"🧠 Tables returned from DB: {list(datasets.keys())}", source="DatabaseViewer")
        if 'positions' in datasets:
            log.success(f"✅ {len(datasets['positions'])} positions loaded into viewer", source="DatabaseViewer")
        else:
            log.warning(f"⚠️ 'positions' table missing in viewer datasets", source="DatabaseViewer")

        return render_template("database_viewer.html", datasets=datasets)

    except Exception as e:
        log.error(f"❌ Error loading tables: {e}", source="DatabaseViewer")
        return render_template("database_viewer.html", datasets={})



# ---------------------------------
# Theme Setup Page
# ---------------------------------
@dashboard_bp.route("/theme_setup")
@route_log_alert
def theme_setup():
    from flask import current_app
    dl = current_app.data_locker
    theme_data = dl.load_theme_data()
    return render_template('theme_setup.html', theme=theme_data)


# ---------------------------------
# Save Theme Settings
# ---------------------------------
@dashboard_bp.route("/save_theme_mode", methods=["POST"])
@route_log_alert
def save_theme_mode():
    theme_mode = request.json.get("theme_mode")
    dl = get_locker()
    dl.set_theme_mode(theme_mode)
    return jsonify({"success": True})

@dashboard_bp.route("/save_theme", methods=["POST"])
@route_log_alert
def save_theme():
    theme_data = request.json
    with open(THEME_CONFIG_PATH, "w") as f:
        json.dump(theme_data, f, indent=2)
    return jsonify({"success": True})

@dashboard_bp.route("/api/get_prices")
@route_log_alert
def get_prices():
    from flask import current_app
    try:
        dl = current_app.data_locker
        prices = dl.get_price_dict()
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

@dashboard_bp.route("/dash")
@route_log_alert
def dash_page():
    from dashboard.dashboard_service import get_dashboard_context
    context = get_dashboard_context(current_app.data_locker)
    dl = current_app.data_locker
    return render_template("dashboard.html", **context)



@dashboard_bp.route('/alerts/alert_config_page', methods=['GET'])
@route_log_alert
def alert_config_page():
    # 🛑 Disabled temporarily
    return "🚫 Alert Config is currently disabled.", 410

# ---------------------------------
# API: Graph Data (Real portfolio history)
# ---------------------------------
@dashboard_bp.route("/api/graph_data")
@route_log_alert
def api_graph_data():
    dl = current_app.data_locker
    portfolio_history = dl.portfolio.get_snapshots() or []
    timestamps = [entry.get("snapshot_time") for entry in portfolio_history]
    values = [float(entry.get("total_value", 0)) for entry in portfolio_history]
    collaterals = [float(entry.get("total_collateral", 0)) for entry in portfolio_history]

    return jsonify({"timestamps": timestamps, "values": values, "collateral": collaterals})

# ---------------------------------
# API: Size Composition Pie (Real positions)
# ---------------------------------

@dashboard_bp.route("/api/size_composition")
@route_log_alert
def api_size_composition():
    try:
        core = PositionCoreService(current_app.data_locker)
        positions = core.get_all_positions() or []

        #positions = PositionCoreService.get_all_positions() or []

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
@route_log_alert
def api_collateral_composition():
    try:
        core = PositionCoreService(current_app.data_locker)
        positions = core.get_all_positions() or []

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