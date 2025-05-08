# cyclone/cyclone_alert_service.py

from alerts.alert_service_manager import AlertServiceManager
from core.core_imports import log


class CycloneAlertService:
    def __init__(self):
        self.alert_service = AlertServiceManager.get_instance()

    async def enrich_all_alerts(self):
        log.info("Starting Alert Enrichment via AlertService", source="CycloneAlerts")
        try:
            await self.alert_service.process_all_alerts()
            log.success("✅ Alerts enriched and evaluated successfully.", source="CycloneAlerts")
        except Exception as e:
            log.error(f"❌ Alert Enrichment failed: {e}", source="CycloneAlerts")

    async def update_evaluated_values(self):
        log.info("Starting Evaluated Value Update for Alerts", source="CycloneAlerts")
        try:
            await self.alert_service.process_all_alerts()
            log.success("✅ Evaluated values updated.", source="CycloneAlerts")
        except Exception as e:
            log.error(f"❌ Failed to update evaluated values: {e}", source="CycloneAlerts")

    async def run_alert_updates(self):
        log.info("Running alert evaluations & notifications", source="CycloneAlerts")
        try:
            await self.alert_service.process_all_alerts()
            log.success("✅ Alert evaluations & notifications completed.", source="CycloneAlerts")
        except Exception as e:
            log.error(f"❌ Alert update cycle failed: {e}", source="CycloneAlerts")

    async def clear_stale_alerts(self):
        try:
            await self.alert_service.clear_stale_alerts()  # Add if not implemented
            log.success("✅ Stale alerts cleared.", source="CycloneAlerts")
        except Exception as e:
            log.error(f"❌ Failed to clear stale alerts: {e}", source="CycloneAlerts")
