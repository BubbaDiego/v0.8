import pytest
from types import SimpleNamespace

from data.alert import Alert, AlertType, AlertLevel, Condition
from alert_core.alert_evaluation_service import AlertEvaluationService


class MockThresholdService:
    """Simple stand-in returning objects with threshold levels."""

    def __init__(self, thresholds: dict[str, dict[str, float]]):
        self.thresholds = thresholds

    def get_thresholds(self, alert_type: str, alert_class: str, condition: str):
        vals = self.thresholds.get(alert_type)
        if not vals:
            return None
        return SimpleNamespace(low=vals["LOW"], medium=vals["MEDIUM"], high=vals["HIGH"])


@pytest.fixture
def evaluation_service():
    """Create an evaluation service with mock thresholds for all types."""
    thresholds = {
        "PriceThreshold": {"LOW": 5000, "MEDIUM": 10000, "HIGH": 15000},
        "TravelPercentLiquid": {"LOW": -10, "MEDIUM": -25, "HIGH": -50},
        "Profit": {"LOW": 500, "MEDIUM": 1000, "HIGH": 2000},
        "HeatIndex": {"LOW": 30, "MEDIUM": 60, "HIGH": 90},
    }
    service = AlertEvaluationService(MockThresholdService(thresholds))
    return service


def test_evaluate_price_threshold_above_high(evaluation_service):
    """Test evaluating a PriceThreshold alert ABOVE condition."""
    alert = Alert(
        id="price-above-high",
        alert_type=AlertType.PriceThreshold,
        asset="BTC",
        trigger_value=60000,
        condition=Condition.ABOVE,
        evaluated_value=12000.0,
    )

    evaluated_alert = evaluation_service.evaluate(alert)
    assert evaluated_alert.level == AlertLevel.MEDIUM


def test_evaluate_travel_percent_below_medium(evaluation_service):
    """Test evaluating a TravelPercentLiquid alert BELOW condition."""
    alert = Alert(
        id="travel-below-medium",
        alert_type=AlertType.TravelPercentLiquid,
        asset="BTC",
        trigger_value=-50,
        condition=Condition.BELOW,
        evaluated_value=-30.0,
    )

    evaluated_alert = evaluation_service.evaluate(alert)
    assert evaluated_alert.level in [AlertLevel.MEDIUM, AlertLevel.HIGH]


def test_evaluate_profit_no_thresholds(evaluation_service):
    """Test evaluating a Profit alert without specific thresholds."""
    alert = Alert(
        id="profit-no-thresholds",
        alert_type=AlertType.Profit,
        asset="BTC",
        trigger_value=500,
        condition=Condition.ABOVE,
        evaluated_value=600,
    )

    evaluated_alert = evaluation_service.evaluate(alert)
    assert evaluated_alert.level in [AlertLevel.LOW, AlertLevel.MEDIUM]


def test_evaluate_heat_index_below_low(evaluation_service):
    """Test evaluating a HeatIndex alert BELOW condition."""
    alert = Alert(
        id="heatindex-low",
        alert_type=AlertType.HeatIndex,
        asset="BTC",
        trigger_value=50,
        condition=Condition.BELOW,
        evaluated_value=20,
    )

    evaluated_alert = evaluation_service.evaluate(alert)
    assert evaluated_alert.level == AlertLevel.HIGH


@pytest.mark.parametrize(
    "value,expected",
    [
        (5000, AlertLevel.LOW),
        (10000, AlertLevel.MEDIUM),
        (15000, AlertLevel.HIGH),
    ],
)
def test_above_boundaries(evaluation_service, value, expected):
    """ABOVE condition should map to correct levels at boundaries."""
    alert = Alert(
        id=f"above-{value}",
        alert_type=AlertType.PriceThreshold,
        asset="BTC",
        trigger_value=0,
        condition=Condition.ABOVE,
        evaluated_value=value,
    )

    evaluated = evaluation_service.evaluate(alert)
    assert evaluated.level == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (-10, AlertLevel.LOW),
        (-25, AlertLevel.MEDIUM),
        (-50, AlertLevel.HIGH),
    ],
)
def test_below_boundaries(evaluation_service, value, expected):
    """BELOW condition should map to correct levels at boundaries."""
    alert = Alert(
        id=f"below-{abs(value)}",
        alert_type=AlertType.TravelPercentLiquid,
        asset="BTC",
        trigger_value=0,
        condition=Condition.BELOW,
        evaluated_value=value,
    )

    evaluated = evaluation_service.evaluate(alert)
    assert evaluated.level == expected


def test_evaluated_value_defaults_to_zero(evaluation_service):
    """None evaluated_value should default to 0.0 and produce NORMAL level."""
    alert = Alert(
        id="none-eval",
        alert_type=AlertType.PriceThreshold,
        asset="BTC",
        trigger_value=100,
        condition=Condition.ABOVE,
        evaluated_value=None,
    )

    evaluated = evaluation_service.evaluate(alert)
    assert evaluated.evaluated_value == 0.0
    assert evaluated.level == AlertLevel.NORMAL


def test_invalid_alert_type_triggers_fallback(evaluation_service):
    """Invalid alert_type should bypass thresholds and use fallback eval."""
    alert = Alert(
        id="bad-type",
        alert_type=AlertType.PriceThreshold,
        asset="BTC",
        trigger_value=100,
        condition=Condition.ABOVE,
        evaluated_value=150,
    )
    alert.alert_type = "UnknownType"

    evaluated = evaluation_service.evaluate(alert)
    assert evaluated.level == AlertLevel.HIGH
