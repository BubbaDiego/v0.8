# dashboard_bp.py

from flask import Blueprint, render_template, jsonify, request
from data.data_locker import DataLocker
from positions.position_service import PositionService
from config.config_constants import DB_PATH, THEME_CONFIG_PATH
import os, json

dashboard_bp = Blueprint('dashboard', __name__, template_folder='templates')

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

    # Fake ledger_info for now (you can replace with real freshness timers later)
    ledger_info = {
        "age_price": 0,
        "age_positions": 0,
        "age_cyclone": 0
    }

    return render_template(
        "dash.html",
        theme_mode=theme_mode,
        positions=all_positions,
        liquidation_positions=all_positions,
        portfolio_value="${:,.2f}".format(totals["total_value"]),
        portfolio_change="N/A",
        totals=totals,
        ledger_info=ledger_info
    )

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
# API: Graph Data
# ---------------------------------
@dashboard_bp.route("/api/graph_data")
def api_graph_data():
    timestamps = [
        "2025-04-24T10:00:00Z",
        "2025-04-24T11:00:00Z",
        "2025-04-24T12:00:00Z",
        "2025-04-24T13:00:00Z",
        "2025-04-24T14:00:00Z"
    ]
    values = [1000, 1050, 980, 1020, 1100]
    collaterals = [800, 810, 790, 800, 820]

    return jsonify({
        "timestamps": timestamps,
        "values": values,
        "collateral": collaterals
    })

# ---------------------------------
# API: Size Composition Pie
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
# API: Collateral Composition Pie
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

# ---------------------------------
# API: Get Alert Limits (for title bar timers)
# ---------------------------------
@dashboard_bp.route("/get_alert_limits")
def get_alert_limits():
    dl = DataLocker.get_instance()
    alert_limits = dl.get_alert_limits()
    return jsonify(alert_limits)
