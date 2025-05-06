import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.console_logger import ConsoleLogger as log  # <-- NEW import
from alerts.alert_evaluation_service import AlertEvaluationService
from xcom.notification_service import NotificationService
from data.alert import Alert, AlertLevel


class AlertService:
    def __init__(self, repository, enrichment_service, config_loader):
        """
        :param repository: Object with DB methods (get_active_alerts, update_alert_level, etc.)
        :param enrichment_service: Object that enriches alerts (adds evaluated_value, etc.)
        :param config_loader: Callable returning latest config dictionary
        """
        self.repository = repository
        self.enrichment_service = enrichment_service
        #self.evaluation_service = AlertEvaluationService(thresholds=config_loader().get("alert_ranges", {}))
        self.evaluation_service = AlertEvaluationService(thresholds=config_loader().get("alert_limits", {}))

        self.notification_service = NotificationService(config_loader)

    async def process_all_alerts(self):
        """
        Main method to fetch, enrich, evaluate, and notify alerts.
        """
        log.banner("STARTING ALERT PROCESSING")

        alerts = self.repository.get_active_alerts()  # ✅ Already synchronous — no await needed

        if not alerts:
            log.warning("No active alerts found.", source="AlertService")
            return

        log.info(f"Fetched {len(alerts)} active alerts.", source="AlertService")
        log.start_timer("process_alerts")

        try:
            # ⚡ Enrich alerts using async batch
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
                            f"✅ Alert evaluated as NORMAL: {evaluated.asset} - {evaluated.alert_type}",
                            source="AlertService",
                            payload={"evaluated_value": evaluated.evaluated_value}
                        )

                    # ✅ Ensure DB is updated
                    self.repository.update_alert_level(evaluated.id, evaluated.level)
                    self.repository.update_alert_evaluated_value(evaluated.id, evaluated.evaluated_value)

                except Exception as inner:
                    log.error(f"⚠️ Error handling alert {alert.id}: {inner}", source="AlertService")

        except Exception as outer:
            log.error(f"❌ Top-level alert processing error: {outer}", source="AlertService")

        log.end_timer("process_alerts", source="AlertService")
        log.banner("ALERT PROCESSING COMPLETE")


