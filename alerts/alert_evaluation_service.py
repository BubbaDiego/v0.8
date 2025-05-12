import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data.alert import AlertLevel, Condition
from config.config_loader import load_config
from data.alert import AlertType
from core.constants import ALERT_LIMITS_PATH

from utils.fuzzy_wuzzy import fuzzy_match_enum
from utils.json_manager import JsonManager, JsonType
from core.logging import log

log.debug_module()


class AlertEvaluationService:
    def __init__(self, config_path=str(ALERT_LIMITS_PATH), thresholds=None):
        if thresholds:
            self.thresholds = thresholds
        else:
            self.thresholds = load_config(config_path).get("alert_limits", {})

    def evaluate(self, alert):
        try:
            if alert.evaluated_value is None:
                log.error(f"❌ Missing evaluated_value for alert {alert.id}", source="AlertEvaluation")
                alert.level = AlertLevel.NORMAL
                return alert

            alert_class = str(alert.alert_class).strip().lower()
            raw_type = str(alert.alert_type).strip()

            # 🔍 Try to resolve AlertType enum (works for both legacy & new)
            enum_type = fuzzy_match_enum(raw_type.split('.')[-1], AlertType)

            if not enum_type:
                log.warning(f"⚠️ Unable to resolve AlertType from: {raw_type}", source="AlertEvaluation")
                return self._evaluate(alert)

            # ✅ Route portfolio-class alerts using type-based evaluator
            if alert_class == "portfolio":
                return self._evaluate_portfolio(alert)

            # ✅ Route position-class alerts
            if alert_class == "position":
                return self._evaluate_position(alert)

            log.warning(
                f"⚠️ Unknown alert class '{alert_class}', using fallback _evaluate for {alert.id}",
                source="AlertEvaluation"
            )
            return self._evaluate(alert)

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
            config = load_config(ALERT_LIMITS_PATH)
            alert_limits = config.get("alert_limits", config)
            total_limits = alert_limits.get("total_portfolio_limits", {})

            raw_type = str(alert.alert_type)
            enum_type = fuzzy_match_enum(raw_type.split('.')[-1], AlertType)

            if not enum_type:
                log.warning(f"⚠️ Unable to resolve AlertType enum from: {raw_type}", source="AlertEvaluation")
                return alert

            alert_key_map = {
                AlertType.TOTAL_VALUE: "total_value",
                AlertType.TOTAL_SIZE: "total_size",
                AlertType.TOTAL_LEVERAGE: "avg_leverage",
                AlertType.TOTAL_RATIO: "value_to_collateral_ratio",
                AlertType.TOTAL_TRAVEL_PERCENT: "avg_travel_percent",
                AlertType.TOTAL_HEAT_INDEX: "total_heat",
            }

            metric_key = alert_key_map.get(enum_type)
            if not metric_key:
                log.warning(f"⚠️ No portfolio key mapped for alert type: {enum_type}", source="AlertEvaluation")
                return alert

            resolved_key = f"{metric_key}_limits"
            thresholds = total_limits.get(resolved_key)

            if not thresholds:
                log.warning(f"⚠️ No thresholds found for key: {resolved_key}", source="AlertEvaluation")
                return alert

            value = alert.evaluated_value
            if value is None:
                log.warning(f"⚠️ Missing evaluated_value for alert {alert.id}", source="AlertEvaluation")
                return alert

            low = thresholds.get("low")
            medium = thresholds.get("medium")
            high = thresholds.get("high")

            log.debug(
                f"📈 Evaluating {enum_type.value} → {value} against {resolved_key}: low={low}, medium={medium}, high={high}",
                source="AlertEvaluation")

            if value >= high:
                alert.level = AlertLevel.HIGH
            elif value >= medium:
                alert.level = AlertLevel.MEDIUM
            elif value >= low:
                alert.level = AlertLevel.LOW
            else:
                alert.level = AlertLevel.NORMAL

            log.success(f"✅ Evaluated {enum_type.value} alert: {value} → level={alert.level}", source="AlertEvaluation")
            return alert

        except Exception as e:
            log.error(f"❌ Portfolio evaluation failed for alert {alert.id}: {e}", source="AlertEvaluation")
            alert.level = AlertLevel.NORMAL
            return alert

    def _evaluate_position(self, alert):
        try:
            raw_type = str(alert.alert_type)
            enum_type = fuzzy_match_enum(raw_type.split('.')[-1], AlertType)

            if not enum_type:
                log.warning(f"⚠️ Unable to fuzzy match alert type: {raw_type}", source="AlertEvaluation")
                return self._evaluate(alert)

            alert_type_str = enum_type.name.lower()

            type_key_map = {
                "profit": "profit_ranges",
                "heatindex": "heat_index_ranges",
                "travelpercentliquid": "travel_percent_liquid_ranges"
            }

            alert_type_key = type_key_map.get(alert_type_str)
            if not alert_type_key:
                log.warning(f"⚠️ No config key mapping for alert type: {alert_type_str}", source="AlertEvaluation")
                return self._evaluate(alert)

            thresholds = self.thresholds.get(alert_type_key)
            if not thresholds or not thresholds.get("enabled", False):
                log.warning(f"⚠️ Thresholds not found or disabled for key: {alert_type_key}", source="AlertEvaluation")
                return self._evaluate(alert)

            log.debug(
                f"🐻 Thresholds for {alert_type_key}: low={thresholds.get('low')} | "
                f"medium={thresholds.get('medium')} | high={thresholds.get('high')}",
                source="AlertEvaluation"
            )

            return self._evaluate_against(alert, thresholds)

        except Exception as e:
            log.error(f"❌ Evaluation error for alert {alert.id}: {e}", source="AlertEvaluation")
            return self._evaluate(alert)

    def _evaluate(self, alert):
        try:
            evaluated = alert.evaluated_value
            trigger = alert.trigger_value
            condition = alert.condition

            log.debug(f"📈 Raw Evaluation: Value={evaluated}, Trigger={trigger}, Condition={condition}", source="AlertEvaluation")

            if condition == Condition.ABOVE and evaluated >= trigger:
                alert.level = AlertLevel.HIGH
            elif condition == Condition.BELOW and evaluated <= trigger:
                alert.level = AlertLevel.HIGH
            else:
                alert.level = AlertLevel.NORMAL

            log.info(f"ℹ️ Default fallback evaluation for alert {alert.id}. Level: {alert.level}", source="AlertEvaluation")
            return alert
        except Exception as e:
            log.error(f"❌ Evaluation fallback error for alert {alert.id}: {e}", source="AlertEvaluation")
            alert.level = AlertLevel.NORMAL
            return alert

    def inject_repo(self, repo):
        self.repo = repo

    def update_alert_evaluated_value(self, alert_id: str, value: float):
        if not self.repo:
            log.error("❌ Alert repository not injected", source="AlertEvaluation")
            return
        try:
            cursor = self.repo.data_locker.db.get_cursor()
            cursor.execute(
                "UPDATE alerts SET evaluated_value = ? WHERE id = ?", (value, alert_id)
            )
            self.repo.data_locker.db.commit()

            log.success(
                f"✅ Updated evaluated_value",
                source="AlertEvaluation",
                payload={"alert_id": alert_id, "evaluated_value": value},
            )
        except Exception as e:
            log.error(
                f"❌ Failed to update evaluated_value",
                source="AlertEvaluation",
                payload={"alert_id": alert_id, "error": str(e)},
            )

    def update_alert_level(self, alert_id: str, level):
        if not self.repo:
            log.error("❌ Alert repository not injected", source="AlertEvaluation")
            return
        try:
            level_str = level.value if hasattr(level, "value") else str(level).capitalize()

            cursor = self.repo.data_locker.db.get_cursor()
            cursor.execute(
                "UPDATE alerts SET level = ? WHERE id = ?", (level_str, alert_id)
            )
            self.repo.data_locker.db.commit()

            log.success(
                "🧪 Updated alert level",
                source="AlertEvaluation",
                payload={"alert_id": alert_id, "level": level_str},
            )
        except Exception as e:
            log.error(
                "❌ Failed to update alert level",
                source="AlertEvaluation",
                payload={"alert_id": alert_id, "error": str(e)},
            )
