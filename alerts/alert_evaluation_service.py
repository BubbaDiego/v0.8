from data.alert import AlertLevel, Condition
from utils.console_logger import ConsoleLogger as log
from utils.config_loader import load_config

class AlertEvaluationService:
    def __init__(self, config_path="alert_limits.json", thresholds=None):
        if thresholds:
            self.thresholds = thresholds
        else:
            self.thresholds = load_config(config_path).get("alert_limits", {})  # fixed key

    def evaluate(self, alert):
        """
        Evaluate an alert by comparing evaluated_value against dynamic thresholds.
        Sets alert.level accordingly.
        """
        try:
            log.debug(f"🧪 Evaluating alert ID={alert.id}, Type={alert.alert_type}, Evaluated={alert.evaluated_value}", source="AlertEvaluation")

            if alert.evaluated_value is None:
                log.error(f"❌ Cannot evaluate alert {alert.id} - evaluated_value is None.", source="AlertEvaluation")
                alert.level = AlertLevel.NORMAL
                return alert

            alert_type_key = alert.alert_type.value.lower() + "_ranges"
            log.debug(f"🔑 Mapped alert_type to config key: {alert_type_key}", source="AlertEvaluation")

            thresholds = self.thresholds.get(alert_type_key, {})
            if not thresholds:
                log.warning(f"⚠️ No thresholds found for alert type {alert_type_key}. Defaulting to trigger_value.", source="AlertEvaluation")
                return self._simple_trigger_evaluation(alert)

            low = thresholds.get("low")
            medium = thresholds.get("medium")
            high = thresholds.get("high")

            if None in (low, medium, high):
                log.warning(f"⚠️ Incomplete thresholds for alert type {alert_type_key}.", source="AlertEvaluation")
                return self._simple_trigger_evaluation(alert)

            evaluated = alert.evaluated_value
            condition = alert.condition

            log.debug(f"📊 Thresholds → low={low}, medium={medium}, high={high}", source="AlertEvaluation")
            log.debug(f"📈 Value={evaluated}, Condition={condition}", source="AlertEvaluation")

            # Evaluate level
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
