from core.logging import log
from positions.position_core_service import PositionCoreService
from data.data_locker import DataLocker
from positions.position_sync_service import PositionSyncService
from utils.json_manager import JsonManager, JsonType
from monitor.ledger_reader import get_ledger_status
from datetime import datetime
from zoneinfo import ZoneInfo
from utils.fuzzy_wuzzy import fuzzy_match_key
from core.core_imports import ALERT_LIMITS_PATH, DB_PATH


global_data_locker = DataLocker(str(DB_PATH))

# 🔐 Controlled alias map
ALERT_KEY_ALIASES = {
    "value": ["total_value_limits"],
    "leverage": ["avg_leverage_limits"],
    "size": ["total_size_limits"],
    "ratio": ["value_to_collateral_ratio_limits"],
    "travel": ["avg_travel_percent_limits"],
    "heat": ["total_heat_limits"]
}

def format_monitor_time(iso_str):
    if not iso_str:
        log.debug("iso_str is None or empty", source="format_monitor_time")
        return "N/A"
    try:
        log.debug(f"Raw iso_str received: {iso_str}", source="format_monitor_time")
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        pacific = dt.astimezone(ZoneInfo("America/Los_Angeles"))
        hour = pacific.strftime("%I").lstrip('0') or '0'
        minute = pacific.strftime("%M")
        ampm = pacific.strftime("%p")
        month = str(pacific.month)
        day = str(pacific.day)
        formatted = f"{hour}:{minute} {ampm} {month}/{day}"
        log.debug(f"Parsed and formatted time: {formatted}", source="format_monitor_time")
        return formatted
    except Exception as e:
        log.error(f"format_monitor_time failed for string '{iso_str}': {e}", source="format_monitor_time")
        return "N/A"

def apply_color(metric_name, value, limits):
    try:
        thresholds = limits.get(metric_name.lower())
        if thresholds is None:
            matched_key = fuzzy_match_key(metric_name, limits, aliases=ALERT_KEY_ALIASES, threshold=40.0)
            log.info(f"🔍 FuzzyMatch resolved '{metric_name}' → '{matched_key}'", source="FuzzyMatch")
            thresholds = limits.get(matched_key)

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
        log.error(f"apply_color failed → metric: '{metric_name}', value: {value}, error: {e}", source="DashboardContext")
        return "red"

def determine_color(age):
    if age < 300:
        return "green"
    elif age < 900:
        return "yellow"
    return "red"

def get_dashboard_context(data_locker):
    log.info("📊 Assembling dashboard context", source="DashboardContext")

    position_core = PositionCoreService(data_locker)
    positions = position_core.get_all_positions() or []

    for pos in positions:
        wallet_name = pos.get("wallet") or pos.get("wallet_name") or "Unknown"
        pos["wallet_image"] = wallet_name

    totals = {
        "total_collateral": sum(float(p.get("collateral", 0)) for p in positions),
        "total_value": sum(float(p.get("value", 0)) for p in positions),
        "total_size": sum(float(p.get("size", 0)) for p in positions),
        "avg_leverage": (sum(float(p.get("leverage", 0)) for p in positions) / len(positions)) if positions else 0,
        "avg_travel_percent": (sum(float(p.get("travel_percent", 0)) for p in positions) / len(positions)) if positions else 0,
        "avg_heat_index": (sum(float(p.get("heat_index", 0)) for p in positions) / len(positions)) if positions else 0
    }

    jm = JsonManager()
    alert_limits = jm.load(ALERT_LIMITS_PATH, JsonType.ALERT_LIMITS)  # ✅

    portfolio_limits = alert_limits.get("alert_limits", {}).get("total_portfolio_limits", {})

    ledger_info = {
        "age_price": get_ledger_status('monitor/price_ledger.json').get("age_seconds", 9999),
        "last_price_time": get_ledger_status('monitor/price_ledger.json').get("last_timestamp", None),
        "age_positions": get_ledger_status('monitor/position_ledger.json').get("age_seconds", 9999),
        "last_positions_time": get_ledger_status('monitor/position_ledger.json').get("last_timestamp", None),
        "age_operations": get_ledger_status('monitor/operations_ledger.json').get("age_seconds", 9999),
        "last_operations_time": get_ledger_status('monitor/operations_ledger.json').get("last_timestamp", None),
        "age_xcom": get_ledger_status('monitor/xcom_ledger.json').get("age_seconds", 9999),
        "last_xcom_time": get_ledger_status('monitor/xcom_ledger.json').get("last_timestamp", None),
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

    log.debug("📊 Dashboard status items", source="DashboardContext", payload=status_items)
    log.debug("🛁 Dashboard monitor items", source="DashboardContext", payload=monitor_items)
    log.debug("📀 Portfolio limit config", source="DashboardContext", payload=portfolio_limits)

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
        "portfolio_limits": portfolio_limits
    }