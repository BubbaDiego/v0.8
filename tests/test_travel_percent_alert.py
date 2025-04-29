import pytest
import asyncio
from alerts.alert_service import AlertService
from alerts.alert_repository import AlertRepository
from alerts.alert_enrichment_service import AlertEnrichmentService
from xcom.notification_service import NotificationService
from data.alert import Alert, AlertType, AlertLevel
from utils.config_loader import load_config
from utils.console_logger import ConsoleLogger as log

# --- Mock Services ---

class MockEnrichmentService:
    def __init__(self, data_locker):
        self.data_locker = data_locker

    async def enrich(self, alert: Alert):
        if alert.alert_type == AlertType.TRAVEL_PERCENT_LIQUID:
            pos = self.data_locker.read_positions()[0]
            alert.evaluated_value = pos.get("travel_percent", 0.0)
        else:
            price = self.data_locker.get_latest_price(alert.asset)
            alert.evaluated_value = price.get("current_price", 0.0) if price else 0.0
        return alert

class MockDataLockerTravelPercent:
    def __init__(self):
        self.alerts = []
        self.positions = {
            "pos1": {
                "travel_percent": -80.0,  # Controlled negative travel percent (expected HIGH)
                "pnl_after_fees_usd": 0.0,
                "current_heat_index": 0.0
            }
        }

    def get_alerts(self):
        return [vars(a) for a in self.alerts]

    def get_latest_price(self, asset_type):
        return {"current_price": 50000}  # Dummy price, not important for TravelPercent

    def read_positions(self):
        return list(self.positions.values())

    def update_alert_conditions(self, alert_id, fields: dict):
        for a in self.alerts:
            if a.id == alert_id:
                for key, val in fields.items():
                    setattr(a, key, val)

    def get_current_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- Test Case ---

@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_travel_percent_alert_behavior():
    # Step 1: Setup mock services
    data_locker = MockDataLockerTravelPercent()
    repo = AlertRepository(data_locker)
    enrichment = MockEnrichmentService(data_locker)
    config_loader = lambda: load_config("alert_limits.json") or {}

    service = AlertService(repo, enrichment, config_loader)
    service.notification_service = NotificationService(config_loader)

    # Step 2: Create a TravelPercent Alert
    alert = Alert(
        id="travel-alert-001",
        alert_type=AlertType.TRAVEL_PERCENT_LIQUID,
        asset="BTC",
        trigger_value=-25.0,
        evaluated_value=0.0,
        condition="BELOW"
    )
    data_locker.alerts.append(alert)

    log.banner("TEST: Travel Percent Alert Test Start")

    # Step 3: Process the alert
    await service.process_all_alerts()

    log.banner("TEST: Travel Percent Alert Test End")

    # ✅ Step 4: Check updated alert (inside function scope)
    updated_alert = data_locker.alerts[0]

    # ✅ Instead of asserting evaluated_value directly,
    # assert the Level (which proves evaluation worked)
    assert updated_alert.level == AlertLevel.HIGH

    log.success(f"✅ TravelPercent Test Passed: Level={updated_alert.level}", source="TestTravelPercent")
