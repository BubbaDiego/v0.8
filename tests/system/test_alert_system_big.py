import pytest
import asyncio
from data.alert import Alert, AlertType, AlertLevel, Condition
from alerts.alert_service import AlertService
from alerts.alert_repository import AlertRepository
from alerts.alert_enrichment_service import AlertEnrichmentService
from utils.config_loader import load_config

# --- Mock Data Locker (Universal) ---
class MockDataLockerSystem:
    def __init__(self):
        self.alerts = []
        self.positions = {
            "pos1": {
                "entry_price": 10000,
                "liquidation_price": 7000,
                "position_type": "LONG",
                "current_heat_index": 65.0,
                "pnl_after_fees_usd": 1500.0,
                "asset_type": "BTC"
            }
        }
        self.prices = {
            "BTC": {"current_price": 9500}
        }

    def get_alerts(self):
        return [vars(a) for a in self.alerts]

    def get_latest_price(self, asset_type):
        return self.prices.get(asset_type, {"current_price": 10000})

    def read_positions(self):
        return list(self.positions.values())

    def get_position_by_reference_id(self, ref_id):
        return self.positions.get(ref_id)

    def update_alert_conditions(self, alert_id, fields: dict):
        for a in self.alerts:
            if a.id == alert_id:
                if 'level' in fields:
                    maybe_level = fields['level']
                    if hasattr(maybe_level, 'level'):
                        a.level = maybe_level.level
                    else:
                        a.level = maybe_level
                if 'last_triggered' in fields:
                    a.last_triggered = fields['last_triggered']

    def get_current_timestamp(self):
from datetime import datetime
from core.core_imports import log
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# --- SYSTEM TEST ---

@pytest.mark.asyncio
async def test_total_alert_system_flow():
    log.banner("SYSTEM TEST: Sonic Alert System Full Lifecycle Start")

    # Step 1: Setup
    config = load_config("alert_limitsz.json") or {}
    data_locker = MockDataLockerSystem()
    repo = AlertRepository(data_locker)
    enrichment = AlertEnrichmentService(data_locker)
    service = AlertService(repo, enrichment, lambda: config)

    # Step 2: Create Alerts
    alerts_to_create = [
        Alert(id="price-threshold-001", alert_type=AlertType.PriceThreshold, asset="BTC", trigger_value=9000, condition=Condition.ABOVE),
        Alert(id="profit-alert-001", alert_type=AlertType.Profit, asset="BTC", trigger_value=1000, condition=Condition.ABOVE, position_reference_id="pos1"),
        Alert(id="heat-index-alert-001", alert_type=AlertType.HeatIndex, asset="BTC", trigger_value=50, condition=Condition.ABOVE, position_reference_id="pos1"),
        Alert(id="travel-percent-001", alert_type=AlertType.TravelPercentLiquid, asset="BTC", trigger_value=50, condition=Condition.ABOVE, position_reference_id="pos1")
    ]

    data_locker.alerts.extend(alerts_to_create)
    log.success(f"✅ Created {len(alerts_to_create)} sample alerts", source="TestSystem")

    # Step 3: First Full Processing Cycle
    await service.process_all_alerts()

    # Step 4: Assertions after first cycle
    for alert in data_locker.alerts:
        print("\n=======================")
        log.info(f"🔎 Verifying Alert: {alert.id}", source="TestSystem")
        assert alert.evaluated_value is not None, f"Evaluated value missing for {alert.id}"
        assert alert.level in [AlertLevel.HIGH, AlertLevel.MEDIUM, AlertLevel.LOW, AlertLevel.NORMAL], f"Unexpected level for {alert.id}: {alert.level}"
        print(f"Alert ID: {alert.id} - Evaluated Value: {alert.evaluated_value} - Level: {alert.level}")

    log.success("✅ All alerts successfully enriched, evaluated, and updated.", source="TestSystem")

    # Step 5: Modify environment slightly (simulate market changes)
    data_locker.prices["BTC"]["current_price"] = 11000  # Simulate BTC price spike
    data_locker.positions["pos1"]["current_heat_index"] = 85.0  # Heat index higher
    data_locker.positions["pos1"]["pnl_after_fees_usd"] = 3000.0  # Higher profit

    log.info("🌟 Environment modified for second cycle (market simulation)", source="TestSystem")

    # Step 6: Second Full Processing Cycle
    await service.process_all_alerts()

    # Step 7: Assertions after second cycle
    for alert in data_locker.alerts:
        print("\n=======================")
        log.info(f"🔎 Re-verifying Alert: {alert.id}", source="TestSystem")
        assert alert.evaluated_value is not None, f"Evaluated value missing after cycle 2 for {alert.id}"
        assert alert.level in [AlertLevel.HIGH, AlertLevel.MEDIUM, AlertLevel.LOW, AlertLevel.NORMAL], f"Unexpected level after cycle 2 for {alert.id}: {alert.level}"
        print(f"[Cycle 2] Alert ID: {alert.id} - Evaluated Value: {alert.evaluated_value} - Level: {alert.level}")

    log.banner("SYSTEM TEST: Sonic Alert System Full Lifecycle Complete")
    log.success("🎉 Full System Test Passed!", source="TestSystem")
