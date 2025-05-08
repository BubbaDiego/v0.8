import pytest
import asyncio
import random
from data.alert import Alert, AlertType, Condition
from alerts.alert_enrichment_service import AlertEnrichmentService
from alerts.alert_evaluation_service import AlertEvaluationService
from core.core_imports import log

# --- Mock DataLocker for Batch Enrichment ---

class MockDataLockerFullPipeline:
    def __init__(self):
        self.positions = {}
        self.prices = {"BTC": {"current_price": 125}}

        for i in range(1, 201):
            pos_id = f"pos{i:03d}"
            self.positions[pos_id] = {
                "entry_price": 100,
                "liquidation_price": 50,
                "pnl_after_fees_usd": random.uniform(100, 5000),
                "current_heat_index": random.uniform(10, 100),
                "position_type": random.choice(["LONG", "SHORT"]),
                "asset_type": "BTC"
            }

    def get_position_by_reference_id(self, ref_id):
        return self.positions.get(ref_id)

    def get_latest_price(self, asset_type):
        return self.prices.get(asset_type.upper())

@pytest.mark.system
@pytest.mark.asyncio
async def test_batch_enrich_evaluate_pipeline():
    """
    Full system test: Enrich and evaluate 200 alerts in pipeline.
    """

    data_locker = MockDataLockerFullPipeline()
    enrichment_service = AlertEnrichmentService(data_locker)
    evaluation_service = AlertEvaluationService()

    # Inject mock thresholds manually
    evaluation_service.thresholds = {
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
    }

    # Generate 200 fake alerts
    alerts = []
    types = [AlertType.PriceThreshold, AlertType.TravelPercentLiquid, AlertType.Profit, AlertType.HeatIndex]
    conditions = [Condition.ABOVE, Condition.BELOW]

    for i in range(200):
        alert_type = random.choice(types)
        position_ref = f"pos{i+1:03d}" if alert_type != AlertType.PriceThreshold else None

        alert = Alert(
            id=f"pipeline-alert-{i:03d}",
            alert_type=alert_type,
            asset="BTC",
            trigger_value=random.uniform(100, 10000),
            condition=random.choice(conditions),
            evaluated_value=0.0,
            position_reference_id=position_ref
        )
        alerts.append(alert)

    # --- Enrich Phase ---
    enriched_alerts = []
    for alert in alerts:
        enriched = await enrichment_service.enrich(alert)
        enriched_alerts.append(enriched)

    # --- Evaluation Phase ---
    evaluated_alerts = []
    for alert in enriched_alerts:
        evaluated = evaluation_service.evaluate(alert)
        evaluated_alerts.append(evaluated)

    # --- Validation Phase ---
    for alert in evaluated_alerts:
        log.success(f"✅ {alert.id} evaluated: {alert.evaluated_value:.2f} -> {alert.level}", source="BatchPipelineTest")
        assert alert.level in ["Normal", "Low", "Medium", "High"]
