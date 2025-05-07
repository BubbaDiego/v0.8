import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.alert import AlertLevel, Condition
from utils.console_logger import ConsoleLogger as log
from config.config_loader import load_config
from data.alert import AlertType
from config.config_constants import ALERT_LIMITS_PATH
from utils.json_manager import JsonManager

from utils.fuzzy_wuzzy import fuzzy_match_enum
#from alerts.enums import AlertType
from utils.console_logger import ConsoleLogger as log


log.debug_module()


class AlertEvaluationService:
    def __init__(self, config_path=str(ALERT_LIMITS_PATH), thresholds=None):
        if thresholds:
            self.thresholds = thresholds
        else:
            self.thresholds = load_config(config_path).get("alert_limits", {})  # fixed key

    def evaluate(self, alert):
        try:
            if alert.evaluated_value is None:
                log.error(f"❌ Missing evaluated_value for alert {alert.id}", source="AlertEvaluation")
                alert.level = AlertLevel.NORMAL
                return alert

            alert_class = str(alert.alert_class).strip().lower()

            if alert_class == "portfolio":
                return self._evaluate_portfolio(alert)

            if alert_class == "position":
                return self._evaluate_position(alert)

            return self._evaluate_standard(alert)

        except Exception as e:
            log.error(f"❌ Evaluation error for alert {alert.id}: {e}", source="AlertEvaluation")
            alert.level = AlertLevel.NORMAL
            return alert

    def _evaluate_against(self, alert, thresholds):
        low = thresholds.get("low")
        med = thresholds.get("medium")
        high = thresholds.get("high")
        val = alert.evaluated_value
        cond = alert.condition

        if cond == Condition.ABOVE:
            if val >= high:
                level = AlertLevel.HIGH
            elif val >= med:
                level = AlertLevel.MEDIUM
            elif val >= low:
                level = AlertLevel.LOW
            else:
                level = AlertLevel.NORMAL
        elif cond == Condition.BELOW:
            if val <= high:
                level = AlertLevel.HIGH
            elif val <= med:
                level = AlertLevel.MEDIUM
            elif val <= low:
                level = AlertLevel.LOW
            else:
                level = AlertLevel.NORMAL
        else:
            level = AlertLevel.NORMAL

        alert.level = level
        log.success(f"✅ Evaluation result for alert {alert.id} → level={level}", source="AlertEvaluation")
        return alert

    def _evaluate_portfolio(self, alert):
        try:
            from config.config_loader import load_config
            from config.config_constants import ALERT_LIMITS_PATH

            config = load_config(ALERT_LIMITS_PATH)
            alert_limits = config.get("alert_limits", config)
            total_limits = alert_limits.get("total_portfolio_limits", {})

            # 🔍 Get the metric being evaluated
            metric = (alert.description or "").strip().lower()
            raw_key = f"{metric}_limits"

            # 🔁 Alias map for fallback matching
            aliases = {
                "total_heat_limits": ["avg_heat_index_limits", "heat_index_limits", "heat_limits"],
                "value_to_collateral_ratio_limits": ["vcr_limits", "valuecollateral_limits", "ratio_limits"],
                "avg_travel_percent_limits": ["travel_percent_limits", "travel_limits"]
            }

            # 🔎 Resolve key using fuzzy + aliases
            json_mgr = JsonManager()
            resolved_key = json_mgr.resolve_key_fuzzy(raw_key, total_limits, aliases=aliases)
            thresholds = total_limits.get(resolved_key)

            log.debug(f"📊 Evaluating Portfolio Alert {alert.id} → description='{metric}' → key='{resolved_key}'",
                      source="AlertEvaluation")

            if not thresholds:
                log.warning(
                    f"⚠️ Thresholds not found for '{metric}'. Resolved key: '{resolved_key}'",
                    source="AlertEvaluation",
                    payload={"available_keys": list(total_limits.keys())}
                )
                return alert

            value = alert.evaluated_value
            if value is None:
                log.warning(f"⚠️ Missing evaluated_value for alert {alert.id}", source="AlertEvaluation")
                return alert

            # 🧠 Evaluate thresholds
            low = thresholds.get("low")
            medium = thresholds.get("medium")
            high = thresholds.get("high")

            log.debug(f"📈 Thresholds for {resolved_key}: low={low}, medium={medium}, high={high}",
                      source="AlertEvaluation")

            if value >= high:
                alert.level = "High"
            elif value >= medium:
                alert.level = "Medium"
            elif value >= low:
                alert.level = "Low"
            else:
                alert.level = "Normal"

            log.success(
                f"✅ Portfolio alert evaluated: {metric}={value} → AlertLevel.{alert.level.upper()}",
                source="AlertEvaluation"
            )

            return alert

        except Exception as e:
            log.error(f"❌ Portfolio evaluation failed for alert {alert.id}: {e}", source="AlertEvaluation")
            return alert

    def _evaluate_position(self, alert):
        try:
            raw_type = str(alert.alert_type)
            enum_type = fuzzy_match_enum(raw_type.split('.')[-1], AlertType)

            if not enum_type:
                log.warning(f"⚠️ Unable to fuzzy match alert type: {raw_type}", source="AlertEvaluation")
                return self._simple_trigger_evaluation(alert)

            alert_type_str = enum_type.name.lower()

            type_key_map = {
                "profit": "profit_ranges",
                "heatindex": "heat_index_ranges",
                "travelpercentliquid": "travel_percent_liquid_ranges"
            }

            alert_type_key = type_key_map.get(alert_type_str)
            if not alert_type_key:
                log.warning(f"⚠️ No config key mapping for alert type: {alert_type_str}", source="AlertEvaluation")
                return self._simple_trigger_evaluation(alert)

            thresholds = self.thresholds.get(alert_type_key)
            if not thresholds or not thresholds.get("enabled", False):
                log.warning(f"⚠️ Thresholds not found or disabled for key: {alert_type_key}", source="AlertEvaluation")
                return self._simple_trigger_evaluation(alert)

            # 🐻 Confirm loaded thresholds
            log.debug(
                f"🐻 Thresholds for {alert_type_key}: low={thresholds.get('low')} | "
                f"medium={thresholds.get('medium')} | high={thresholds.get('high')}",
                source="AlertEvaluation"
            )

            return self._evaluate_against(alert, thresholds)

        except Exception as e:
            log.error(f"❌ Evaluation error for alert {alert.id}: {e}", source="AlertEvaluation")
            return self._simple_trigger_evaluation(alert)


    def _simple_trigger_evaluation(self, alert):
        """
        Fallback simple evaluation based only on alert.trigger_value.
        """
        try:
            evaluated = alert.evaluated_value
            trigger = alert.trigger_value
            condition = alert.condition

            log.debug(f"📈 Simple Eval: Value={evaluated}, Trigger={trigger}, Condition={condition}", source="AlertEvaluation")

            if condition == Condition.ABOVE and evaluated >= trigger:
                alert.level = AlertLevel.HIGH
            elif condition == Condition.BELOW and evaluated <= trigger:
                alert.level = AlertLevel.HIGH
            else:
                alert.level = AlertLevel.NORMAL

            log.info(f"ℹ️ Simple evaluation used for alert {alert.id}. Result level: {alert.level}", source="AlertEvaluation")
            return alert
        except Exception as e:
            log.error(f"❌ Simple evaluation error for alert {alert.id}: {e}", source="AlertEvaluation")
            alert.level = AlertLevel.NORMAL
            return alert
