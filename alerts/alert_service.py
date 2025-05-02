from alerts.alert_evaluation_service import AlertEvaluationService
from xcom.notification_service import NotificationService
from data.alert import Alert, AlertLevel
from utils.console_logger import ConsoleLogger as log  # <-- NEW import

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

        alerts = await self.repository.get_active_alerts()

        if not alerts:
            log.warning("No active alerts found.", source="AlertService")
            return

        log.info(f"Fetched {len(alerts)} active alerts.", source="AlertService")

        log.start_timer("process_alerts")

        for alert in alerts:
            try:
                enriched_alert = await self.enrichment_service.enrich(alert)
                new_level = self.evaluation_service.evaluate(enriched_alert)

                if new_level != AlertLevel.NORMAL:
                    log.success(
                        f"ALERT TRIGGERED! {enriched_alert.asset} - {enriched_alert.alert_type} ({new_level})",
                        source="AlertService",
                        payload={"evaluated_value": enriched_alert.evaluated_value,
                                 "trigger_value": enriched_alert.trigger_value}
                    )
                    await self.notification_service.send_alert(enriched_alert)
                else:
                    log.debug(
                        f"Alert evaluated as NORMAL: {enriched_alert.asset} - {enriched_alert.alert_type}",
                        source="AlertService",
                        payload={"evaluated_value": enriched_alert.evaluated_value}
                    )

                await self.repository.update_alert_level(enriched_alert.id, new_level)

            except Exception as e:
                log.error(f"Error processing alert {alert.id}: {e}", source="AlertService")

        log.end_timer("process_alerts", source="AlertService")
        log.banner("ALERT PROCESSING COMPLETE")
