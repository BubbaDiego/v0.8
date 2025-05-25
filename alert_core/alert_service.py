from __future__ import annotations

import inspect

from xcom.notification_service import NotificationService
from data.alert import Alert
from core.logging import log


class AlertService:
    """High level coordinator for alert processing."""

    def __init__(self, repository, enrichment_service, config_loader=None):
        self.repository = repository
        self.enrichment_service = enrichment_service
        self.config_loader = config_loader or (lambda: {})
        self.notification_service = NotificationService(self.config_loader)

    async def process_all_alerts(self) -> None:
        alerts = await self.repository.get_active_alerts()
        for alert in alerts:
            enriched = await self.enrichment_service.enrich(alert)
            await self.repository.update_alert_evaluated_value(
                enriched.id, getattr(enriched, "evaluated_value", None)
            )
            await self.repository.update_alert_level(
                enriched.id, getattr(enriched, "level", None)
            )
            try:
                await self.notification_service.send_alert(enriched)
            except Exception as e:  # pragma: no cover - notification best effort
                log.error(f"Notification failed for {enriched.id}: {e}", source="AlertService")
