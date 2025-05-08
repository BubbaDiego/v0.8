from data.data_locker import DataLocker
from positions.position_service import PositionService
from utils.json_manager import JsonType
from monitor.ledger_reader import get_ledger_status
from datetime import datetime
from zoneinfo import ZoneInfo

def format_monitor_time(iso_str):
    if not iso_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        pacific = dt.astimezone(ZoneInfo("America/Los_Angeles"))
        hour = pacific.strftime("%I").lstrip('0') or '0'
        minute = pacific.strftime("%M")
        ampm = pacific.strftime("%p")
        month = str(pacific.month)
        day = str(pacific.day)
        return f"{hour}:{minute} {ampm} {month}/{day}"
    except Exception as e:
        print(f"[ERROR] format_monitor_time failed: {e}")
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

def determine_color(age):
    if age < 300:
        return "green"
    elif age < 900:
        return "yellow"
    return "red"

from data.data_locker import DataLocker
from positions.position_service import PositionService
from utils.json_manager import JsonType
from monitor.ledger_reader import get_ledger_status
from utils.calc_services import CalcServices
from datetime import datetime
from zoneinfo import ZoneInfo
from core.core_imports import ALERT_LIMITS_PATH, DB_PATH, JsonManager, get_locker

def get_dashboard_context():
    dl = get_locker()
    positions = PositionService.get_all_positions(DB_PATH) or []

    for pos in positions:
        wallet_name = pos.get("wallet") or pos.get("wallet_name") or "Unknown"
        pos["wallet_image"] = wallet_name

    calc = CalcServices()
    totals = {
        "total_collateral": sum(float(p.get("collateral", 0)) for p in positions),
        "total_value": sum(float(p.get("value", 0)) for p in positions),
        "total_size": sum(float(p.get("size", 0)) for p in positions),
        "avg_leverage": (sum(float(p.get("leverage", 0)) for p in positions) / len(positions)) if positions else 0,
        "avg_travel_percent": (sum(float(p.get("travel_percent", 0)) for p in positions) / len(positions)) if positions else 0,
        "avg_heat_index": calc.calculate_totals(positions).get("avg_heat_index", 0.0)  # ✅ critical fix
    }

    jm = JsonManager()
    alert_limits = jm.load(ALERT_LIMITS_PATH, JsonType.ALERT_LIMITS)
    portfolio_limits = alert_limits.get("total_portfolio_limits", {})

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

    return {
        "theme_mode": dl.get_theme_mode(),
        "positions": positions,
        "liquidation_positions": positions,
        "portfolio_value": "${:,.2f}".format(totals["total_value"]),
        "portfolio_change": "N/A",
        "totals": totals,
        "ledger_info": ledger_info,
        "status_items": [],
        "monitor_items": [],
        "portfolio_limits": portfolio_limits
    }

