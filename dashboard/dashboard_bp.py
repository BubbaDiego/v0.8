# dashboard_bp.py

from flask import Blueprint, render_template, jsonify, request
from data.data_locker import DataLocker
from positions.position_service import PositionService
#from monitor.price_ledger import PriceLedger
#from monitor.position_ledger import PositionLedger
#from monitor.sonic_ledger import SonicLedger
#from monitor.ledger_reader import get_ledger_age_seconds
from monitor.ledger_reader import get_ledger_status


from config.config_constants import DB_PATH, THEME_CONFIG_PATH
import os, json

dashboard_bp = Blueprint('dashboard', __name__, template_folder='templates')



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

# ---------------------------------
# Main Dashboard Page
# ---------------------------------
@dashboard_bp.route("/dash", endpoint="dash_page")
def dash_page():
    dl = DataLocker.get_instance()
    all_positions = PositionService.get_all_positions(DB_PATH) or []

    totals = {
        "total_collateral": sum(float(p.get("collateral", 0)) for p in all_positions),
        "total_value": sum(float(p.get("value", 0)) for p in all_positions),
        "total_size": sum(float(p.get("size", 0)) for p in all_positions),
        "avg_leverage": (sum(float(p.get("leverage", 0)) for p in all_positions) / len(all_positions)) if all_positions else 0,
        "avg_travel_percent": (sum(float(p.get("travel_percent", 0)) for p in all_positions) / len(all_positions)) if all_positions else 0,
    }

    theme_mode = dl.get_theme_mode()

    ledger_info = {
        "age_price": get_ledger_status('monitor/price_ledger.json')["age_seconds"],
        "age_positions": get_ledger_status('monitor/position_ledger.json')["age_seconds"],
        "age_cyclone": get_ledger_status('monitor/sonic_ledger.json')["age_seconds"]
    }

    return render_template(
        "dashboard.html",
        theme_mode=theme_mode,
        positions=all_positions,
        liquidation_positions=all_positions,
        portfolio_value="${:,.2f}".format(totals["total_value"]),
        portfolio_change="N/A",
        totals=totals,
        ledger_info=ledger_info
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
