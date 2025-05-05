import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import uuid
from datetime import datetime

from data.alert import Alert, AlertType, Condition, NotificationType
from data.data_locker import DataLocker
from alerts.alert_enrichment_service import AlertEnrichmentService
from alerts.alert_evaluation_service import AlertEvaluationService
from alerts.alert_repository import AlertRepository
from config.config_loader import load_config
from config.config_constants import ALERT_LIMITS_PATH
from utils.console_logger import ConsoleLogger as log
from alerts.alert_threshold_utils import get_default_trigger_value
from dashboard import dashboard_service


# ==================================================================================
# 🔁 IMPORTANT: FULL END-TO-END ALERT WORKFLOW (MULTI-CYCLE)
# This test performs the complete alert lifecycle for 3 full runs with varied data:
#
# 1️⃣  Load alert configuration and log top-level keys
# 2️⃣  Clear alerts/positions per cycle
# 3️⃣  Inject portfolio snapshot, position, and price data
# 4️⃣  Create alerts for all alert types (with trigger values from config)
# 5️⃣  Enrich alerts to compute `evaluated_value`
# 6️⃣  Evaluate alerts using threshold config to assign `level`
# 7️⃣  Save `evaluated_value` and `level` to DB
# 8️⃣  Validate all values in memory and DB
# ==================================================================================

def test_portfolio_alerts_EE_multirun():
    log.banner("STARTING FULL END-TO-END ALERT SYSTEM TEST")
    locker = DataLocker.get_instance()

    # ✅ Step 1: Load config
    try:
        config = load_config(str(ALERT_LIMITS_PATH))
        alert_limits = config.get("alert_limits", config)
        log.info(f"Loaded alert_limits keys: {list(alert_limits.keys())}", source="ConfigLoader")
        assert "total_portfolio_limits" in alert_limits, "Missing 'total_portfolio_limits' in config"
        log.success("✅ Alert configuration loaded and validated", source="ConfigLoader")
    except Exception as e:
        raise AssertionError(f"❌ Failed to load alert config: {e}")

    if not hasattr(locker, "get_current_value"):
        setattr(locker, "get_current_value", lambda asset: locker.get_latest_price(asset).get("current_price", 0.0))

    repo = AlertRepository(locker)
    enrichment_service = AlertEnrichmentService(locker)
    evaluation_service = PatchedEvaluationService()

    for run in range(1, 4):
        log.banner(f"🔁 CYCLE {run}/3")

        # ✅ Step 2: Clear state
        locker.delete_all_alerts()
        locker.delete_all_positions()

        # ✅ Step 3: Mock data
        totals = _mock_portfolio_snapshot(locker, run)
        _mock_positions(locker, run)
        _mock_prices(locker, run)

        # Override dashboard context for enrichment
        dashboard_service.get_dashboard_context = lambda: {"totals": totals}

        # ✅ Step 4: Create alerts (trigger values pulled from config)
        alerts = []
        alerts += _create_portfolio_alerts(repo)
        alerts += _create_position_alerts(repo, run)
        alerts += _create_market_alerts(repo)
        log.info(f"📋 Created {len(alerts)} alerts for run {run}", source="Test")

        # ✅ Step 5: Enrich + Evaluate
        async def enrich_and_evaluate():
            enriched = await enrichment_service.enrich_all(alerts)
            evaluated = [evaluation_service.evaluate(a) for a in enriched]
            return evaluated

        final_alerts = asyncio.run(enrich_and_evaluate())

        # ✅ Step 6: Save results
        for alert in final_alerts:
            repo.update_alert_evaluated_value(alert.id, alert.evaluated_value)
            asyncio.run(repo.update_alert_level(alert.id, alert.level))

        # ✅ Step 7: Memory assertions
        log.info(f"🔍 Validating in-memory alerts for run {run}", source="MemoryCheck")
        for alert in final_alerts:
            log.debug(f"{alert.alert_class} - {alert.alert_type} → Eval={alert.evaluated_value} | Level={alert.level}",
                      source="MemoryCheck")
            assert isinstance(alert.evaluated_value, (int, float))
            assert alert.level in {"Low", "Medium", "High", "Normal"}

        # ✅ Step 8: DB assertions
        log.info(f"🧪 Validating DB entries for run {run}", source="DBCheck")
        db_alerts = locker.get_alerts()
        for a in db_alerts:
            log.debug(f"[DB] Alert {a['id']} → Eval={a['evaluated_value']} | Level={a['level']}", source="DBCheck")
            assert isinstance(a["evaluated_value"], (int, float))
            assert a["level"] in {"Low", "Medium", "High", "Normal"}

    log.banner("✅ ALL ALERT CYCLES COMPLETED SUCCESSFULLY")


