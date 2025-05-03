import asyncio
import logging
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from monitor.monitor_utils import LedgerWriter
from datetime import datetime, timezone
from monitor.price_monitor import PriceMonitor
from uuid import uuid4
from datetime import datetime
from data.alert import AlertType, Condition
from alerts.alert_utils import log_alert_summary
from data.data_locker import DataLocker
from utils.unified_logger import UnifiedLogger
from sonic_labs.hedge_manager import HedgeManager  # Import HedgeManager directly
from positions.position_service import PositionService
from alerts.alert_service_manager import AlertServiceManager
from config.config_manager import UnifiedConfigManager
from config.config_constants import CONFIG_PATH
from utils.console_logger import ConsoleLogger as log




class Cyclone:
    def __init__(self, poll_interval=60):
        self.logger = logging.getLogger("Cyclone")
        self.poll_interval = poll_interval
        self.logger.setLevel(logging.DEBUG)
        self.u_logger = UnifiedLogger()  # Unified logging (now supports cyclone events)

        # Initialize core components
        self.data_locker = DataLocker.get_instance()
        self.price_monitor = PriceMonitor()  # Market Updates
        self.alert_service = AlertServiceManager.get_instance()    # Alert Updates
        self.config = UnifiedConfigManager(CONFIG_PATH).load_config()


        from utils.console_logger import ConsoleLogger as log
        log.banner("🌀  🌪️ CYCLONE ENGINE STARTUP 🌪️ 🌀")
        #log.banner("🌪️  CYCLONE ENGINE STARTUP 🌪️")
        log.success("Cyclone orchestrator initialized.", source="Cyclone")

    async def run_market_updates(self):
        self.logger.info("Starting Market Updates")
        try:
            await self.price_monitor.update_prices(source="Market Updates")
            self.u_logger.log_cyclone(
                operation_type="Market Updates",
                primary_text="Prices updated successfully",
                source="Cyclone",
                file="cyclone.py"
            )
        except Exception as e:
            self.logger.error(f"Market Updates failed: {e}")
            self.u_logger.log_cyclone(
                operation_type="Market Updates",
                primary_text=f"Failed: {e}",
                source="Cyclone",
                file="cyclone.py"
            )

    async def run_position_updates(self):
        self.logger.info("Starting Position Updates")
        try:
            # Fetch and persist positions via your PositionService
            result = PositionService.update_jupiter_positions()

            # Cyclone unified log
            self.u_logger.log_cyclone(
                operation_type="Position Updates",
                primary_text=result.get("message", "No message returned"),
                source="Cyclone",
                file="cyclone.py"
            )

            # Also write to JSON ledger so dashboard picks it up
            ledger = LedgerWriter()
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "component": "PositionMonitor",
                "operation": "position_update",
                "status": "Success",
                "metadata": result
            }
            ledger.write("position_ledger.json", entry)

        except Exception as e:
            # Log failure in both unified logger and ledger
            self.logger.error(f"Position Updates failed: {e}")
            self.u_logger.log_cyclone(
                operation_type="Position Updates",
                primary_text=f"Failed: {e}",
                source="Cyclone",
                file="cyclone.py"
            )
            from monitor.monitor_utils import LedgerWriter
            from datetime import datetime, timezone

            ledger = LedgerWriter()
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "component": "PositionMonitor",
                "operation": "position_update",
                "status": "Error",
                "metadata": {"error": str(e)}
            }
            ledger.write("position_ledger.json", entry)


    async def run_enrich_positions(self):
        self.logger.info("Starting Position Enrichment")
        try:
            enriched_positions = PositionService.get_all_positions()
            count = len(enriched_positions)
            self.u_logger.log_cyclone(
                operation_type="Position Enrichment",
                primary_text=f"Enriched {count} positions",
                source="Cyclone",
                file="cyclone.py"
            )
            print(f"Enriched {count} positions.")
        except Exception as e:
            self.logger.error(f"Position Enrichment failed: {e}")
            self.u_logger.log_cyclone(
                operation_type="Position Enrichment",
                primary_text=f"Failed: {e}",
                source="Cyclone",
                file="cyclone.py"
            )
        self.logger.info("Starting Position Data Enrichment")
        try:
            enriched_positions = PositionService.get_all_positions()
            count = len(enriched_positions)
            self.u_logger.log_cyclone(
                operation_type="Position Enrichment",
                primary_text=f"Enriched {count} positions",
                source="Cyclone",
                file="cyclone.py"
            )
            print(f"Enriched {count} positions.")
        except Exception as e:
            self.logger.error(f"Position Data Enrichment failed: {e}")
            self.u_logger.log_cyclone(
                operation_type="Position Enrichment",
                primary_text=f"Failed: {e}",
                source="Cyclone",
                file="cyclone.py"
            )

    async def run_create_position_alerts(self):
        """
        Create HeatIndex, Profit, and TravelPercentLiquid alerts for all active positions.
        """
        from uuid import uuid4
        from datetime import datetime
        from data.alert import AlertType, Condition
        from alerts.alert_utils import log_alert_summary

        data_locker = DataLocker.get_instance()
        positions = data_locker.get_all_positions()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"ℹ️ [{now}] [Cyclone] Starting Position-Based Alert Creation")

        try:
            for p in positions:
                position_id = p["id"]
                asset = p["asset_type"]
                position_type = p["position_type"]

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
                    "description": f"Position-based alert for {asset}",
                    "liquidation_distance": 0.0,
                    "travel_percent": 0.0,
                    "liquidation_price": 0.0,
                    "evaluated_value": 0.0
                }

                heat_alert = {
                    **base,
                    "id": str(uuid4()),
                    "created_at": now,
                    "alert_type": AlertType.HeatIndex.value,
                    "alert_class": "Position",
                    "trigger_value": 50,
                    "condition": Condition.ABOVE.value
                }

                profit_alert = {
                    **base,
                    "id": str(uuid4()),
                    "created_at": now,
                    "alert_type": AlertType.Profit.value,
                    "alert_class": "Position",
                    "trigger_value": 1000,
                    "condition": Condition.ABOVE.value
                }

                travel_alert = {
                    **base,
                    "id": str(uuid4()),
                    "created_at": now,
                    "alert_type": AlertType.TravelPercentLiquid.value,
                    "alert_class": "Position",
                    "trigger_value": -25,
                    "condition": Condition.BELOW.value
                }

                data_locker.create_alert(heat_alert)
                log_alert_summary(heat_alert)

                data_locker.create_alert(profit_alert)
                log_alert_summary(profit_alert)

                data_locker.create_alert(travel_alert)
                log_alert_summary(travel_alert)

            print(f"✅ [{now}] [Cyclone] ✅ Created {len(positions) * 3} position alerts successfully.")

        except Exception as e:
            print(f"❌ [{now}] [Cyclone] ❌ Failed to create position alerts: {e}")

    async def run_create_portfolio_alerts(self):
        """
        Create portfolio alerts using specific alert types with class='Portfolio'.
        """

        dl = DataLocker.get_instance()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        metrics = [
            (AlertType.TotalValue, "total_value", 50000),
            (AlertType.TotalSize, "total_size", 1.0),
            (AlertType.AvgLeverage, "avg_leverage", 2.0),
            (AlertType.AvgTravelPercent, "avg_travel_percent", 10.0),
            (AlertType.ValueToCollateralRatio, "value_to_collateral_ratio", 1.2),
            (AlertType.TotalHeat, "total_heat", 25.0),
        ]

        for alert_type, metric_desc, trigger_value in metrics:
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
                "position_type": None
            }
            dl.create_alert(alert)
            log_alert_summary(alert)

        print(f"✅ [{now}] [Cyclone] ✅ Portfolio alerts created with typed alert_type and class='Portfolio'.")

    async def run_create_market_alerts(self):
        """
        Create a dummy sample market alert using DataLocker directly.
        """
        log.info("Creating Market Alerts via DataLocker directly", source="Cyclone")
        try:
            from uuid import uuid4
            from data.data_locker import DataLocker

            dummy_alert = {
                "id": str(uuid4()),
                "alert_type": "PRICE_THRESHOLD",
                "alert_class": "Market",
                "asset_type": "BTC",
                "trigger_value": 60000,
                "condition": "ABOVE",
                "notification_type": "SMS",
                "level": "Normal",
                "last_triggered": None,
                "status": "Active",
                "frequency": 1,
                "counter": 0,
                "liquidation_distance": 0.0,
                "travel_percent": -10.0,
                "liquidation_price": 50000,
                "notes": "Sample market alert created by Cyclone",
                "description": "Cyclone test alert",
                "position_reference_id": None,
                "evaluated_value": 59000
            }

            dl = DataLocker.get_instance()
            success = dl.create_alert(dummy_alert)

            if success:
                log.success("✅ Market alert created successfully.", source="Cyclone")
                print("✅ Market alert created successfully.")
            else:
                log.warning("⚠️ Failed to create market alert.", source="Cyclone")
                print("⚠️ Failed to create market alert.")
        except Exception as e:
            log.error(f"❌ Error creating market alert: {e}", source="Cyclone")
            print(f"❌ Error creating market alert: {e}")

    async def run_update_hedges(self):
        self.logger.info("Starting Hedge Update")
        try:
            hedge_groups = HedgeManager.find_hedges()
            self.logger.info(f"Found {len(hedge_groups)} hedge group(s) using find_hedges.")

            positions = [dict(pos) for pos in self.data_locker.read_positions()]
            hedge_manager = HedgeManager(positions)
            hedges = hedge_manager.get_hedges()
            self.logger.info(f"Built {len(hedges)} hedge(s) using HedgeManager instance.")

            self.u_logger.log_cyclone(
                operation_type="Update Hedges",
                primary_text=f"Updated hedges: {len(hedge_groups)} hedge group(s) found, {len(hedges)} hedges built.",
                source="Cyclone",
                file="cyclone.py"
            )
            print(f"Updated hedges: {len(hedge_groups)} group(s) found, {len(hedges)} hedge(s) built.")
        except Exception as e:
            self.logger.error(f"Hedge Update failed: {e}", exc_info=True)
            self.u_logger.log_cyclone(
                operation_type="Update Hedges",
                primary_text=f"Failed: {e}",
                source="Cyclone",
                file="cyclone.py"
            )

    # --- Deletion Logic Refactoring ---

    def _clear_alerts_sync(self):
        """
        Synchronous helper to clear all alert records.
        """
        try:
            conn = self.data_locker.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM alerts")
            conn.commit()
            cursor.close()
            self.logger.info("Cleared alert records successfully.")
            print("Cleared alert records successfully.")
        except Exception as e:
            self.logger.error("Error clearing alerts: %s", e, exc_info=True)
            print(f"Error clearing alerts: {e}")

    def clear_alerts_backend(self):
        """
        Alias for the internal sync clear-alerts method,
        so console and API routes can call it uniformly.
        """
        self._clear_alerts_sync()

    def clear_prices_backend(self):
        try:
            dl = DataLocker.get_instance()
            cursor = dl.conn.cursor()
            cursor.execute("DELETE FROM prices")
            dl.conn.commit()
            deleted = cursor.rowcount
            cursor.close()
            self.u_logger.log_cyclone(
                operation_type="Clear Prices",
                primary_text=f"Cleared {deleted} price record(s)",
                source="Cyclone",
                file="cyclone.py"
            )
            print(f"Price data cleared. {deleted} record(s) deleted.")
        except Exception as e:
            print(f"Error clearing price data: {e}")

    def clear_positions_backend(self):
        try:
            dl = DataLocker.get_instance()
            cursor = dl.conn.cursor()
            cursor.execute("DELETE FROM positions")
            dl.conn.commit()
            deleted = cursor.rowcount
            cursor.close()
            self.u_logger.log_cyclone(
                operation_type="Clear Positions",
                primary_text=f"Cleared {deleted} position record(s)",
                source="Cyclone",
                file="cyclone.py"
            )
            print(f"Positions cleared. {deleted} record(s) deleted.")
        except Exception as e:
            print(f"Error clearing positions: {e}")

    def _clear_all_data_core(self):
        """
        Private helper to clear all alerts, prices, and positions synchronously.
        """
        self._clear_alerts_sync()
        self.clear_prices_backend()
        self.clear_positions_backend()

    async def run_clear_all_data(self):
        """
        Async method to clear all data in a non-interactive way.
        """
        self.logger.info("Starting Clear All Data (non-interactive)")
        try:
            # Run the synchronous _clear_all_data_core in a thread.
            await asyncio.to_thread(self._clear_all_data_core)
            self.u_logger.log_cyclone(
                operation_type="Clear All Data",
                primary_text="All alerts, prices, and positions have been deleted.",
                source="Cyclone",
                file="cyclone.py"
            )
            print("All alerts, prices, and positions have been deleted.")
        except Exception as e:
            self.logger.error(f"Clear All Data failed: {e}", exc_info=True)
            self.u_logger.log_cyclone(
                operation_type="Clear All Data",
                primary_text=f"Failed: {e}",
                source="Cyclone",
                file="cyclone.py"
            )

    def run_delete_all_data(self):
        """
        Synchronous, interactive method to clear all data.
        """
        confirm = input(
            "WARNING: This will DELETE ALL alerts, prices, and positions from the database. Are you sure? (yes/no) [default: yes]: "
        ).strip().lower()
        if confirm == "no":
            print("Deletion aborted.")
            return
        try:
            self._clear_all_data_core()
            self.u_logger.log_cyclone(
                operation_type="Delete All Data",
                primary_text="All alerts, prices, and positions have been deleted.",
                source="Cyclone",
                file="cyclone.py"
            )
            print("All alerts, prices, and positions have been deleted.")
        except Exception as e:
            print(f"Error deleting data: {e}")

    async def run_cleanse_ids(self):
        self.logger.info("Running cleanse_ids step: clearing stale IDs.")
        try:
            self.alert_manager.clear_stale_alerts()
            self.u_logger.log_cyclone(
                operation_type="Clear IDs",
                primary_text="Stale alert, position, and hedge IDs cleared successfully",
                source="Cyclone",
                file="cyclone.py"
            )
            print("Stale IDs have been cleansed successfully.")
        except Exception as e:
            self.logger.error(f"Error cleansing IDs: {e}", exc_info=True)
            print(f"Error cleansing IDs: {e}")

        # In cyclone.py (Cyclone class)

    async def run_alert_enrichment(self):
        """
        Re-enrich all active alerts using the new AlertEnrichmentService.
        """
        try:
            self.logger.info("Starting Alert Enrichment via AlertService")
            await self.alert_service.process_all_alerts()
            self.logger.info("✅ Alerts enriched and evaluated successfully.")
            print("✅ Alerts enriched and evaluated successfully.")
        except Exception as e:
            self.logger.error(f"Alert Enrichment failed: {e}", exc_info=True)
            print(f"❌ Alert Enrichment failed: {e}")

    async def run_enrich_positions(self):
        self.logger.info("Starting Position Enrichment")
        try:
            enriched_positions = PositionService.get_all_positions()
            count = len(enriched_positions)
            self.u_logger.log_cyclone(
                operation_type="Position Enrichment",
                primary_text=f"Enriched {count} positions",
                source="Cyclone",
                file="cyclone.py"
            )
            print(f"Enriched {count} positions.")
        except Exception as e:
            self.logger.error(f"Position Enrichment failed: {e}")
            self.u_logger.log_cyclone(
                operation_type="Position Enrichment",
                primary_text=f"Failed: {e}",
                source="Cyclone",
                file="cyclone.py"
            )

    async def run_cycle(self, steps=None):
        """
        Master run_cycle method to run various steps.
        New default ordering includes "enrich alerts" and renames the position enrichment step.
        """
        available_steps = {
            "clear_all_data": self.run_clear_all_data,
            "market": self.run_market_updates,
            "position": self.run_position_updates,
            "cleanse_ids": self.run_cleanse_ids,
            "link_hedges": self.run_link_hedges,
            "enrich positions": self.run_enrich_positions,  # Renamed step for positions
            "enrich alerts": self.run_alert_enrichment,  # New step for alert enrichment
            "create_market_alerts": self.run_create_market_alerts,
            "create_portfolio_alerts": self.run_create_portfolio_alerts,
            "create_position_alerts": self.run_create_position_alerts,
            "create_system_alerts": self.run_create_system_alerts,
            "update_evaluated_value": self.run_update_evaluated_value,
            "alert": self.run_alert_updates,
            "system": self.run_system_updates
        }
        if steps:
            for step in steps:
                if step in available_steps:
                    await available_steps[step]()
                else:
                    self.logger.warning(f"Unknown step requested: {step}")
        else:
            for step in [
                "clear_all_data", "market", "position", "cleanse_ids",
                "enrich positions", "enrich alerts", "create_market_alerts",
                "create_position_alerts", "create_system_alerts", "create_portfolio_alerts",
                "update_evaluated_value", "alert", "system", "link_hedges"
            ]:
                await available_steps[step]()

    async def run_link_hedges(self):
        self.logger.info("Starting Link Hedges step")
        try:
            hedge_groups = HedgeManager.find_hedges()
            count = len(hedge_groups)
            msg = f"Linked hedges: {count} hedge group(s) found."
            self.u_logger.log_cyclone(
                operation_type="Link Hedges",
                primary_text=msg,
                source="Cyclone",
                file="cyclone.py"
            )
            print(msg)
        except Exception as e:
            self.logger.error(f"Link Hedges failed: {e}", exc_info=True)
            self.u_logger.log_cyclone(
                operation_type="Link Hedges",
                primary_text=f"Failed: {e}",
                source="Cyclone",
                file="cyclone.py"
            )


    async def run_create_system_alerts(self):
        self.logger.info("Creating System Alerts")
        return

    async def run_update_evaluated_value(self):
        """
        Update evaluated values for all alerts via AlertService.
        """
        self.logger.info("Starting Evaluated Value Update for Alerts")
        try:
            await self.alert_service.process_all_alerts()
            self.u_logger.log_cyclone(
                operation_type="Update Evaluated Value",
                primary_text="Alert evaluated values updated successfully",
                source="Cyclone",
                file="cyclone.py"
            )
            print("✅ Alert evaluated values updated successfully.")
        except Exception as e:
            self.logger.error(f"Updating evaluated values failed: {e}", exc_info=True)
            self.u_logger.log_cyclone(
                operation_type="Update Evaluated Value",
                primary_text=f"Failed: {e}",
                source="Cyclone",
                file="cyclone.py"
            )

    async def run_alert_updates(self):
        """
        Evaluate and process all alerts using the new AlertService.
        """
        log.info("Starting Alert Evaluations via AlertServiceManager", source="Cyclone")
        try:
            await self.alert_service.process_all_alerts()
            log.success("✅ Alert evaluations and notifications processed successfully.", source="Cyclone")
            print("✅ Alert evaluations and notifications processed successfully.")
        except Exception as e:
            log.error(f"❌ Alert Evaluations failed: {e}", source="Cyclone")
            print(f"❌ Alert Evaluations failed: {e}")

    async def run_system_updates(self):
        self.logger.info("Starting System Updates")
        try:
            self.u_logger.log_cyclone(
                operation_type="System Updates",
                primary_text="System state updated",
                source="Cyclone",
                file="cyclone.py"
            )
        except Exception as e:
            self.logger.error(f"System Updates failed: {e}")
            self.u_logger.log_cyclone(
                operation_type="System Updates",
                primary_text=f"Failed: {e}",
                source="Cyclone",
                file="cyclone.py"
            )

    def view_prices_backend(self):
        try:
            dl = DataLocker.get_instance()
            cursor = dl.conn.cursor()
            cursor.execute("SELECT * FROM prices")
            prices = cursor.fetchall()
            cursor.close()

            print("\n----- Prices -----")
            print(f"Found {len(prices)} price record(s).\n")

            for price in prices:
                p = dict(price)
                print(f"ID: {p.get('id', '-')}")
                print(f"Asset: {p.get('asset_type', '-')}")
                print(f"Current Price: {p.get('current_price', '-')}")
                print(f"Timestamp: {p.get('timestamp', '-')}")
                print("-" * 40)
            print("")
        except Exception as e:
            print(f"Error viewing prices: {e}")

    def view_positions_backend(self):
        try:
            from rich.console import Console
            from rich.table import Table
            console = Console()
            dl = DataLocker.get_instance()
            cursor = dl.conn.cursor()
            cursor.execute("SELECT * FROM positions")
            positions = cursor.fetchall()
            cursor.close()

            table = Table(title="Positions", show_lines=True)
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Asset", style="magenta")
            table.add_column("Pos Type", style="red")
            table.add_column("Entry", justify="right")
            table.add_column("Liquidation", justify="right")
            table.add_column("Travel%", justify="right")
            table.add_column("Value", justify="right")
            table.add_column("Collateral", justify="right")
            table.add_column("Size", justify="right")
            table.add_column("Leverage", justify="right")
            table.add_column("Wallet", style="green")
            table.add_column("Last Updated", style="dim")

            for row in positions:
                pos = dict(row)
                table.add_row(
                    str(pos.get("id", "")),
                    str(pos.get("asset_type", "")),
                    str(pos.get("position_type", "")) if pos.get("position_type") else "-",
                    f'{pos.get("entry_price", 0):.2f}',
                    f'{pos.get("liquidation_price", 0):.2f}',
                    f'{pos.get("travel_percent", 0):.2f}',
                    f'{pos.get("value", 0):.2f}',
                    f'{pos.get("collateral", 0):.2f}',
                    f'{pos.get("size", 0):.2f}',
                    f'{pos.get("leverage", 0):.2f}',
                    str(pos.get("wallet_name", "")),
                    str(pos.get("last_updated", ""))
                )
            console.print(table)
        except Exception as e:
            print(f"Error viewing positions: {e}")

    def view_alerts_backend(self):
        try:
            dl = DataLocker.get_instance()
            cursor = dl.conn.cursor()
            cursor.execute("SELECT * FROM alerts")
            alerts = cursor.fetchall()
            cursor.close()

            print("\n🔔 Alerts")
            print(f"Found {len(alerts)} alert record(s).\n")

            # ANSI color codes for levels
            color_map = {
                "Normal": "\033[34m",  # blue
                "Low": "\033[32m",  # green
                "Medium": "\033[33m",  # yellow
                "High": "\033[31m"  # red
            }
            reset = "\033[0m"

            for a in alerts:
                alert = dict(a)
                level = alert.get("level", "-")
                lvl_color = color_map.get(level, "")
                colored_level = f"{lvl_color}{level}{reset}"

                print(f"🆔 ID:               {alert.get('id', '-')}")
                print(f"📌 Type:             {alert.get('alert_type', '-')}")
                print(f"🏷️ Class:            {alert.get('alert_class', '-')}")
                print(f"💰 Asset:            {alert.get('asset_type', '-')}")
                print(f"🎯 Trigger Value:    {alert.get('trigger_value', '-')}")
                print(f"📈 Evaluated Value:  {alert.get('evaluated_value', '-')}")
                print(f"⚙️ Condition:        {alert.get('condition', '-')}")
                print(f"🔔 Notification:     {alert.get('notification_type', '-')}")
                print(f"📊 Level:            {colored_level}")
                print(f"📍 Position Ref:     {alert.get('position_reference_id', '-')}")
                pos_type = alert.get("position_type")
                print(f"📊 Position Type:    {pos_type if pos_type is not None else '-'}")
                print(f"🕒 Created at:       {alert.get('created_at', '-')}")
                print("-" * 40)
            print("")
        except Exception as e:
            print(f"Error viewing alerts: {e}")

    def view_wallets_backend(self):
        try:
            from pprint import pprint
            dl = DataLocker.get_instance()
            cursor = dl.conn.cursor()
            cursor.execute("SELECT * FROM wallets")
            wallets = cursor.fetchall()
            cursor.close()
            print("----- Wallets -----")
            print(f"Found {len(wallets)} wallet record(s).")
            for row in wallets:
                pprint(dict(row))
        except Exception as e:
            print(f"Error viewing wallets: {e}")

    def add_wallet_backend(self):
        try:
            name = input("Enter wallet name: ").strip()
            public_address = input("Enter public address: ").strip()
            private_address = input("Enter private address: ").strip()
            image_path = input("Enter image path: ").strip()
            balance_str = input("Enter balance: ").strip()
            try:
                balance = float(balance_str)
            except Exception:
                balance = 0.0
            dl = DataLocker.get_instance()
            cursor = dl.conn.cursor()
            cursor.execute(
                "INSERT INTO wallets (name, public_address, private_address, image_path, balance) VALUES (?, ?, ?, ?, ?)",
                (name, public_address, private_address, image_path, balance)
            )
            dl.conn.commit()
            inserted = cursor.rowcount
            cursor.close()
            self.u_logger.log_cyclone(
                operation_type="Add Wallet",
                primary_text=f"Added wallet '{name}' ({inserted} row inserted)",
                source="Cyclone",
                file="cyclone.py"
            )
            print(f"Wallet added successfully. {inserted} record(s) inserted.")
        except Exception as e:
            print(f"Error adding wallet: {e}")

    def clear_wallets_backend(self):
        try:
            dl = DataLocker.get_instance()
            cursor = dl.conn.cursor()
            cursor.execute("DELETE FROM wallets")
            dl.conn.commit()
            deleted = cursor.rowcount
            cursor.close()
            self.u_logger.log_cyclone(
                operation_type="Clear Wallets",
                primary_text=f"Cleared {deleted} wallet record(s)",
                source="Cyclone",
                file="cyclone.py"
            )
            print(f"Wallets cleared. {deleted} record(s) deleted.")
        except Exception as e:
            print(f"Error clearing wallets: {e}")

    def clear_alert_ledger_backend(self):
        try:
            dl = DataLocker.get_instance()
            cursor = dl.conn.cursor()
            cursor.execute("DELETE FROM alert_ledger")
            dl.conn.commit()
            deleted = cursor.rowcount
            cursor.close()
            self.u_logger.log_cyclone(
                operation_type="Clear Alert Ledger",
                primary_text=f"Cleared {deleted} alert ledger record(s)",
                source="Cyclone",
                file="cyclone.py"
            )
            print(f"Alert ledger cleared. {deleted} record(s) deleted.")
        except Exception as e:
            print(f"Error clearing alert ledger: {e}")

    async def run_delete_position(self):
        position_id = input("Enter the Position ID to delete: ").strip()
        if not position_id:
            print("No position ID provided.")
            return
        try:
            from positions.position_service import delete_position_and_cleanup
            await asyncio.to_thread(delete_position_and_cleanup, position_id)
            print(f"Position {position_id} deleted along with associated alerts and hedges.")
        except Exception as e:
            print(f"Error deleting position {position_id}: {e}")

    async def run_update_evaluated_value(self):
        """
        Update evaluated values for all alerts via AlertService.
        """
        log.info("Starting Evaluated Value Update for Alerts", source="Cyclone")
        try:
            await self.alert_service.process_all_alerts()
            log.success("✅ Alert evaluated values updated successfully.", source="Cyclone")
            print("✅ Alert evaluated values updated successfully.")
        except Exception as e:
            log.error(f"❌ Updating evaluated values failed: {e}", source="Cyclone")
            print(f"❌ Updating evaluated values failed: {e}")

    async def run_alert_updates(self):
        """
        Evaluate and process all alerts using the new AlertService.
        """
        self.logger.info("Starting Alert Evaluations via AlertServiceManager")
        try:
            await self.alert_service.process_all_alerts()
            self.u_logger.log_cyclone(
                operation_type="Alert Evaluations",
                primary_text="Alert evaluations and notifications processed successfully",
                source="Cyclone",
                file="cyclone.py"
            )
            print("✅ Alert evaluations and notifications processed successfully.")
        except Exception as e:
            self.logger.error(f"Alert Evaluations failed: {e}", exc_info=True)
            self.u_logger.log_cyclone(
                operation_type="Alert Evaluations",
                primary_text=f"Failed: {e}",
                source="Cyclone",
                file="cyclone.py"
            )

    async def run_system_updates(self):
        self.logger.info("Starting System Updates")
        try:
            self.u_logger.log_cyclone(
                operation_type="System Updates",
                primary_text="System state updated",
                source="Cyclone",
                file="cyclone.py"
            )
        except Exception as e:
            self.logger.error(f"System Updates failed: {e}")
            self.u_logger.log_cyclone(
                operation_type="System Updates",
                primary_text=f"Failed: {e}",
                source="Cyclone",
                file="cyclone.py"
            )

# The interactive console (menu and navigation) has been moved into a separate helper class.
# The Cyclone class now focuses solely on processing logic.
if __name__ == "__main__":
    cyclone = Cyclone(poll_interval=60)
    from cyclone_console_helper import CycloneConsoleHelper
    helper = CycloneConsoleHelper(cyclone)
    helper.run()
