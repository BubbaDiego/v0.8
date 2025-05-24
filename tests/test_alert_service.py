import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from alert_core.alert_service import AlertService
from data.alert import Alert, AlertLevel

@pytest.mark.asyncio
async def test_alert_service_process_all_alerts_triggers_notifications():
    # Mock repository
    repo = MagicMock()
    repo.get_active_alerts = AsyncMock(return_value=[
        Alert(
            id="alert-123",
            alert_type="PriceThreshold",
            asset="BTC",
            trigger_value=50000,
            evaluated_value=60000,
            condition="ABOVE",
            level=AlertLevel.NORMAL
        )
    ])
    repo.update_alert_level = AsyncMock()

    # Mock enrichment
    enrichment = MagicMock()
    enrichment.enrich = AsyncMock(side_effect=lambda alert: alert)

    # Mock config loader
    config_loader = lambda: {
        "alert_ranges": {
            "price_alerts": {
                "BTC": {"trigger_value": 50000, "enabled": True, "condition": "ABOVE"}
            }
        }
    }

    # Mock notification service
    notification_service = MagicMock()
    notification_service.send_alert = AsyncMock(return_value=True)

    # Patch AlertService to inject our notification_service mock
    service = AlertService(repo, enrichment, config_loader)
    service.notification_service = notification_service

    # Run
    await service.process_all_alerts()

    # Assertions
    repo.get_active_alerts.assert_awaited_once()
    enrichment.enrich.assert_awaited()
    notification_service.send_alert.assert_awaited()
    repo.update_alert_level.assert_awaited()
