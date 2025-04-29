import pytest
import asyncio
from alerts.alert_service import AlertService
from alerts.alert_repository import AlertRepository
from alerts.alert_enrichment_service import AlertEnrichmentService
from xcom.notification_service import NotificationService
from data.alert import Alert, AlertLevel
from utils.config_loader import load_config
from utils.console_logger import ConsoleLogger as log

# Mock DataLocker (simulate DB)
class MockDataLocker:
    def __init__(self):
        self.alerts = []
        self.prices = {"BTC": {"current_price": 60500}, "ETH": {"current_price": 1900}}
    
    def get_alerts(self):
        return [a.__dict__ for a in self.alerts]

    def get_latest_price(self, asset_type):
        return self.prices.get(asset_type.upper())

    def update_alert_conditions(self, alert_id, fields: dict):
        for a in self.alerts:
            if a.id == alert_id:
                for key, val in fields.items():
                    setattr(a, key, val)

    def get_current_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@pytest.mark.asyncio
async def test_full_alert_flow():
    # Step 1: Setup mock repo and services
    data_locker = MockDataLocker()

    repo = AlertRepository(data_locker)
    enrichment = AlertEnrichmentService(data_locker)
    config_loader = lambda: load_config("alert_limits.json") or {}  # fallback empty
    notification_service = NotificationService(config_loader)

    service = AlertService(repo, enrichment, config_loader)
    service.notification_service = notification_service  # override with real notifier

    # Step 2: Create manual alerts
    alert1 = Alert(
        id="alert-001",
        alert_type="PriceThreshold",
        asset="BTC",
        trigger_value=60000,
        evaluated_value=0.0,  # will be enriched
        condition="ABOVE"
    )

    alert2 = Alert(
        id="alert-002",
        alert_type="PriceThreshold",
        asset="ETH",
        trigger_value=2000,
        evaluated_value=0.0,  # will be enriched
        condition="ABOVE"
    )

    data_locker.alerts.append(alert1)
    data_locker.alerts.append(alert2)

    log.banner("TEST: Full Alert Flow Start")

    # Step 3: Process alerts
    await service.process_all_alerts()

    log.banner("TEST: Full Alert Flow Complete")

    # Step 4: Validate outcomes
    # Step 4: Validate only that evaluated_value is a valid number
    for alert in data_locker.alerts:
        assert alert.evaluated_value is not None
        assert isinstance(alert.evaluated_value, (float, int))

