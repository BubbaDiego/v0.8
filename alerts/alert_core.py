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
        self.config_loader = config_loader
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

    async def run_alert_evaluation(self):
        log.banner("🚨 Alert Evaluation Triggered")
        return await self.process_alerts()

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

    async def create_portfolio_alerts(self):
        log.banner("📦 Creating Portfolio Alerts")

        try:
            config = self.config_loader()
            alert_ranges = config.get("alert_ranges", {})
            log.info("Loaded alert_ranges from config", source="AlertCore", payload={"metric_count": len(alert_ranges)})

            def build(metric, trigger_value):
                alert_id = str(uuid4())
                payload = {
                    "id": alert_id,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "alert_type": metric,
                    "alert_class": "Portfolio",
                    "asset": "PORTFOLIO",
                    "asset_type": "ALL",
                    "trigger_value": trigger_value,
                    "condition": "ABOVE",
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
                    "description": metric.lower(),
                    "position_reference_id": None,
                    "evaluated_value": 0.0,
                    "position_type": "N/A"
                }
                log.debug("Built alert payload", source="AlertCore", payload=payload)
                return payload

            created = 0
            for metric, thresholds in alert_ranges.items():
                if not isinstance(thresholds, dict):
                    log.warning("Skipping malformed alert config", source="AlertCore", payload={"metric": metric})
                    continue

                trigger = thresholds.get("high") or thresholds.get("medium") or thresholds.get("low")
                if trigger is not None:
                    alert_data = build(metric, trigger)
                    created_flag = await self.create_alert(alert_data)
                    if created_flag:
                        created += 1
                        log.success("✅ Alert created", source="AlertCore", payload={"metric": metric, "trigger": trigger})
                    else:
                        log.warning("⚠️ Failed to create alert", source="AlertCore", payload={"metric": metric})

            log.success(f"✅ Portfolio alert creation complete", source="AlertCore", payload={"created": created})

        except Exception as e:
            log.error(f"❌ Failed to create portfolio alerts: {e}", source="AlertCore")


    async def create_position_alerts(self):
        log.banner("📊 Creating Position Alerts")

        try:
            alerts_created = 0
            alerts_skipped = 0
            config = self.config_loader()
            thresholds = config.get("alert_ranges", {})
            log.info("📁 Loaded alert config", source="AlertCore", payload={"threshold_keys": list(thresholds.keys())})

            positions = self.repo.data_locker.positions.get_all_positions()
            log.info("📥 Fetched positions", source="AlertCore", payload={"count": len(positions)})

            for pos in positions:
                for metric_key, limits in thresholds.items():
                    if not isinstance(limits, dict):
                        log.warning("Skipping malformed metric config", source="AlertCore", payload={"metric": metric_key})
                        continue

                    trigger = limits.get("high") or limits.get("medium") or limits.get("low")
                    if trigger is None:
                        alerts_skipped += 1
                        continue

                    alert_data = {
                        "id": str(uuid4()),
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "alert_type": metric_key,
                        "alert_class": "Position",
                        "asset": pos["asset_type"],
                        "asset_type": pos["asset_type"],
                        "trigger_value": trigger,
                        "condition": "ABOVE",
                        "notification_type": "SMS",
                        "level": "Normal",
                        "last_triggered": None,
                        "status": "Active",
                        "frequency": 1,
                        "counter": 0,
                        "liquidation_distance": pos.get("liquidation_distance", 0.0),
                        "travel_percent": pos.get("travel_percent", 0.0),
                        "liquidation_price": pos.get("liquidation_price", 0.0),
                        "notes": f"Auto alert for {pos['id']}",
                        "description": metric_key,
                        "position_reference_id": pos["id"],
                        "evaluated_value": 0.0,
                        "position_type": pos.get("position_type", "N/A")
                    }

                    log.debug("🔧 Prepared position alert", source="AlertCore", payload={"position": pos["id"], "metric": metric_key})
                    if await self.create_alert(alert_data):
                        log.success("✅ Created position alert", source="AlertCore", payload={"id": alert_data["id"], "type": metric_key})
                        alerts_created += 1
                    else:
                        log.warning("⚠️ Failed to create alert", source="AlertCore", payload={"position_id": pos["id"], "metric": metric_key})

            log.success("📊 Position Alert Summary", source="AlertCore", payload={
                "alerts_created": alerts_created,
                "alerts_skipped": alerts_skipped,
                "positions": len(positions)
            })

        except Exception as e:
            log.error(f"💥 create_position_alerts() failed: {e}", source="AlertCore")


    async def create_all_alerts(self):
        log.banner("🛠 Starting Full Alert Creation")

        try:
            log.start_timer("create_all_alerts")

            await self.create_portfolio_alerts()
            await self.create_position_alerts()

            log.end_timer("create_all_alerts", source="AlertCore")
            log.success("🛠 Alert generation complete", source="AlertCore")

        except Exception as e:
            log.error(f"❌ Failed in create_all_alerts: {e}", source="AlertCore")


    async def enrich_all_alerts(self):
        """
        Runs enrichment only — no evaluation or notification.
        """
        log.banner("💡 Enriching All Alerts")

        try:
            alerts = self.repo.get_active_alerts()
            if not alerts:
                log.warning("⚠️ No active alerts to enrich", source="AlertCore")
                return []

            log.info(f"📥 Loaded {len(alerts)} alerts", source="AlertCore")
            enriched = await self.enricher.enrich_all(alerts)

            log.success("✅ Alert enrichment complete", source="AlertCore", payload={"count": len(enriched)})
            return enriched

        except Exception as e:
            log.error(f"❌ enrich_all_alerts() failed: {e}", source="AlertCore")
            return []

    async def update_evaluated_values(self):
        """
        Evaluates alerts and updates only their evaluated_value (no notify).
        """
        log.banner("🧪 Updating Evaluated Values")

        try:
            alerts = self.repo.get_active_alerts()
            if not alerts:
                log.warning("⚠️ No active alerts to update", source="AlertCore")
                return

            enriched = await self.enricher.enrich_all(alerts)
            for alert in enriched:
                try:
                    evaluated = self.evaluator.evaluate(alert)
                    self.evaluator.update_alert_evaluated_value(evaluated.id, evaluated.evaluated_value)
                    log.success("✅ Updated evaluated_value", source="AlertCore", payload={
                        "id": evaluated.id,
                        "value": evaluated.evaluated_value
                    })
                except Exception as e:
                    log.error(f"❌ Failed to update value for alert {alert.id}: {e}", source="AlertCore")

            log.success("✅ Completed evaluated value update", source="AlertCore")

        except Exception as e:
            log.error(f"💥 update_evaluated_values() failed: {e}", source="AlertCore")
