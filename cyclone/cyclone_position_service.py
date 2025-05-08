# cyclone_position_service.py

from datetime import datetime, timezone
from uuid import uuid4
import asyncio
import os

from data.data_locker import DataLocker
from positions.position_service import PositionService
from monitor.monitor_utils import LedgerWriter
from data.alert import AlertType, Condition
from alerts.alert_utils import log_alert_summary
from core.core_imports import DB_PATH, log

print("👁 Viewer using DB path:", os.path.abspath(DB_PATH))

class CyclonePositionService:
    def __init__(self):
        self.dl = DataLocker(str(DB_PATH))



    async def update_positions_from_jupiter(self):
        print("🛰️ [TRACE] CyclonePositionService.update_positions_from_jupiter() CALLED")

        log.info("🚀 Starting Position Updates", source="CyclonePosition")
        try:
            result = await asyncio.to_thread(PositionService.update_jupiter_positions)
            message = result.get("message", "No message returned")
            log.success(f"✅ Jupiter positions updated: {message}", source="CyclonePosition")
            print("📦 Jupiter Update Result:", result)

            from monitor.monitor_utils import LedgerWriter
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

    async def enrich_positions(self):
        log.info("✨ Starting Position Enrichment", source="CyclonePosition")
        try:
            positions = PositionService.get_all_positions()
            count = len(positions)
            log.success(f"✅ Enriched {count} positions", source="CyclonePosition")
            print(f"🔍 Enriched {count} positions.")
        except Exception as e:
            log.error(f"❌ Position enrichment failed: {e}", source="CyclonePosition")

    async def create_position_alerts(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log.info("🔔 Creating position alerts", source="CyclonePosition")
        try:
            positions = self.dl.positions.get_all_positions()
            total_alerts = 0

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
                    "notes": "Auto-created by Cyclone",
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
                    self.dl.alerts.create_alert(alert)
                    log_alert_summary(alert)
                    total_alerts += 1

            log.success(f"✅ Created {total_alerts} total alerts for {len(positions)} positions",
                        source="CyclonePosition")
        except Exception as e:
            log.error(f"❌ Failed to create position alerts: {e}", source="CyclonePosition")

    async def delete_position(self, position_id: str):
        try:
            await asyncio.to_thread(PositionService.delete_position, position_id)
            log.warning(f"🧹 Deleted position: {position_id}", source="CyclonePosition")
        except Exception as e:
            log.error(f"❌ Failed to delete position: {e}", source="CyclonePosition")

    async def clear_positions_backend(self):
        try:
            await asyncio.to_thread(PositionService.clear_positions)
            log.warning("🧹 All positions cleared.", source="CyclonePosition")
        except Exception as e:
            log.error(f"❌ Failed to clear positions: {e}", source="CyclonePosition")

    async def link_hedges(self):
        log.info("🛡 Finding hedge candidates...", source="CyclonePosition")
        try:
            await asyncio.to_thread(PositionService.link_hedges)
            log.success("✅ Hedges linked.", source="CyclonePosition")
        except Exception as e:
            log.error(f"❌ Failed to link hedges: {e}", source="CyclonePosition")

    def view_positions(self):
        """
        CLI viewer for positions — dynamically reloads from DB.
        """
        try:
            index = 0

            while True:
                positions = self.dl.positions.get_all_positions()

                if not positions:
                    os.system("cls" if os.name == "nt" else "clear")
                    print("⚠️ No positions found.\n")
                    break

                total = len(positions)

                if index >= total:
                    index = 0

                os.system("cls" if os.name == "nt" else "clear")
                pos = positions[index]

                print("━━━━━━━━━━ POSITION ━━━━━━━━━━")
                print(f"🆔 ID:           {pos.get('id', '')}")
                print(f"💰 Asset:        {pos.get('asset_type', '')}")
                print(f"📉 Type:         {pos.get('position_type', '')}")
                print(f"📈 Entry Price:  {pos.get('entry_price', '')}")
                print(f"🔄 Current:      {pos.get('current_price', '')}")
                print(f"💣 Liq. Price:   {pos.get('liquidation_price', '')}")
                print(f"🪙 Collateral:   {pos.get('collateral', '')}")
                print(f"📦 Size:         {pos.get('size', '')}")
                print(f"⚖ Leverage:     {pos.get('leverage', '')}x")
                print(f"💵 Value:        {pos.get('value', '')}")
                print(f"💰 PnL (net):    {pos.get('pnl_after_fees_usd', '')}")
                print(f"💼 Wallet:       {pos.get('wallet_name', '')}")
                print(f"🧠 Alert Ref:    {pos.get('alert_reference_id', '')}")
                print(f"🛡 Hedge ID:     {pos.get('hedge_buddy_id', '')}")
                print(f"📅 Updated:      {pos.get('last_updated', '')}")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

                print(f"📘 Page {index + 1} of {total}")
                print("Commands: [N]ext | [P]rev | [Q]uit | [Enter]=Next/Quit")
                cmd = input("→ ").strip().lower()
                if cmd == "q":
                    break
                elif cmd == "p":
                    index = (index - 1) % total
                else:
                    index = (index + 1) % total

        except Exception as e:
            log.error(f"❌ Failed to view positions: {e}", source="CyclonePosition")

