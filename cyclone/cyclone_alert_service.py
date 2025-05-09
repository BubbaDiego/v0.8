import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from uuid import uuid4
from data.alert import AlertType, Condition
from alerts.alert_utils import log_alert_summary
from datetime import datetime
from alerts.alert_enrichment_service import AlertEnrichmentService
from alerts.alert_evaluation_service import AlertEvaluationService
#from positions.positions_core_service import PositionsCoreService
from positions.position_core_service import PositionCoreService
from cyclone.cyclone_portfolio_service import CyclonePortfolioService
from uuid import uuid4
from data.alert import AlertType, Condition
from alerts.alert_utils import log_alert_summary
from datetime import datetime


from alerts.alert_utils import normalize_alert_fields
from core.logging import log as logger


class CycloneAlertService:
    def __init__(self, data_locker):
        self.data_locker = data_locker
        self.enrichment_service = AlertEnrichmentService(data_locker)
        self.evaluation_service = AlertEvaluationService()

    async def create_position_alerts(self):
        """Generate alerts per open position"""
       # from positions.position_service import PositionService
        logger.info("🔔 Creating position alerts", source="CycloneAlertService")
        try:
            positions = self.data_locker.positions.get_all_positions()
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            created = 0

            for pos in positions:
                base = {
                    "asset": pos["asset_type"],
                    "asset_type": pos["asset_type"],
                    "position_reference_id": pos["id"],
                    "position_type": pos.get("position_type", "long"),
                    "notification_type": "SMS",
                    "level": "Normal",
                    "last_triggered": None,
                    "status": "Active",
                    "frequency": 1,
                    "counter": 0,
                    "notes": "Auto-created by Cyclone",
                    "description": f"Alert for {pos['asset_type']}",
                    "liquidation_distance": 0.0,
                    "travel_percent": 0.0,
                    "liquidation_price": 0.0,
                    "evaluated_value": 0.0,
                    "created_at": now
                }

                alerts = [
                    {
                        **base,
                        "id": str(uuid4()),
                        "alert_type": AlertType.HeatIndex.value,
                        "alert_class": "Position",
                        "trigger_value": 50,
                        "condition": Condition.ABOVE.value
                    },
                    {
                        **base,
                        "id": str(uuid4()),
                        "alert_type": AlertType.Profit.value,
                        "alert_class": "Position",
                        "trigger_value": 1000,
                        "condition": Condition.ABOVE.value
                    }
                ]

                for alert in alerts:
                    self.data_locker.alerts.create_alert(alert)
                    log_alert_summary(alert)
                    created += 1

            logger.success(f"✅ Created {created} position alerts", source="CycloneAlertService")
        except Exception as e:
            logger.error(f"❌ Failed to create position alerts: {e}", source="CycloneAlertService")

    async def create_portfolio_alerts(self):
        """Generate portfolio-level alerts"""

        logger.info("📦 Creating portfolio alerts", source="CycloneAlertService")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        metrics = [
            (AlertType.TotalValue, "total_value", 50000),
            (AlertType.TotalSize, "total_size", 1.0),
            (AlertType.AvgLeverage, "avg_leverage", 2.0),
            (AlertType.AvgTravelPercent, "avg_travel_percent", 10.0),
            (AlertType.ValueToCollateralRatio, "value_to_collateral_ratio", 1.2),
            (AlertType.TotalHeat, "total_heat", 25.0),
        ]

        created = 0

        for alert_type, metric_desc, trigger_value in metrics:
            alert = None  # defensive
            try:
                logger.debug(f"⏳ Building alert: {metric_desc} @ {now}", source="CycloneAlertService")

                alert = {
                    "id": str(uuid4()),
                    "created_at": now,
                    "alert_type": alert_type.value,
                    "alert_class": "Portfolio",
                    "asset": "PORTFOLIO",
                    "asset_type": "ALL",
                    "trigger_value": trigger_value,
                    "condition": Condition.ABOVE.value,
                    "notification_type": "SMS",
                    "level": "Normal",
                    "last_triggered": None,
                    "status": "Active",
                    "frequency": 1,
                    "counter": 0,
                    "liquidation_distance": 0.0,
                    "travel_percent": 0.0,
                    "liquidation_price": 0.0,
                    "notes": "Auto-generated portfolio alert",
                    "description": metric_desc,
                    "position_reference_id": None,
                    "evaluated_value": 0.0,
                    "position_type": "N/A"
                }

                self.data_locker.alerts.create_alert(alert)
                log_alert_summary(alert)
                created += 1

            except Exception as e:
                logger.error(f"💥 Failed to create alert for {metric_desc}: {e}", source="CycloneAlertService")
                if alert:
                    logger.debug(f"🧾 Alert payload (partial): {alert}", source="CycloneAlertService")

        logger.success(f"✅ Created {created} portfolio alerts", source="CycloneAlertService")

    async def create_global_alerts(self):
        """Example global alert"""
        logger.info("Creating global alert (price threshold for BTC)", source="CycloneAlertService")
        try:
            alert = {
                "id": str(uuid4()),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "alert_type": AlertType.PriceThreshold.value,
                "alert_class": "Market",
                "asset": "BTC",
                "asset_type": "Crypto",
                "trigger_value": 65000,
                "condition": Condition.ABOVE.value,
                "notification_type": "SMS",
                "level": "Normal",
                "last_triggered": None,
                "status": "Active",
                "frequency": 1,
                "counter": 0,
                "liquidation_distance": 0.0,
                "travel_percent": 0.0,
                "liquidation_price": 0.0,
                "notes": "BTC price alert",
                "description": "BTC threshold",
                "position_reference_id": None,
                "evaluated_value": 0.0,
                "position_type": "N/A"
            }

            self.data_locker.alerts.create_alert(alert)
            log.success("✅ Global alert created.", source="CycloneAlertService")
        except Exception as e:
            logger.error(f"💥 Failed to create global alert: {e}", source="CycloneAlertService")

    async def enrich_all_alerts(self):
        alerts = self.data_locker.alerts.get_all_alerts()
        if not alerts:
            log.warning("⚠️ No alerts found to enrich", source="CycloneAlertService")
            return []

        alerts = [normalize_alert_fields(a) for a in alerts]
        logger.info(f"🔬 Enriching {len(alerts)} alerts", source="CycloneAlertService")

        enriched = await self.enrichment_service.enrich_all(alerts)
        log.success(f"✅ Enriched {len(enriched)} alerts", source="CycloneAlertService")
        return enriched

    async def run_alert_evaluation(self):
        """Evaluate all alerts and log results in detail"""
        logger.banner("🔍 Running ALERT EVALUATION ONLY")

        alerts = self.data_locker.alerts.get_all_alerts()
        if not alerts:
            logger.warning("⚠️ No alerts found to evaluate", source="CycloneAlertService")
            return

        total = len(alerts)
        evaluated = 0
        skipped = 0
        failed = 0

        logger.start_timer("alert_evaluation")

        for alert in alerts:
            try:
                if alert.get("evaluated_value") is None:
                    skipped += 1
                    log.warning(f"⚠️ Alert {alert['id'][:6]} missing evaluated_value, skipping",
                                source="CycloneAlertService")
                    continue

                normalized = normalize_alert_fields(alert)
                result = self.evaluation_service.evaluate(normalized)

                self.data_locker.alerts.update_alert(result)
                logger.success(
                    f"✅ [{alert['id'][:6]}] → {alert['alert_type']} = {result.evaluated_value} → Level: {result.level}",
                    source="CycloneAlertService")
                evaluated += 1
            except Exception as e:
                failed += 1
                logger.error(f"❌ Error evaluating alert {alert.get('id', '?')} — {e}", source="CycloneAlertService")

        logger.end_timer("alert_evaluation", source="CycloneAlertService")
        logger.info(f"📊 Evaluation Summary → Total: {total}, Evaluated: {evaluated}, Skipped: {skipped}, Failed: {failed}",
                 source="CycloneAlertService")

    async def update_evaluated_values(self):
        alerts = self.data_locker.alerts.get_all_alerts()
        if not alerts:
            log.warning("⚠️ No alerts found to evaluate", source="CycloneAlertService")
            return

        updated = 0
        for alert in alerts:
            try:
                normalized = normalize_alert_fields(alert)
                evaluated = self.evaluation_service.evaluate(normalized)
                self.data_locker.alerts.update_alert(evaluated)
                updated += 1
            except Exception as e:
                logger.error(f"💣 Failed to evaluate alert {alert.get('id', '?')}: {e}", source="CycloneAlertService")

        logger.success(f"✅ Evaluated and updated {updated} alerts", source="CycloneAlertService")

    def clear_stale_alerts(self):
        try:
            self.data_locker.alerts.clear_inactive_alerts()
            logger.success("🧹 Inactive alerts cleared", source="CycloneAlertService")
        except Exception as e:
            logger.error(f"💥 Failed to clear inactive alerts: {e}", source="CycloneAlertService")

    async def run_alert_updates(self):
        logger.info("🔄 Running enrichment + evaluation cycle", source="CycloneAlertService")
        await self.enrich_all_alerts()
        await self.update_evaluated_values()
        logger.success("✅ Alert pipeline completed", source="CycloneAlertService")
