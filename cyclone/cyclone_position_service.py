# cyclone/cyclone_position_service.py

from datetime import datetime, timezone
from uuid import uuid4

from data.data_locker import DataLocker
from positions.position_service import PositionService
from utils.console_logger import ConsoleLogger as log
from monitor.monitor_utils import LedgerWriter
from data.alert import AlertType, Condition
from alerts.alert_utils import log_alert_summary
from core.constants import DB_PATH


class CyclonePositionService:
    def __init__(self):

        self.data_locker = DataLocker(str(DB_PATH))


    async def update_positions_from_jupiter(self):
        log.info("Starting Position Updates", source="CyclonePosition")
        try:
            result = PositionService.update_jupiter_positions()

            # Log success
            log.log_operation(
                operation_type="Position Updates",
                primary_text=result.get("message", "No message returned"),
                source="CyclonePosition",
                file="cyclone_position_service.py"
            )

            # Ledger write
            ledger = LedgerWriter()
            ledger.write("position_ledger.json", {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "component": "PositionMonitor",
                "operation": "position_update",
                "status": "Success",
                "metadata": result
            })

        except Exception as e:
            log.error(f"❌ Position update failed: {e}", source="CyclonePosition")
            LedgerWriter().write("position_ledger.json", {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "component": "PositionMonitor",
                "operation": "position_update",
                "status": "Error",
                "metadata": {"error": str(e)}
            })

    async def enrich_positions(self):
        log.info("Starting Position Enrichment", source="CyclonePosition")
        try:
            positions = PositionService.get_all_positions()
            count = len(positions)
            log.log_operation(
                operation_type="Position Enrichment",
                primary_text=f"Enriched {count} positions",
                source="CyclonePosition",
                file="cyclone_position_service.py"
            )
            print(f"Enriched {count} positions.")
        except Exception as e:
            log.error(f"Position enrichment failed: {e}", source="CyclonePosition")

    async def create_position_alerts(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.info("Creating position alerts", source="CyclonePosition")

        try:
            positions = self.dl.get_all_positions()

            for p in positions:
                position_id = p["id"]
                asset = p["asset_type"]
                position_type = p.get("position_type", "long")

                base = {
                    "asset": asset,
                    "asset_type": asset,
                    "position_reference_id": position_id,
                    "position_type": position_type,
                    "notification_type": "SMS",
                    "level": "Normal",
                    "last_triggered": None,
                    "status": "Active",
                    "frequency": 1,
                    "counter": 0,
                    "notes": f"Auto-created by Cyclone",
                    "description": f"Alert for {asset}",
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
                    },
                    {
                        **base,
                        "id": str(uuid4()),
                        "alert_type": AlertType.TravelPercentLiquid.value,
                        "alert_class": "Position",
                        "trigger_value": -25,
                        "condition": Condition.BELOW.value
                    }
                ]

                for alert in alerts:
                    self.dl.create_alert(alert)
                    log_alert_summary(alert)

            log.success(f"✅ Created {len(positions) * 3} position alerts.", source="CyclonePosition")

        except Exception as e:
            log.error(f"❌ Failed to create position alerts: {e}", source="CyclonePosition")
