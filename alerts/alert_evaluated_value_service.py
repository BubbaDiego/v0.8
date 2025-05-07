# alerts/alert_evaluated_value_service.py

from utils.console_logger import ConsoleLogger as log
from utils.json_manager import JsonManager


class AlertEvaluatedValueServicez:
    def __init__(self, dashboard_context: callable = None):
        from dashboard.dashboard_service import get_dashboard_context
        self.get_dashboard_context = dashboard_context or get_dashboard_context

    def get_portfolio_metric_value(self, alert) -> float | None:
        log.debug(f"📥 Processing evaluated_value for Portfolio alert {alert.id}", source="EvalValue")

        if not alert.description:
            log.error("❌ Missing description field in alert (used for metric resolution)", source="EvalValue")
            return None

        try:
            metric = alert.description.strip().lower()
            context = self.get_dashboard_context()
            totals = context.get("totals", {})

            key_map = {
                "total_value": totals.get("total_value"),
                "total_collateral": totals.get("total_collateral"),
                "total_size": totals.get("total_size"),
                "avg_leverage": totals.get("avg_leverage"),
                "avg_travel_percent": totals.get("avg_travel_percent"),
                "value_to_collateral_ratio": (
                    totals.get("total_value") / totals.get("total_collateral")
                    if totals.get("total_collateral") else None
                ),
                "total_heat": totals.get("avg_heat_index")
            }

            aliases = {
                "total_heat": ["avg_heat_index", "heat_index", "heat"],
                "value_to_collateral_ratio": ["vcr", "collateral_ratio", "valuecollateral"],
                "avg_travel_percent": ["travel", "travel_percent", "avgtravel"]
            }

            json_mgr = JsonManager()
            resolved_key = json_mgr.resolve_key_fuzzy(metric, key_map, aliases=aliases)
            value = key_map.get(resolved_key)

            log.debug(f"🔍 Requested metric: {metric}", source="EvalValue")
            log.debug(f"🔑 Resolved key: {resolved_key}", source="EvalValue")
            log.debug("📦 Available keys:", source="EvalValue", payload={"keys": list(key_map.keys())})

            if value is None:
                log.warning("⚠️ Failed to extract evaluated_value", source="EvalValue", payload={
                    "metric": metric,
                    "resolved_key": resolved_key,
                    "totals_keys": list(totals.keys())
                })

            return value

        except Exception as e:
            log.error(f"❌ Error resolving evaluated_value for Portfolio alert {alert.id}: {e}", source="EvalValue")
            return None
