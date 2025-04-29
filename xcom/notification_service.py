from data.alert import AlertLevel, Alert
from xcom.xcom import send_email, send_sms, send_call

class NotificationService:
    def __init__(self, config_loader):
        """
        config_loader: a callable or object that returns the latest config dictionary.
        """
        self.get_config = config_loader

    async def send_alert(self, alert: Alert) -> bool:
        config = self.get_config()

        # Decide based on alert level
        if alert.level == AlertLevel.HIGH:
            message = self._build_message(alert)
            recipient = self._choose_recipient(alert, config)
            success_sms = send_sms(recipient, message, config)
            success_call = send_call(recipient, message, config)
            return success_sms and bool(success_call)
        elif alert.level == AlertLevel.MEDIUM:
            message = self._build_message(alert)
            recipient = self._choose_recipient(alert, config)
            return send_sms(recipient, message, config)
        else:  # LOW or NORMAL
            message = self._build_message(alert)
            recipient = self._choose_recipient(alert, config)
            return send_email(recipient, "Alert Notification", message, config)

    def _choose_recipient(self, alert: Alert, config: dict) -> str:
        # For now, fallback to default recipients from config
        # Can be extended based on asset, alert type, etc.
        return ""  # Empty will cause xcom to use default recipient

    def _build_message(self, alert: Alert) -> str:
        return (f"ALERT TRIGGERED:\n"
                f"Asset: {alert.asset}\n"
                f"Type: {alert.alert_type}\n"
                f"Level: {alert.level}\n"
                f"Current: {alert.evaluated_value}\n"
                f"Trigger: {alert.trigger_value}\n")
