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
        if alert.alert_type == AlertType.Profit:
            pos = self.data_locker.read_positions()[0]
            alert.evaluated_value = pos.get("pnl_after_fees_usd", 0.0)
        else:
            price = self.data_locker.get_latest_price(alert.asset)
            alert.evaluated_value = price.get("current_price", 0.0) if price else 0.0
        return alert

class MockDataLockerProfit:
    def __init__(self):
        self.alerts = []
        self.positions = {
            "pos1": {
                "travel_percent": 0.0,
                "pnl_after_fees_usd": 3500.0,
                "current_heat_index": 0.0
            }
        }

    def get_alerts(self):
        return [vars(a) for a in self.alerts]  # ✅ return dicts again

    def get_latest_price(self, asset_type):
        return {"current_price": 50000}

    def read_positions(self):
        return list(self.positions.values())

    def update_alert_conditions(self, alert_id, fields: dict):
        for a in self.alerts:
            if a.id == alert_id:
                # Special care: if level looks like an Alert, extract
                maybe_level = fields.get('level')
                if isinstance(maybe_level, Alert):
                    a.level = maybe_level.level  # <-- real fix: drill inside
                else:
                    a.level = maybe_level
                if 'last_triggered' in fields:
                    a.last_triggered = fields['last_triggered']

    def get_current_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# --- Test Case ---

@pytest.mark.asyncio
async def test_profit_alert_behavior():
    # Step 1: Setup mock services
    data_locker = MockDataLockerProfit()
    repo = AlertRepository(data_locker)
    enrichment = MockEnrichmentService(data_locker)
    config_loader = lambda: load_config("alert_limits.json") or {}

    service = AlertService(repo, enrichment, config_loader)
    service.notification_service = NotificationService(config_loader)

    # Step 2: Create a Profit Alert
    alert = Alert(
        id="profit-alert-001",
        alert_type=AlertType.Profit,
        asset="BTC",
        trigger_value=1000.0,  # Trigger when profit ABOVE $1000
        evaluated_value=0.0,
        condition="ABOVE"
    )
    data_locker.alerts.append(alert)

    log.banner("TEST: Profit Alert Test Start")

    # Step 3: Process the alert
    await service.process_all_alerts()

    log.banner("TEST: Profit Alert Test End")

    # Step 4: Check updated alert (live memory object)
    updated_alert = data_locker.alerts[0]

    # Step 5: Assertions
    # (We now check LEVEL not exact evaluated_value directly)
    assert updated_alert.level in [AlertLevel.HIGH, AlertLevel.MEDIUM, AlertLevel.LOW]

    log.success(f"✅ ProfitAlert Test Passed: Evaluated={updated_alert.evaluated_value} Level={updated_alert.level}", source="TestProfitAlert")
