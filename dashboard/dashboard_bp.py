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


from config.config_constants import DB_PATH, THEME_CONFIG_PATH
import os, json

dashboard_bp = Blueprint('dashboard', __name__, template_folder='templates')



# ✅ NEW WALLET IMAGE MAP
WALLET_IMAGE_MAP = {
    "ObiVault": "obivault.jpg",
    "R2Vault": "r2vault.jpg",
    "LandoVault": "landovault.jpg",
    # You can add more specific wallets here if needed
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

def format_monitor_time(iso_str):
    if not iso_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        pacific = dt.astimezone(ZoneInfo("America/Los_Angeles"))
        return pacific.strftime("Updated: %-I:%M %p %-m/%-d")
    except Exception:
        return "N/A"


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
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        pacific = dt.astimezone(ZoneInfo("America/Los_Angeles"))
        return pacific.strftime("%-I:%M %p")
    except Exception:
        return "N/A"

def apply_color(metric_name, value, limits):
    thresholds = limits.get(metric_name.lower())
    if thresholds is None or value is None:
        return "red"
    try:
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
    except:
        return "red"

@dashboard_bp.route("/dash", endpoint="dash_page")
def dash_page():
    dl = DataLocker.get_instance()
    all_positions = PositionService.get_all_positions(DB_PATH) or []

    for pos in all_positions:
        wallet_name = pos.get("wallet") or pos.get("wallet_name") or "Unknown"
        image_filename = WALLET_IMAGE_MAP.get(wallet_name, DEFAULT_WALLET_IMAGE)
        pos["wallet_image"] = image_filename

    positions = all_positions
    totals = {
        "total_collateral": sum(float(p.get("collateral", 0)) for p in positions),
        "total_value": sum(float(p.get("value", 0)) for p in positions),
        "total_size": sum(float(p.get("size", 0)) for p in positions),
        "avg_leverage": (sum(float(p.get("leverage", 0)) for p in positions) / len(positions)) if positions else 0,
        "avg_travel_percent": (sum(float(p.get("travel_percent", 0)) for p in positions) / len(positions)) if positions else 0,
    }

    jm = JsonManager()
    alert_limits = jm.load(ALERT_LIMITS_PATH, JsonType.ALERT_LIMITS)
    portfolio_limits = alert_limits.get("total_portfolio_limits", {})

    ledger_info = {
        "age_price": get_ledger_status('monitor/price_ledger.json').get("age_seconds", 9999),
        "last_price_time": get_ledger_status('monitor/price_ledger.json').get("last_timestamp", None),
        "age_positions": get_ledger_status('monitor/position_ledger.json').get("age_seconds", 9999),
        "last_positions_time": get_ledger_status('monitor/position_ledger.json').get("last_timestamp", None),
        "age_cyclone": get_ledger_status('monitor/sonic_ledger.json').get("age_seconds", 9999),
        "last_cyclone_time": get_ledger_status('monitor/sonic_ledger.json').get("last_timestamp", None),
        "age_operations": get_ledger_status('monitor/operations_ledger.json').get("age_seconds", 9999),
        "last_operations_time": get_ledger_status('monitor/operations_ledger.json').get("last_timestamp", None),
    }

    def determine_color(age):
        if age < 300:
            return "green"
        elif age < 900:
            return "yellow"
        return "red"

    universal_items = [
        {"title": "Price", "icon": "📈", "value": format_monitor_time(ledger_info["last_price_time"]), "color": determine_color(ledger_info["age_price"]), "raw_value": ledger_info["age_price"]},
        {"title": "Positions", "icon": "📊", "value": format_monitor_time(ledger_info["last_positions_time"]), "color": determine_color(ledger_info["age_positions"]), "raw_value": ledger_info["age_positions"]},
        {"title": "Operations", "icon": "⚙️", "value": format_monitor_time(ledger_info["last_operations_time"]), "color": determine_color(ledger_info["age_operations"]), "raw_value": ledger_info["age_operations"]},
        {"title": "Xcom", "icon": "🚀", "value": format_monitor_time(ledger_info["last_cyclone_time"]), "color": determine_color(ledger_info["age_cyclone"]), "raw_value": ledger_info["age_cyclone"]},
        {"title": "Value", "icon": "💰", "value": "${:,.0f}".format(totals["total_value"]), "color": apply_color("value", totals["total_value"], portfolio_limits), "raw_value": totals["total_value"]},
        {"title": "Leverage", "icon": "⚖️", "value": "{:.2f}".format(totals["avg_leverage"]), "color": apply_color("leverage", totals["avg_leverage"], portfolio_limits), "raw_value": totals["avg_leverage"]},
        {"title": "Heat", "icon": "🔥", "value": "N/A", "color": "red", "raw_value": 9999},
        {"title": "Size", "icon": "📊", "value": "${:,.0f}".format(totals["total_size"]), "color": apply_color("size", totals["total_size"], portfolio_limits), "raw_value": totals["total_size"]},
        {"title": "Ratio", "icon": "⚡", "value": "{:.2f}".format(totals["total_value"] / totals["total_collateral"]) if totals["total_collateral"] > 0 else "N/A", "color": apply_color("ratio", (totals["total_value"] / totals["total_collateral"]) if totals["total_collateral"] > 0 else None, portfolio_limits), "raw_value": (totals["total_value"] / totals["total_collateral"]) if totals["total_collateral"] > 0 else None},
        {"title": "Travel", "icon": "✈️", "value": "{:.2f}%".format(totals["avg_travel_percent"]), "color": apply_color("travel", totals["avg_travel_percent"], portfolio_limits), "raw_value": totals["avg_travel_percent"]}
    ]

    monitor_titles = {"Price", "Positions", "Operations", "Xcom"}
    monitor_items = [item for item in universal_items if item["title"] in monitor_titles]
    status_items = [item for item in universal_items if item["title"] not in monitor_titles]

    return render_template(
        "dashboard.html",
        theme_mode=dl.get_theme_mode(),
        positions=positions,
        liquidation_positions=positions,
        portfolio_value="${:,.2f}".format(totals["total_value"]),
        portfolio_change="N/A",
        totals=totals,
        ledger_info=ledger_info,
        status_items=status_items,
        monitor_items=monitor_items,
        portfolio_limits=portfolio_limits
    )

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
        long_total = sum(float(p.get("size", 0)) for p in positions if p.get("position_type", "").upper() == "LONG")
        short_total = sum(float(p.get("size", 0)) for p in positions if p.get("position_type", "").upper() == "SHORT")
        total = long_total + short_total
        series = [round(long_total / total * 100), round(short_total / total * 100)] if total > 0 else [0, 0]
        return jsonify({"series": series})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------------
# API: Collateral Composition Pie (Real positions)
# ---------------------------------
@dashboard_bp.route("/api/collateral_composition")
def api_collateral_composition():
    try:
        positions = PositionService.get_all_positions(DB_PATH) or []
        long_total = sum(float(p.get("collateral", 0)) for p in positions if p.get("position_type", "").upper() == "LONG")
        short_total = sum(float(p.get("collateral", 0)) for p in positions if p.get("position_type", "").upper() == "SHORT")
        total = long_total + short_total
        series = [round(long_total / total * 100), round(short_total / total * 100)] if total > 0 else [0, 0]
        return jsonify({"series": series})
    except Exception as e:
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
    try:
        with open(ALERT_LIMITS_PATH, 'r', encoding='utf-8') as f:
            limits = json.load(f)
        return jsonify({
            "call_refractory_period": limits.get("call_refractory_period", 1800),
            "call_refractory_start": limits.get("call_refractory_start"),
            "snooze_countdown": limits.get("snooze_countdown", 300),
            "snooze_start": limits.get("snooze_start")
        })
    except Exception as e:
        return jsonify({
            "call_refractory_period": 1800,
            "call_refractory_start": None,
            "snooze_countdown": 300,
            "snooze_start": None
        })
