import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import uuid
import json
import re
import inspect

from data.alert import Alert, AlertType, Condition, NotificationType
from data.data_locker import DataLocker
from alerts.alert_enrichment_service import AlertEnrichmentService
from alerts.alert_evaluation_service import AlertEvaluationService
from alerts.alert_repository import AlertRepository
from utils.json_manager import JsonManager
from config.config_loader import load_config
from config.config_constants import ALERT_LIMITS_PATH


def test_heat_index_limits_validation():
    print("\n🔥 TEST: Heat Index (total_heat_limits) Configuration + Evaluation\n")

    # === Load Config ===
    config = load_config(str(ALERT_LIMITS_PATH))
    alert_limits = config.get("alert_limits", config)
    tpl = alert_limits.get("total_portfolio_limits", {})
    assert "total_heat_limits" in tpl, "❌ 'total_heat_limits' missing in config"

    thresholds = tpl["total_heat_limits"]
    print(f"✅ Loaded total_heat_limits: {thresholds}")

    # === Set Up System ===
    locker = DataLocker.get_instance()
    repo = AlertRepository(locker)
    enrichment = AlertEnrichmentService(locker)
    evaluation = AlertEvaluationService()

    locker.delete_all_alerts()
    locker.delete_all_positions()

    # === Mock Portfolio Snapshot ===
    locker.record_portfolio_snapshot({
        "total_value": 10000,
        "total_collateral": 5000,
        "total_size": 7000,
        "avg_leverage": 2.0,
        "avg_travel_percent": 15,
        "avg_heat_index": 35.0  # triggers MEDIUM
    })

    # === Create Alert ===
    alert = Alert(
        id=str(uuid.uuid4()),
        alert_type=AlertType.TotalHeat,
        alert_class="Portfolio",
        trigger_value=10,
        condition=Condition.ABOVE,
        notification_type=NotificationType.EMAIL,
        description="total_heat"
    )
    repo.create_alert(alert.model_dump())

    # === Enrich & Evaluate ===
    async def process():
        enriched = await enrichment.enrich(alert)
        evaluated = evaluation.evaluate(enriched)
        return evaluated

    result = asyncio.run(process())

    # === Output ===
    print(f"🧪 Evaluated → evaluated_value={result.evaluated_value}, level={result.level}")
    assert result.evaluated_value == 35.0
    assert result.level == "Medium"

    print("✅ Heat Index Alert correctly enriched and evaluated.\n")


# === SELF-RUN ===
if __name__ == "__main__":
    test_heat_index_limits_validation()
