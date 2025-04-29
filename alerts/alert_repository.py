from data.alert import Alert, AlertLevel
import asyncio
from utils.console_logger import ConsoleLogger as log  # <-- NEW

class AlertRepository:
    def __init__(self, data_locker):
        self.data_locker = data_locker

    def create_alert(self, alert_dict):
        """Insert a new alert into the database."""
        return self.data_locker.create_alert(alert_dict)

    async def get_active_alerts(self) -> list[Alert]:
        """
        Fetch active alerts from the database.
        """
        await asyncio.sleep(0)  # simulate async
        alerts_raw = self.data_locker.get_alerts()

        if not alerts_raw:
            log.warning("No alerts found in database.", source="AlertRepository")
            return []

        log.info(f"Loaded {len(alerts_raw)} alerts from database.", source="AlertRepository")

        alerts = []
        for a in alerts_raw:
            try:
                alerts.append(Alert(**a))
            except Exception as e:
                log.error(f"Failed to parse alert record: {e}", source="AlertRepository")
        return alerts

    async def update_alert_level(self, alert_id: str, new_level: AlertLevel):
        """
        Update alert's level and last triggered timestamp.
        """
        await asyncio.sleep(0)  # simulate async
        try:
            self.data_locker.update_alert_conditions(alert_id, {
                "level": new_level,
                "last_triggered": self.data_locker.get_current_timestamp()
            })
            log.success(f"Updated alert {alert_id} to level {new_level}.", source="AlertRepository")
        except Exception as e:
            log.error(f"Failed to update alert {alert_id}: {e}", source="AlertRepository")
