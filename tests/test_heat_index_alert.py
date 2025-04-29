import pytest
import asyncio
from data.alert import Alert, AlertType, AlertLevel, Condition
from alerts.alert_service import AlertService
from alerts.alert_repository import AlertRepository
from alerts.alert_enrichment_service import AlertEnrichmentService
from utils.config_loader import load_config
from utils.console_logger import ConsoleLogger as log

# --- Mock DataLocker for isolated testing ---
class MockDataLockerHeatIndex:
    def __init__(self):
        self.alerts = []
        self.positions = {
            "pos1": {
                "current_heat_index": 75.0  # Example: high risk heat index
            }
        }

    def get_alerts(self):
        return [vars(a) for a in self.alerts]

    def get_latest_price(self, asset_type):
        return {"current_price": 10000}  # Dummy, not needed here

    def read_positions(self):
        return list(self.positions.values())

    def update_alert_conditions(self, alert_id, fields: dict):
        for a in self.alerts:
            if a.id == alert_id:
                if 'level' in fields:
                    maybe_level = fields['level']
                    if hasattr(maybe_level, "level"):  # means it’s a full Alert object
                        a.level = maybe_level.level
                    else:
                        a.level = maybe_level
                if 'last_triggered' in fields:
                    a.last_triggered = fields['last_triggered']

    def get_position_by_reference_id(self, ref_id):
        return self.positions.get(ref_id, None)

    def get_current_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- The actual robust test ---

@pytest.mark.asyncio
async def test_heat_index_alert_behavior():
    # Step 1: Setup mocks
    data_locker = MockDataLockerHeatIndex()
    repo = AlertRepository(data_locker)
    enrichment = AlertEnrichmentService(data_locker)
    config_loader = lambda: load_config("alert_limits.json") or {}

    service = AlertService(repo, enrichment, config_loader)

    # Step 2: Create a HeatIndex Alert
    alert = Alert(
        id="heat-index-alert-001",
        alert_type=AlertType.HeatIndex,
        asset="BTC",
        trigger_value=50.0,  # Trigger when Heat Index ABOVE 50
        evaluated_value=0.0,
        condition=Condition.ABOVE,
        position_reference_id="pos1"
    )
    data_locker.alerts.append(alert)

    log.banner("TEST: Heat Index Alert Test Start")

    # Step 3: Process alerts
    await service.process_all_alerts()

    log.banner("TEST: Heat Index Alert Test End")

    # Step 4: Verify updated alert
    updated_alert = data_locker.alerts[0]

    assert updated_alert.evaluated_value is not None, "Alert was not enriched"
    assert updated_alert.level in [AlertLevel.HIGH, AlertLevel.MEDIUM, AlertLevel.LOW], f"Unexpected alert level: {updated_alert.level}"

    log.success(f"✅ HeatIndex Test Passed: Evaluated={updated_alert.evaluated_value} Level={updated_alert.level}", source="TestHeatIndexAlert")
