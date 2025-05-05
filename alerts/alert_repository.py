from data.alert import Alert, AlertLevel
import asyncio
from utils.console_logger import ConsoleLogger as log


class AlertRepository:
    def __init__(self, data_locker):
        self.data_locker = data_locker

    def create_alert(self, alert_dict):
        """Insert a new alert into the database."""
        # Ensure starting_value is captured at creation time if not manually provided
        if "starting_value" not in alert_dict or alert_dict["starting_value"] is None:
            try:
                current = self.data_locker.get_current_value(alert_dict["asset"])
                alert_dict["starting_value"] = current
                log.debug(f"[create_alert] Injected starting_value: {current}", source="AlertRepository")
            except Exception as e:
                log.warning(f"[create_alert] Could not fetch starting_value for {alert_dict['asset']}: {e}", source="AlertRepository")

        return self.data_locker.create_alert(alert_dict)

    def get_active_alerts(self) -> list[Alert]:
        alerts_raw = self.data_locker.get_alerts()

        if not alerts_raw:
            log.warning("No alerts found in database.", source="AlertRepository")
            return []

        log.info(f"Loaded {len(alerts_raw)} alerts from database.", source="AlertRepository")

        alerts = []
        for a in alerts_raw:
            try:
                # 🧼 HARD SANITIZE LEVEL FIELD
                level_raw = a.get("level", "Normal")
                if isinstance(level_raw, str):
                    level_clean = level_raw.strip().capitalize()
                    if level_clean not in {"Normal", "Low", "Medium", "High"}:
                        a["level"] = "Normal"
                    else:
                        a["level"] = level_clean
                else:
                    a["level"] = "Normal"

                # Ensure starting_value exists (fallback for legacy)
                if "starting_value" not in a:
                    a["starting_value"] = a.get("trigger_value", 0)

                alerts.append(Alert(**a))
            except Exception as e:
                log.warning(f"⚠️ Failed to parse alert {a.get('id', '?')} — {str(e)}", source="AlertRepository")

        return alerts

    async def update_alert_level(self, alert_id: str, new_level):
        await asyncio.sleep(0)  # simulate async
        try:
            level_value = getattr(new_level, "value", str(new_level))
            self.data_locker.update_alert_conditions(alert_id, {
                "level": level_value,
                "last_triggered": self.data_locker.get_current_timestamp()
            })
            log.success(f"Updated alert {alert_id} to level {level_value}.", source="AlertRepository")
        except Exception as e:
            log.error(f"Failed to update alert {alert_id}: {e}", source="AlertRepository")
