from __future__ import annotations

from data.alert import Alert


class AlertRepository:
    """Lightweight repository wrapping a data locker-like backend."""

    def __init__(self, data_locker):
        self.data_locker = data_locker

    def create_alert(self, alert_data: dict):
        if "starting_value" not in alert_data:
            getter = getattr(self.data_locker, "get_current_value", None)
            if callable(getter):
                alert_data["starting_value"] = getter(alert_data.get("asset"))

        if hasattr(self.data_locker, "create_alert"):
            return self.data_locker.create_alert(alert_data)
        if hasattr(self.data_locker, "alerts") and hasattr(self.data_locker.alerts, "create_alert"):
            return self.data_locker.alerts.create_alert(alert_data)
        if hasattr(self.data_locker, "alerts") and isinstance(self.data_locker.alerts, list):
            self.data_locker.alerts.append(Alert(**alert_data))
            return alert_data
        raise AttributeError("DataLocker does not support alert creation")

    async def get_active_alerts(self) -> list[Alert]:
        if hasattr(self.data_locker, "get_alerts"):
            raw = self.data_locker.get_alerts()
        elif hasattr(self.data_locker, "alerts") and hasattr(self.data_locker.alerts, "get_all_alerts"):
            raw = self.data_locker.alerts.get_all_alerts()
        elif hasattr(self.data_locker, "alerts"):
            raw = self.data_locker.alerts
        else:
            raw = []
        alerts = []
        for a in raw:
            if isinstance(a, Alert):
                alerts.append(a)
            elif isinstance(a, dict):
                alerts.append(Alert(**a))
        return alerts

    async def update_alert_level(self, alert_id: str, level):
        update = {"level": level}
        self._update(alert_id, update)

    async def update_alert_evaluated_value(self, alert_id: str, value: float):
        update = {"evaluated_value": value}
        self._update(alert_id, update)

    # ------------------------------------------------------------------
    def _update(self, alert_id: str, fields: dict) -> None:
        if hasattr(self.data_locker, "update_alert_conditions"):
            self.data_locker.update_alert_conditions(alert_id, fields)
        elif hasattr(self.data_locker, "alerts") and hasattr(self.data_locker.alerts, "update_alert_conditions"):
            self.data_locker.alerts.update_alert_conditions(alert_id, fields)
        elif hasattr(self.data_locker, "alerts") and isinstance(self.data_locker.alerts, list):
            for a in self.data_locker.alerts:
                if getattr(a, "id", None) == alert_id:
                    for k, v in fields.items():
                        setattr(a, k, v)
                    break
