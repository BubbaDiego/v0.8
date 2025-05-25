from __future__ import annotations


class NotificationService:
    """Very small stub used for tests."""

    def __init__(self, config_loader=None):
        self.config_loader = config_loader or (lambda: {})

    async def send_alert(self, alert) -> bool:
        """Pretend to dispatch an alert notification."""
        return True
