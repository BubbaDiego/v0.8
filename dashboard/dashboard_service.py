
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.logging import log
from positions.position_core import PositionCore
from data.data_locker import DataLocker
from utils.json_manager import JsonManager, JsonType
from monitor.ledger_reader import get_ledger_status
from datetime import datetime
from zoneinfo import ZoneInfo
from utils.fuzzy_wuzzy import fuzzy_match_key
from core.core_imports import ALERT_LIMITS_PATH, DB_PATH


def format_monitor_time(iso_str):
    if not iso_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        pacific = dt.astimezone(ZoneInfo("America/Los_Angeles"))
        return pacific.strftime("%I:%M %p %m/%d").lstrip("0")
    except Exception as e:
        log.error(f"Time formatting failed: {e}", source="DashboardContext")
        return "N/A"

def determine_color(age):
    if age < 300:
        return "green"
    elif age < 900:
        return "yellow"
    return "red"

ALERT_KEY_ALIASES = {
    "value": ["total_value_limits"],
    "leverage": ["avg_leverage_limits"],
    "size": ["total_size_limits"],
    "ratio": ["value_to_collateral_ratio_limits"],
    "travel": ["avg_travel_percent_limits"],
    "heat": ["total_heat_limits"]
}

def apply_color(metric_name, value, limits):
    try:
        thresholds = limits.get(metric_name.lower())
        if thresholds is None:
            matched_key = fuzzy_match_key(metric_name, limits, aliases=ALERT_KEY_ALIASES, threshold=40.0)
            thresholds = limits.get(matched_key)
        if thresholds is None or value is None:
            return "red"
        val = float(value)
        if metric_name.lower() == "travel":
            return (
                "green" if val >= thresholds["low"] else
                "yellow" if val >= thresholds["medium"] else
                "red"
            )
        return (
            "green" if val <= thresholds["low"] else
            "yellow" if val <= thresholds["medium"] else
            "red"
        )
    except Exception as e:
        log.error(f"apply_color failed: {e}", source="DashboardContext")
        return "red"

