from data.alert import AlertLevel, Condition
from utils.console_logger import ConsoleLogger as log
from utils.config_loader import load_config

class AlertEvaluationService:
    def __init__(self, config_path="alert_limits.json", thresholds=None):
        """
        If thresholds are provided explicitly (test overrides), use them.
        Otherwise load from alert_limits.json.
        """
        if thresholds:
            self.thresholds = thresholds
        else:
            self.thresholds = load_config(config_path).get("alert_ranges", {})

    def evaluate(self, alert):
        """
        Evaluate an alert by comparing evaluated_value against dynamic thresholds.
        Sets alert.level accordingly.
        """

        try:
            if alert.evaluated_value is None:
                log.error(f"❌ Cannot evaluate alert {alert.id} - evaluated_value is None.", source="AlertEvaluation")
                alert.level = AlertLevel.NORMAL
                return alert

            alert_type_key = alert.alert_type.value if hasattr(alert.alert_type, "value") else str(alert.alert_type)
            thresholds = self.thresholds.get(alert_type_key, {})

            if not thresholds:
                log.warning(f"⚠️ No thresholds found for alert type {alert_type_key}. Defaulting to trigger_value.", source="AlertEvaluation")
                # If no special thresholds, fall back to trigger_value
                return self._simple_trigger_evaluation(alert)

            low = thresholds.get("LOW")
            medium = thresholds.get("MEDIUM")
            high = thresholds.get("HIGH")

            if None in (low, medium, high):
                log.warning(f"⚠️ Incomplete thresholds for alert type {alert_type_key}.", source="AlertEvaluation")
                return self._simple_trigger_evaluation(alert)

            evaluated = alert.evaluated_value
            condition = alert.condition

            # 🚀 Evaluate depending on condition direction
            if condition == Condition.ABOVE:
                if evaluated >= high:
                    alert.level = AlertLevel.HIGH
                elif evaluated >= medium:
                    alert.level = AlertLevel.MEDIUM
                elif evaluated >= low:
                    alert.level = AlertLevel.LOW
                else:
                    alert.level = AlertLevel.NORMAL

            elif condition == Condition.BELOW:
                if evaluated <= high:
                    alert.level = AlertLevel.HIGH
                elif evaluated <= medium:
                    alert.level = AlertLevel.MEDIUM
                elif evaluated <= low:
                    alert.level = AlertLevel.LOW
                else:
                    alert.level = AlertLevel.NORMAL
            else:
                log.warning(f"⚠️ Unknown condition {condition} for alert {alert.id}", source="AlertEvaluation")
                alert.level = AlertLevel.NORMAL

            log.success(f"✅ Evaluated alert {alert.id}: evaluated_value={evaluated}, level={alert.level}", source="AlertEvaluation")
            return alert

        except Exception as e:
            log.error(f"❌ Exception during evaluation of alert {alert.id}: {e}", source="AlertEvaluation")
            alert.level = AlertLevel.NORMAL
            return alert

    def _simple_trigger_evaluation(self, alert):
        """
        Fallback simple evaluation based only on alert.trigger_value.
        """

        try:
            evaluated = alert.evaluated_value
            trigger = alert.trigger_value
            condition = alert.condition

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
