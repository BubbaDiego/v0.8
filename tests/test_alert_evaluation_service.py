import pytest

from data.alert import Alert, AlertType, AlertLevel, Condition
from alert_core.alert_evaluation_service import AlertEvaluationService
from data.models import AlertThreshold


class DummyThresholdService:
    """Simple stand-in that returns static thresholds per type."""

    def __init__(self, values: dict[str, dict[str, float]]):
        self.values = values

    def get_thresholds(self, alert_type: str, alert_class: str, condition: str):
        vals = self.values.get(alert_type)
        if not vals:
            return None
        return AlertThreshold(
            id="t1",
            alert_type=alert_type,
            alert_class=alert_class,
            metric_key="m",
            condition=condition,
            low=vals["LOW"],
            medium=vals["MEDIUM"],
            high=vals["HIGH"],
        )


@pytest.fixture
def evaluation_service():
    thresholds = {
        "PriceThreshold": {"LOW": 5000, "MEDIUM": 10000, "HIGH": 15000},
        "TravelPercentLiquid": {"LOW": -10, "MEDIUM": -25, "HIGH": -50},
    }
    return AlertEvaluationService(DummyThresholdService(thresholds))


@pytest.mark.parametrize(
    "value,expected",
    [
        (5000, AlertLevel.LOW),
        (10000, AlertLevel.MEDIUM),
        (15000, AlertLevel.HIGH),
    ],
)
def test_above_boundaries(evaluation_service, value, expected):
    alert = Alert(
        id=f"above-{value}",
        alert_type=AlertType.PriceThreshold,
        asset="BTC",
        trigger_value=0,
        condition=Condition.ABOVE,
        evaluated_value=value,
    )
    result = evaluation_service.evaluate(alert)
    assert result.level == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (-10, AlertLevel.LOW),
        (-25, AlertLevel.MEDIUM),
        (-50, AlertLevel.HIGH),
    ],
)
def test_below_boundaries(evaluation_service, value, expected):
    alert = Alert(
        id=f"below-{abs(value)}",
        alert_type=AlertType.TravelPercentLiquid,
        asset="BTC",
        trigger_value=0,
        condition=Condition.BELOW,
        evaluated_value=value,
    )
    result = evaluation_service.evaluate(alert)
    assert result.level == expected


@pytest.mark.parametrize(
    "alter_type,evaluated,expected_eval,expected_level",
    [
        ("UnknownType", 150, 150, AlertLevel.HIGH),
        (AlertType.PriceThreshold, None, 0.0, AlertLevel.NORMAL),
    ],
)
def test_fallback_and_default(evaluation_service, alter_type, evaluated, expected_eval, expected_level):
    alert = Alert(
        id="case",
        alert_type=AlertType.PriceThreshold,
        asset="BTC",
        trigger_value=100,
        condition=Condition.ABOVE,
        evaluated_value=evaluated,
    )
    # mutate type after validation to trigger fuzzy matching failure when needed
    alert.alert_type = alter_type

    result = evaluation_service.evaluate(alert)
    assert result.evaluated_value == expected_eval
    assert result.level == expected_level