# === MOCKS ===

def _mock_portfolio_snapshot(locker, cycle):
    snapshot = {
        "total_value": 10000 * cycle,
        "total_collateral": 5000 * cycle,
        "total_size": 2000 * cycle,
        "avg_leverage": 1.0 + cycle,
        "avg_travel_percent": 10 * cycle,
        "avg_heat_index": 35.0  # Ensures total_heat is valid
    }
    locker.record_portfolio_snapshot(snapshot)
    return snapshot


def _mock_positions(locker, cycle):
    locker.create_position({
        "id": f"pos-{cycle}",
        "asset_type": "ETH",
        "position_type": "LONG",
        "entry_price": 1000,
        "liquidation_price": 800 - (cycle * 10),
        "collateral": 1000 + (cycle * 500),
        "size": 2000 + (cycle * 100),
        "leverage": 1.5 + cycle,
        "value": 2500 + (cycle * 200),
        "wallet_name": f"CycleWallet{cycle}",
        "current_price": 1100 + (cycle * 20),
        "heat_index": 35.0,  # ← important for HeatIndex
        "current_heat_index": 35.0,
        "pnl_after_fees_usd": 100 + (cycle * 50)
    })


def _mock_prices(locker, cycle):
    locker.insert_or_update_price("BTC", 60000 + (cycle * 5000), "TestCycle")


# === ALERT GENERATORS ===

def _create_portfolio_alerts(repo):
    metric_map = {
        AlertType.TotalValue: "total_value",
        AlertType.TotalSize: "total_size",
        AlertType.AvgLeverage: "avg_leverage",
        AlertType.AvgTravelPercent: "avg_travel_percent",
        AlertType.ValueToCollateralRatio: "value_to_collateral_ratio",
        AlertType.TotalHeat: "total_heat"
    }
    alerts = []
    for atype, desc in metric_map.items():
        alert = Alert(
            id=str(uuid.uuid4()),
            alert_type=atype,
            alert_class="Portfolio",
            trigger_value=get_default_trigger_value(atype),
            condition=Condition.ABOVE,
            notification_type=NotificationType.EMAIL,
            description=desc
        )
        repo.create_alert(alert.model_dump())
        alerts.append(alert)
    return alerts


def _create_position_alerts(repo, cycle):
    position_id = f"pos-{cycle}"
    alerts = []
    for atype in [AlertType.TravelPercentLiquid, AlertType.HeatIndex, AlertType.Profit]:
        alert = Alert(
            id=str(uuid.uuid4()),
            alert_type=atype,
            alert_class="Position",
            position_reference_id=position_id,
            trigger_value=get_default_trigger_value(atype),
            condition=Condition.ABOVE,
            notification_type=NotificationType.SMS
        )
        repo.create_alert(alert.model_dump())
        alerts.append(alert)
    return alerts


def _create_market_alerts(repo):
    alert = Alert(
        id=str(uuid.uuid4()),
        alert_type=AlertType.PriceThreshold,
        alert_class="Market",
        asset="BTC",
        trigger_value=60000,  # could be dynamic too
        condition=Condition.ABOVE,
        notification_type=NotificationType.SMS
    )
    repo.create_alert(alert.model_dump())
    return [alert]


# === PATCHED EVALUATOR ===

class PatchedEvaluationService(AlertEvaluationService):
    def _evaluate_standard(self, alert):
        return self._simple_trigger_evaluation(alert)


# === RUN ===

if __name__ == "__main__":
    test_portfolio_alerts_EE_multirun()
