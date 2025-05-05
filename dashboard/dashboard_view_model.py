# dashboard_view_model.py

from data.alert import Alert
from utils.console_logger import ConsoleLogger as logger
from alerts.alert_repository import AlertRepository
from alerts.alert_repository import AlertRepository
from data.data_locker import DataLocker  # ✅ required for fallback

class DashboardViewModel:
    def __init__(self, data_locker=None):
        if data_locker is None:
            data_locker = DataLocker()  # 🔥 fallback
        self.alert_repo = AlertRepository(data_locker)

    def get_alerts(self):
        alerts = self.alert_repo.get_active_alerts()
        return [a.model_dump() for a in alerts]

    def build_dashboard_alerts(self):
        raw_alerts = self.alert_repo.get_all()  # or get_active()
        parsed_alerts = []

        for row in raw_alerts:
            try:
                data = dict(row) if not isinstance(row, dict) else row
                alert = Alert(**data)

                alert_dict = {
                    "id": str(alert.id),
                    "asset": alert.asset,
                    "alert_class": alert.alert_class,
                    "alert_type": getattr(alert.alert_type, 'value', str(alert.alert_type)),
                    "trigger_value": alert.trigger_value,
                    "condition": getattr(alert.condition, 'value', str(alert.condition)),
                    "evaluated_value": alert.evaluated_value,
                    "level": getattr(alert.level, 'value', str(alert.level)),
                    "status": getattr(alert.status, 'value', str(alert.status)),
                    "notes": alert.notes,
                    "description": alert.description,
                    "position_type": alert.position_type,
                    "notification_type": getattr(alert.notification_type, 'value', str(alert.notification_type)),
                }

                parsed_alerts.append(alert_dict)

            except Exception as e:
                logger.warning(f"[DashboardViewModel] ⚠️ Failed to parse alert {row.get('id', '?')}: {e}")

        logger.info(f"[DashboardViewModel] ✅ Prepared {len(parsed_alerts)} alerts")
        return parsed_alerts