def get_dashboard_context(data_locker: DataLocker):
    log.info("📊 Assembling dashboard context", source="DashboardContext")

    position_core = PositionCore(data_locker)
    positions = position_core.get_all_positions() or []

    for pos in positions:
        wallet_name = pos.get("wallet") or pos.get("wallet_name") or "Unknown"
        pos["wallet_image"] = wallet_name

    from utils.calc_services import CalcServices
    totals = CalcServices().calculate_totals(positions)

    jm = JsonManager()
    alert_limits = jm.load(ALERT_LIMITS_PATH, JsonType.ALERT_LIMITS)
    portfolio_limits = alert_limits.get("alert_limits", {}).get("total_portfolio_limits", {})

    ledger_info = {
        "age_price": get_ledger_status('monitor/price_ledger.json').get("age_seconds", 9999),
        "last_price_time": get_ledger_status('monitor/price_ledger.json').get("last_timestamp"),
        "age_positions": get_ledger_status('monitor/position_ledger.json').get("age_seconds", 9999),
        "last_positions_time": get_ledger_status('monitor/position_ledger.json').get("last_timestamp"),
        "age_operations": get_ledger_status('monitor/operations_ledger.json').get("age_seconds", 9999),
        "last_operations_time": get_ledger_status('monitor/operations_ledger.json').get("last_timestamp"),
        "age_xcom": get_ledger_status('monitor/xcom_ledger.json').get("age_seconds", 9999),
        "last_xcom_time": get_ledger_status('monitor/xcom_ledger.json').get("last_timestamp"),
    }

    universal_items = [
        {"title": "Price", "icon": "📈", "value": format_monitor_time(ledger_info["last_price_time"]),
         "color": determine_color(ledger_info["age_price"]), "raw_value": ledger_info["age_price"]},
        {"title": "Positions", "icon": "📊", "value": format_monitor_time(ledger_info["last_positions_time"]),
         "color": determine_color(ledger_info["age_positions"]), "raw_value": ledger_info["age_positions"]},
        {"title": "Operations", "icon": "⚙️", "value": format_monitor_time(ledger_info["last_operations_time"]),
         "color": determine_color(ledger_info["age_operations"]), "raw_value": ledger_info["age_operations"]},
        {"title": "Xcom", "icon": "🛁", "value": format_monitor_time(ledger_info["last_xcom_time"]),
         "color": determine_color(ledger_info["age_xcom"]), "raw_value": ledger_info["age_xcom"]},
        {"title": "Value", "icon": "💰", "value": "${:,.0f}".format(totals["total_value"]),
         "color": apply_color("total_value", totals["total_value"], portfolio_limits),
         "raw_value": totals["total_value"]},
        {"title": "Leverage", "icon": "⚖️", "value": "{:.2f}".format(totals["avg_leverage"]),
         "color": apply_color("avg_leverage", totals["avg_leverage"], portfolio_limits),
         "raw_value": totals["avg_leverage"]},
        {"title": "Size", "icon": "📊", "value": "${:,.0f}".format(totals["total_size"]),
         "color": apply_color("total_size", totals["total_size"], portfolio_limits),
         "raw_value": totals["total_size"]},
        {"title": "Ratio", "icon": "⚖️",
         "value": "{:.2f}".format(totals["total_value"] / totals["total_collateral"]) if totals["total_collateral"] > 0 else "N/A",
         "color": apply_color("value_to_collateral_ratio",
                              (totals["total_value"] / totals["total_collateral"]) if totals["total_collateral"] > 0 else None,
                              portfolio_limits),
         "raw_value": (totals["total_value"] / totals["total_collateral"]) if totals["total_collateral"] > 0 else None},
        {"title": "Travel", "icon": "✈️", "value": "{:.2f}%".format(totals["avg_travel_percent"]),
         "color": apply_color("avg_travel_percent", totals["avg_travel_percent"], portfolio_limits),
         "raw_value": totals["avg_travel_percent"]}
    ]

    monitor_titles = {"Price", "Positions", "Operations", "Xcom"}
    monitor_items = [item for item in universal_items if item["title"] in monitor_titles]
    status_items = [item for item in universal_items if item["title"] not in monitor_titles]

    portfolio_history = data_locker.portfolio.get_snapshots() or []
    graph_data = {
        "timestamps": [entry.get("snapshot_time") for entry in portfolio_history],
        "values": [float(entry.get("total_value", 0)) for entry in portfolio_history],
        "collateral": [float(entry.get("total_collateral", 0)) for entry in portfolio_history]
    }

    # 🧮 Size Composition
    long_total = sum(float(p.get("size", 0)) for p in positions if str(p.get("position_type", "")).upper() == "LONG")
    short_total = sum(float(p.get("size", 0)) for p in positions if str(p.get("position_type", "")).upper() == "SHORT")
    total = long_total + short_total

    log.debug("📊 Size totals", source="DashboardContext", payload={
        "long_total": long_total,
        "short_total": short_total,
        "combined": total
    })

    if total > 0:
        size_composition = {"series": [round(long_total / total * 100), round(short_total / total * 100)]}
    else:
        size_composition = {"series": [0, 0], "label": "No position data"}

    # 🧮 Collateral Composition
    long_collat = sum(
        float(p.get("collateral", 0)) for p in positions if str(p.get("position_type", "")).upper() == "LONG")
    short_collat = sum(
        float(p.get("collateral", 0)) for p in positions if str(p.get("position_type", "")).upper() == "SHORT")
    total_collat = long_collat + short_collat

    log.debug("💰 Collateral totals", source="DashboardContext", payload={
        "long_collat": long_collat,
        "short_collat": short_collat,
        "combined": total_collat
    })

    if total_collat > 0:
        collateral_composition = {
            "series": [round(long_collat / total_collat * 100), round(short_collat / total_collat * 100)]}
    else:
        collateral_composition = {"series": [0, 0], "label": "No collateral data"}

    return {
            "theme_mode": data_locker.system.get_theme_mode(),
            "positions": positions,
            "liquidation_positions": positions,
            "portfolio_value": "${:,.2f}".format(totals["total_value"]),
            "portfolio_change": "N/A",
            "totals": totals,
            "ledger_info": ledger_info,
            "status_items": status_items,
            "monitor_items": monitor_items,
            "portfolio_limits": portfolio_limits,
            "graph_data": graph_data,
            "size_composition": size_composition,
            "collateral_composition": collateral_composition
        }
