from config.config_loader import load_config
from data.alert import AlertType
from core.core_imports import ALERT_LIMITS_PATH


def get_default_trigger_value(alert_type: AlertType) -> float:
    """
    Returns the default trigger value from alert_limitsz.json based on the alert_type.
    """
    config = load_config(ALERT_LIMITS_PATH)
    alert_limits = config.get("alert_limits", config)

    # Handle Position alert types (heat_index, profit, travel_percent)
    mapping = {
        AlertType.HeatIndex: ("heat_index_ranges", "medium"),
        AlertType.Profit: ("profit_ranges", "medium"),
        AlertType.TravelPercentLiquid: ("travel_percent_liquid_ranges", "medium"),
        AlertType.PriceThreshold: ("price_alerts", None),  # special case
    }

    # Portfolio alert metrics
    portfolio_map = {
        AlertType.TotalValue: "total_value_limits",
        AlertType.TotalSize: "total_size_limits",
        AlertType.AvgLeverage: "avg_leverage_limits",
        AlertType.AvgTravelPercent: "avg_travel_percent_limits",
        AlertType.ValueToCollateralRatio: "value_to_collateral_ratio_limits",
        AlertType.TotalHeat: "total_heat_limits",
    }

    if alert_type in mapping:
        key, level = mapping[alert_type]
        if key in alert_limits and level in alert_limits[key]:
            return alert_limits[key][level]

    elif alert_type in portfolio_map:
        key = portfolio_map[alert_type]
        tpl = alert_limits.get("total_portfolio_limits", {})
        if key in tpl and "medium" in tpl[key]:
            return tpl[key]["medium"]

    # Fallback default
    return 50.0
