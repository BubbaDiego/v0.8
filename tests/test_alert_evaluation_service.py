import pytest
from data.alert import Alert, AlertType, AlertLevel, Condition
from alert_core.alert_evaluation_service import AlertEvaluationService
from core.core_imports import log

@pytest.fixture
def evaluation_service():
    """Create an evaluation service with mock thresholds for all types."""
    return AlertEvaluationService(thresholds={
        "PriceThreshold": {
            "LOW": 5000,
            "MEDIUM": 10000,
            "HIGH": 15000
        },
        "TravelPercentLiquid": {
            "LOW": -10,
            "MEDIUM": -25,
            "HIGH": -50
        },
        "Profit": {
            "LOW": 500,
            "MEDIUM": 1000,
            "HIGH": 2000
        },
        "HeatIndex": {
            "LOW": 30,
            "MEDIUM": 60,
            "HIGH": 90
        }
    })

@pytest.mark.asyncio
async def test_evaluate_price_threshold_above_high(evaluation_service):
    """Test evaluating a PriceThreshold alert ABOVE condition."""
    alert = Alert(
        id="price-above-high",
        alert_type=AlertType.PriceThreshold,
        asset="BTC",
        trigger_value=60000,
        condition=Condition.ABOVE,
        evaluated_value=12000.0  # Simulated price
    )

    evaluated_alert = evaluation_service.evaluate(alert)
    log.success(f"✅ Evaluated {evaluated_alert.id} as {evaluated_alert.level}", source="TestEval")
    assert evaluated_alert.level == AlertLevel.MEDIUM

@pytest.mark.asyncio
async def test_evaluate_travel_percent_below_medium(evaluation_service):
    """Test evaluating a TravelPercentLiquid alert BELOW condition."""
    alert = Alert(
        id="travel-below-medium",
        alert_type=AlertType.TravelPercentLiquid,
        asset="BTC",
        trigger_value=-50,
        condition=Condition.BELOW,
        evaluated_value=-30.0
    )

    evaluated_alert = evaluation_service.evaluate(alert)
    log.success(f"✅ Evaluated {evaluated_alert.id} as {evaluated_alert.level}", source="TestEval")
    assert evaluated_alert.level in [AlertLevel.MEDIUM, AlertLevel.HIGH]

@pytest.mark.asyncio
async def test_evaluate_profit_no_thresholds(evaluation_service):
    """Test evaluating a Profit alert without specific thresholds."""
    alert = Alert(
        id="profit-no-thresholds",
        alert_type=AlertType.Profit,
        asset="BTC",
        trigger_value=500,
        condition=Condition.ABOVE,
        evaluated_value=600
    )

    evaluated_alert = evaluation_service.evaluate(alert)
    log.success(f"✅ Evaluated {evaluated_alert.id} as {evaluated_alert.level}", source="TestEval")
    assert evaluated_alert.level == AlertLevel.LOW or evaluated_alert.level == AlertLevel.MEDIUM

@pytest.mark.asyncio
async def test_evaluate_heat_index_below_low(evaluation_service):
    """Test evaluating a HeatIndex alert BELOW condition."""
    alert = Alert(
        id="heatindex-low",
        alert_type=AlertType.HeatIndex,
        asset="BTC",
        trigger_value=50,
        condition=Condition.BELOW,
        evaluated_value=20
    )

    evaluated_alert = evaluation_service.evaluate(alert)
    log.success(
        f"✅ Evaluated {evaluated_alert.id} as {evaluated_alert.level}",
        source="TestEval",
    )
    assert evaluated_alert.level == AlertLevel.HIGH
