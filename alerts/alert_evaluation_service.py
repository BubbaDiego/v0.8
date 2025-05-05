import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.alert import AlertLevel, Condition
from utils.console_logger import ConsoleLogger as log
from config.config_loader import load_config
from data.alert import AlertType
from config.config_constants import ALERT_LIMITS_PATH
#config_loader = lambda: load_config(str(ALERT_LIMITS_PATH)) or {}


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
        """
        Special evaluator for portfolio alerts using total_*_limits thresholds.
        Metric name is derived from description/notes.
        """
        try:
            metric = alert.description or alert.notes or ""
            metric_key = metric.strip().lower().replace(" ", "_") + "_limits"
            portfolio_limits = self.thresholds.get("total_portfolio_limits", {})
            thresholds = portfolio_limits.get(metric_key)

            if not thresholds:
                log.warning(f"⚠️ No thresholds for portfolio metric {metric_key}.", source="AlertEvaluation")
                return self._simple_trigger_evaluation(alert)

            value = alert.evaluated_value
            condition = alert.condition

            low = thresholds.get("low")
            medium = thresholds.get("medium")
            high = thresholds.get("high")

            log.debug(f"📊 Portfolio thresholds ({metric_key}) → low={low}, medium={medium}, high={high}",
                      source="AlertEvaluation")

            if condition == Condition.ABOVE:
                if value >= high:
                    alert.level = AlertLevel.HIGH
                elif value >= medium:
                    alert.level = AlertLevel.MEDIUM
                elif value >= low:
                    alert.level = AlertLevel.LOW
                else:
                    alert.level = AlertLevel.NORMAL
            elif condition == Condition.BELOW:
                if value <= high:
                    alert.level = AlertLevel.HIGH
                elif value <= medium:
                    alert.level = AlertLevel.MEDIUM
                elif value <= low:
                    alert.level = AlertLevel.LOW
                else:
                    alert.level = AlertLevel.NORMAL
            else:
                alert.level = AlertLevel.NORMAL

            log.success(f"✅ Portfolio alert evaluated: {metric}={value} → {alert.level}", source="AlertEvaluation")
            return alert

        except Exception as e:
            log.error(f"❌ Exception in portfolio evaluation for alert {alert.id}: {e}", source="AlertEvaluation")
            alert.level = AlertLevel.NORMAL
            return alert

    def _evaluate_position(self, alert):
        """
        Handles evaluation of Position alerts using alert-type-specific thresholds.
        """
        type_key_map = {
            "profit": "profit_ranges",
            "heatindex": "heat_index_ranges",
            "travelpercentliquid": "travel_percent_liquid_ranges",
            "pricethreshold": "price_alerts"
        }

        if not alert.alert_type:
            log.error(f"❌ Cannot evaluate: missing alert_type on alert {alert.id}", source="AlertEvaluation")
            alert.level = AlertLevel.NORMAL
            return alert

        # 🔧 Remove Enum wrapper (i.e., 'AlertType.Profit' → 'profit')
        alert_type_str = str(alert.alert_type).lower().replace("alerttype.", "")
        alert_type_key = type_key_map.get(alert_type_str)

        if not alert_type_key:
            log.warning(f"⚠️ Unknown alert type '{alert.alert_type}' → using fallback eval", source="AlertEvaluation")
            return self._simple_trigger_evaluation(alert)

        thresholds = self.thresholds.get(alert_type_key)
        if thresholds:
            return self._evaluate_against(alert, thresholds)

        log.warning(f"⚠️ No thresholds found for key '{alert_type_key}'", source="AlertEvaluation")
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
