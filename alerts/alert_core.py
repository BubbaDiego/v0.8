# alerts/core.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from alerts.alert_enrichment_service import AlertEnrichmentService
from alerts.alert_evaluation_service import AlertEvaluationService
from alerts.alert_store import AlertStore
from xcom.notification_service import NotificationService
from core.core_imports import log

class AlertCore:
    def __init__(self, data_locker, config_loader):
        self.data_locker = data_locker
        self.repo = AlertStore(data_locker)
        self.enricher = AlertEnrichmentService(data_locker)
        self.evaluator = AlertEvaluationService(
            thresholds=config_loader().get("alert_limits", {})
        )
        self.notifier = NotificationService(config_loader)

        self.evaluator.inject_repo(self.repo)  # ⚡️ enable DB updates

    async def create_alert(self, alert_dict: dict) -> bool:
        try:
            success = self.repo.create_alert(alert_dict)
            if success:
                log.success(f"✅ AlertCore created alert", source="AlertCore", payload={"id": alert_dict.get("id")})
            return success
        except Exception as e:
            log.error(f"💥 Failed to create alert", source="AlertCore", payload={"error": str(e)})
            return False

    async def evaluate_alert(self, alert):
        try:
            enriched = await self.enricher.enrich(alert)
            evaluated = self.evaluator.evaluate(enriched)

            self.evaluator.update_alert_level(evaluated.id, evaluated.level)
            self.evaluator.update_alert_evaluated_value(evaluated.id, evaluated.evaluated_value)

            log.success(
                f"🧠 Alert processed",
                source="AlertCore",
                payload={"id": evaluated.id, "level": evaluated.level, "value": evaluated.evaluated_value}
            )

            return evaluated
        except Exception as e:
            log.error(f"❌ Failed to evaluate alert", source="AlertCore", payload={"id": alert.id, "error": str(e)})
            return alert

    async def evaluate_all_alerts(self):
        log.banner("🚨 EVALUATING ALL ALERTS")

        alerts = self.repo.get_active_alerts()
        if not alerts:
            log.warning("⚠️ No active alerts found", source="AlertCore")
            return []

        log.info(f"📥 Loaded {len(alerts)} active alerts", source="AlertCore")

        from asyncio import gather
        enriched = await self.enricher.enrich_all(alerts)
        results = await gather(*(self.evaluate_alert(alert) for alert in enriched))

        log.success(f"✅ Finished processing {len(results)} alerts", source="AlertCore")
        return results

    def clear_stale_alerts(self):
        log.banner("🧹 CLEARING STALE ALERTS")

        alerts = self.repo.get_alerts()
        positions = self.data_locker.positions.get_all_positions()
        valid_pos_ids = {p["id"] for p in positions}
        deleted = 0

        for alert in alerts:
            pos_id = alert.get("position_reference_id")
            if pos_id and pos_id not in valid_pos_ids:
                if self.repo.delete_alert(alert["id"]):
                    deleted += 1
                    log.info(
                        f"🗑 Deleted dangling alert",
                        source="AlertCore",
                        payload={"alert_id": alert["id"], "missing_position": pos_id}
                    )

        log.success(f"✅ Cleared {deleted} stale alerts", source="AlertCore")
        return deleted

    async def enrich_and_evaluate_alerts(self, alerts: list):
        if not alerts:
            log.warning("⚠️ No alerts to process in enrich_and_evaluate_alerts()", source="AlertCore")
            return []

        log.info(f"🧠 Enriching + Evaluating {len(alerts)} alerts", source="AlertCore")

        enriched = await self.enricher.enrich_all(alerts)
        results = []

        for alert in enriched:
            try:
                evaluated = self.evaluator.evaluate(alert)
                self.evaluator.update_alert_level(evaluated.id, evaluated.level)
                self.evaluator.update_alert_evaluated_value(evaluated.id, evaluated.evaluated_value)

                results.append(evaluated)

                log.debug(
                    f"✅ Evaluated Alert {evaluated.id}",
                    source="AlertCore",
                    payload={"level": evaluated.level, "value": evaluated.evaluated_value}
                )

            except Exception as e:
                log.error(
                    f"❌ Failed to evaluate alert {alert.id}",
                    source="AlertCore",
                    payload={"error": str(e)}
                )

        log.success(f"✅ Completed enrich+evaluate for {len(results)} alerts", source="AlertCore")
        return results

    async def process_alerts(self):
        log.banner("🔍 Processing Alerts: Enrich + Evaluate")

        alerts = self.repo.get_active_alerts()
        if not alerts:
            log.warning("⚠️ No active alerts found", source="AlertCore")
            return []

        evaluated_alerts = await self.enrich_and_evaluate_alerts(alerts)
        return evaluated_alerts




