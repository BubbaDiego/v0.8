import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.console_logger import ConsoleLogger as log
from alerts.alert_evaluation_service import AlertEvaluationService
from positions.position_core_service import PositionCoreService
from xcom.notification_service import NotificationService
from data.alert import AlertLevel


class AlertService:
    def __init__(self, repository, enrichment_service, config_loader):
        """
        :param repository: DB-facing object with methods like get_alerts(), delete_alert(), etc.
        :param enrichment_service: Enriches alerts with evaluated_value, etc.
        :param config_loader: Callable returning latest config dict (e.g. from alert_limits.json)
        """
        self.repository = repository
        self.enrichment_service = enrichment_service
        self.evaluation_service = AlertEvaluationService(
            thresholds=config_loader().get("alert_limits", {})
        )
        self.notification_service = NotificationService(config_loader)
        self.position_core = PositionCoreService(repository.data_locker)  # ✅ Injected for position awareness

    async def process_all_alerts(self):
        """
        Main method to fetch, enrich, evaluate, and notify alerts.
        """
        log.banner("STARTING ALERT PROCESSING")

        alerts = self.repository.get_active_alerts()

        if not alerts:
            log.warning("No active alerts found.", source="AlertService")
            return

        log.info(f"Fetched {len(alerts)} active alerts.", source="AlertService")
        log.start_timer("process_alerts")

        try:
            enriched_alerts = await self.enrichment_service.enrich_all(alerts)

            for alert in enriched_alerts:
                try:
                    evaluated = self.evaluation_service.evaluate(alert)

                    if evaluated.level != AlertLevel.NORMAL:
                        log.success(
                            f"🚨 ALERT TRIGGERED: {evaluated.asset} - {evaluated.alert_type} ({evaluated.level})",
                            source="AlertService",
                            payload={"evaluated_value": evaluated.evaluated_value}
                        )
                        self.notification_service.send_alert(evaluated)
                    else:
                        log.debug(
                            f"✅ Alert NORMAL: {evaluated.asset} - {evaluated.alert_type}",
                            source="AlertService",
                            payload={"evaluated_value": evaluated.evaluated_value}
                        )

                    self.repository.update_alert_level(evaluated.id, evaluated.level)
                    self.repository.update_alert_evaluated_value(evaluated.id, evaluated.evaluated_value)

                except Exception as inner:
                    log.error(f"⚠️ Error evaluating alert {alert.id}: {inner}", source="AlertService")

        except Exception as outer:
            log.error(f"❌ Top-level alert processing error: {outer}", source="AlertService")

        log.end_timer("process_alerts", source="AlertService")
        log.banner("ALERT PROCESSING COMPLETE")

    def clear_stale_alerts(self):
        """
        Deletes alerts linked to missing positions and clears stale references from positions.
        """
        log.banner("🧹 CLEARING STALE ALERTS")

        alerts = self.repository.get_alerts()
        positions = self.position_core.get_all_positions()

        valid_position_ids = {pos.get("id") for pos in positions}
        deleted_alerts = 0

        for alert in alerts:
            pos_id = alert.get("position_reference_id")
            if pos_id and pos_id not in valid_position_ids:
                if self.repository.delete_alert(alert["id"]):
                    deleted_alerts += 1
                    log.info(f"🗑 Deleted stale alert {alert['id']} (dangling pos ref)", source="AlertService")

        log.success(f"✅ Deleted {deleted_alerts} stale alerts", source="AlertService")

        alerts = self.repository.get_alerts()  # refreshed
        valid_alert_ids = {alert.get("id") for alert in alerts}
        updated_positions = 0

        for pos in positions:
            alert_id = pos.get("alert_reference_id")
            if alert_id and alert_id not in valid_alert_ids:
                self.repository.clear_alert_reference(pos.get("id"))
                updated_positions += 1
                log.info(f"🔗 Cleared invalid alert ref in position {pos['id']}", source="AlertService")

        log.success(f"✅ Cleared alert refs in {updated_positions} position(s)", source="AlertService")

        try:
            from sonic_labs.hedge_manager import HedgeManager
            HedgeManager.clear_hedge_data()
            log.success("✅ Cleared hedge associations in positions", source="AlertService")
        except Exception as e:
            log.warning(f"⚠️ Skipped hedge cleanup: {e}", source="AlertService")

        log.banner("🧼 STALE ALERT CLEANUP COMPLETE")
