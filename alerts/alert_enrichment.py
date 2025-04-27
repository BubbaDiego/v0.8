import logging
from utils.json_manager import JsonManager, JsonType
from data.models import AlertType


def normalize_alert_type(alert: dict) -> dict:
    if "alert_type" not in alert or not alert["alert_type"]:
        raise ValueError("Alert missing alert_type.")

    normalized = alert["alert_type"].upper().replace(" ", "").replace("_", "")

    mapping = {
        "TRAVELPERCENT": AlertType.TRAVEL_PERCENT_LIQUID.value,
        "TRAVELPERCENTLIQUID": AlertType.TRAVEL_PERCENT_LIQUID.value,
        "PRICETHRESHOLD": AlertType.PRICE_THRESHOLD.value,
        "PROFITALERT": AlertType.PROFIT.value,
        "HEATINDEX": AlertType.HEAT_INDEX.value,
        "DELTACHANGE": AlertType.DELTA_CHANGE.value,
        "TIME": AlertType.TIME.value
    }
    alert["alert_type"] = mapping.get(normalized, alert["alert_type"])
    return alert


def enrich_alert_data(alert: dict, data_locker, logger, alert_controller) -> dict:
    alert = normalize_alert_type(alert)
    alert_type = alert.get("alert_type")

    jm = JsonManager()
    alert_limits = jm.load("", JsonType.ALERT_LIMITS)

    if alert_type == AlertType.PRICE_THRESHOLD.value:
        asset = alert.get("asset_type", "BTC")
        price_conf = alert_limits.get("alert_ranges", {}).get("price_alerts", {}).get(asset, {})
        if price_conf:
            alert["trigger_value"] = price_conf.get("trigger_value", 0.0)
            alert["condition"] = price_conf.get("condition", "ABOVE")
            alert["notification_type"] = "Call" if price_conf.get("notifications", {}).get("call") else "Email"

        price_record = data_locker.get_latest_price(asset)
        alert["evaluated_value"] = price_record.get("current_price", 0.0) if price_record else 0.0

    elif alert_type == AlertType.TRAVEL_PERCENT_LIQUID.value:
        travel_conf = alert_limits.get("alert_ranges", {}).get("travel_percent_liquid_ranges", {})
        if travel_conf.get("enabled", False):
            alert["trigger_value"] = travel_conf.get("low", -25.0)
            alert["condition"] = "BELOW"

        positions = data_locker.read_positions()
        position = next((p for p in positions if p.get("id") == alert.get("position_reference_id")), None)
        if position:
            alert["evaluated_value"] = position.get("travel_percent", 0.0)

    elif alert_type == AlertType.PROFIT.value:
        profit_conf = alert_limits.get("alert_ranges", {}).get("profit_ranges", {})
        if profit_conf.get("enabled", False):
            alert["trigger_value"] = profit_conf.get("low", 22.0)
            alert["condition"] = "ABOVE"

        positions = data_locker.read_positions()
        position = next((p for p in positions if p.get("id") == alert.get("position_reference_id")), None)
        if position:
            alert["evaluated_value"] = position.get("pnl_after_fees_usd", 0.0)

    elif alert_type == AlertType.HEAT_INDEX.value:
        heat_conf = alert_limits.get("alert_ranges", {}).get("heat_index_ranges", {})
        if heat_conf.get("enabled", False):
            alert["trigger_value"] = heat_conf.get("low", 7.0)
            alert["condition"] = "ABOVE"

        positions = data_locker.read_positions()
        position = next((p for p in positions if p.get("id") == alert.get("position_reference_id")), None)
        if position:
            alert["evaluated_value"] = position.get("current_heat_index", 0.0)

    else:
        logger.warning(f"Unknown alert type during enrichment: {alert_type}")

    return alert
