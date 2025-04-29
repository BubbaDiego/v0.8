import pytest
import asyncio
from data.alert import Alert, AlertType, Condition
from alerts.alert_enrichment_service import AlertEnrichmentService
from utils.console_logger import ConsoleLogger as log

# --- Mock DataLocker for testing determine_value methods ---

class MockDataLockerDetermineValue:
    def __init__(self):
        self.positions = {
            "pos123": {
                "entry_price": 100,
                "liquidation_price": 50,
                "pnl_after_fees_usd": 2500,
                "current_heat_index": 70,
                "position_type": "LONG",
                "asset_type": "BTC"
            }
        }
        self.prices = {
            "BTC": {"current_price": 125}
        }

    def get_position_by_reference_id(self, ref_id):
        return self.positions.get(ref_id)

    def get_latest_price(self, asset_type):
        return self.prices.get(asset_type.upper())

@pytest.mark.asyncio
async def test_determine_value_travel_percent():
    data_locker = MockDataLockerDetermineValue()
    enrichment = AlertEnrichmentService(data_locker)

    alert = Alert(
        id="tp1",
        alert_type=AlertType.TravelPercentLiquid,
        asset="BTC",
        trigger_value=0,
        condition=Condition.ABOVE,
        evaluated_value=0.0,
        position_reference_id="pos123"
    )

    tp = await enrichment._determine_value_travel_percent(alert)
    log.success(f"✅ Travel Percent calculated: {tp}", source="TestDetermineValue")
    assert tp == 50  # Should be 50% movement toward profit

@pytest.mark.asyncio
async def test_determine_value_price_threshold():
    data_locker = MockDataLockerDetermineValue()
    enrichment = AlertEnrichmentService(data_locker)

    alert = Alert(
        id="pt1",
        alert_type=AlertType.PriceThreshold,
        asset="BTC",
        trigger_value=0,
        condition=Condition.ABOVE,
        evaluated_value=0.0,
        position_reference_id=None
    )

    price = await enrichment._determine_value_price_threshold(alert)
    log.success(f"✅ Price fetched: {price}", source="TestDetermineValue")
    assert price == 125

@pytest.mark.asyncio
async def test_determine_value_profit():
    data_locker = MockDataLockerDetermineValue()
    enrichment = AlertEnrichmentService(data_locker)

    alert = Alert(
        id="profit1",
        alert_type=AlertType.Profit,
        asset="BTC",
        trigger_value=0,
        condition=Condition.ABOVE,
        evaluated_value=0.0,
        position_reference_id="pos123"
    )

    profit = await enrichment._determine_value_profit(alert)
    log.success(f"✅ Profit fetched: {profit}", source="TestDetermineValue")
    assert profit == 2500

@pytest.mark.asyncio
async def test_determine_value_heat_index():
    data_locker = MockDataLockerDetermineValue()
    enrichment = AlertEnrichmentService(data_locker)

    alert = Alert(
        id="heat1",
        alert_type=AlertType.HeatIndex,
        asset="BTC",
        trigger_value=0,
        condition=Condition.ABOVE,
        evaluated_value=0.0,
        position_reference_id="pos123"
    )

    heat_index = await enrichment._determine_value_heat_index(alert)
    log.success(f"✅ Heat Index fetched: {heat_index}", source="TestDetermineValue")
    assert heat_index == 70
