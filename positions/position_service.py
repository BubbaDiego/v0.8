#!/usr/bin/env python
"""
Module: position_service.py
Description:
    Provides services for retrieving, enriching, and updating positions data.
    This includes methods to:
      - Get and enrich all positions.
      - Update Jupiter positions by fetching from the external API.
      - Delete existing Jupiter positions.
      - Record snapshots of aggregated positions data.
"""

import logging
from typing import List, Dict, Any
import requests
from datetime import datetime
from data.data_locker import DataLocker
from core.constants import DB_PATH
from utils.calc_services import CalcServices
#from alerts.alert_evaluator import AlertEvaluator
#from utils.unified_logger import UnifiedLogger
#from api.dydx_api import DydxAPI

logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)
if not logger.handlers:
    import sys
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(levelname)s] %(asctime)s - %(name)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class PositionService:
    # Mapping for market mints to asset types
    MINT_TO_ASSET = {
        "3NZ9JMVBmGAqocybic2c7LQCJScmgsAZ6vQqTDzcqmJh": "BTC",
        "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs": "ETH",
        "So11111111111111111111111111111111111111112": "SOL"
    }

    def update_position_and_alert(pos: dict, data_locker):
        """
        After updating a position, re-evaluate its alert state and update the alert record.
        """
        data_locker.create_position(pos)  # Or update_position() as appropriate

        evaluator = AlertEvaluator({}, data_locker)  # Pass an empty config or load one as needed
        evaluator.update_alert_for_position(pos)

    @staticmethod
    @staticmethod
    def get_all_positions(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
        """
        Retrieve all positions from the database, enrich each,
        and inject wallet info as `wallet` object.
        """
        try:
            dl = DataLocker.get_instance(db_path)
            raw_positions = dl.read_positions()
            positions = []

            for pos in raw_positions:
                pos_dict = {key: pos[key] for key in pos.keys()}
                enriched = PositionService.enrich_position(pos_dict)

                # 🔗 Attach wallet object
                wallet_name = enriched.get("wallet_name")
                wallet_data = dl.get_wallet_by_name(wallet_name) if wallet_name else None
                enriched["wallet"] = wallet_data

                positions.append(enriched)

            return positions

        except Exception as e:
            logger.error(f"Error retrieving and enriching positions: {e}", exc_info=True)
            raise

    @staticmethod
    def enrich_position(position: Dict[str, Any]) -> Dict[str, Any]:
        try:
            logger.debug(f"Enriching position: {position}")
            calc = CalcServices()
            # Ensure required numeric fields have a default value
            required_fields = ['entry_price', 'current_price', 'liquidation_price', 'collateral', 'size']
            for field in required_fields:
                if position.get(field) is None:
                    if field == 'current_price' and position.get('entry_price') is not None:
                        logger.debug(f"Field '{field}' is None, defaulting to entry_price: {position['entry_price']}")
                        position[field] = position['entry_price']
                    else:
                        logger.debug(f"Field '{field}' is None, defaulting to 0.0")
                        position[field] = 0.0

            # Convert values to float explicitly
            try:
                position['entry_price'] = float(position['entry_price'])
                position['current_price'] = float(position['current_price'])
                position['liquidation_price'] = float(position['liquidation_price'])
                position['collateral'] = float(position['collateral'])
                position['size'] = float(position['size'])
                logger.debug("Converted required fields to float.")
            except Exception as conv_err:
                logger.error(f"Error converting fields to float: {conv_err}")
                raise

            # Compute profit value
            profit = calc.calculate_value(position)
            position['profit'] = profit
            logger.debug(f"Calculated profit: {profit}")

            # Compute leverage
            collateral = position['collateral']
            size = position['size']
            if collateral > 0:
                leverage = calc.calculate_leverage(size, collateral)
                position['leverage'] = leverage
                logger.debug(f"Calculated leverage: {leverage}")
            else:
                position['leverage'] = None
                logger.debug("Collateral is zero or negative; leverage set to None.")

            logger.debug(
                f"[BEFORE travel_percent calc] ID={position.get('id', 'N/A')} | type={position.get('position_type')} | entry={position.get('entry_price')} | current={position.get('current_price')} | liquidation={position.get('liquidation_price')}")
            # Compute travel percent if relevant data exists
            if all(k in position for k in ['entry_price', 'current_price', 'liquidation_price']):
                travel_percent = calc.calculate_travel_percent(
                    position.get('position_type', ''),
                    position['entry_price'],
                    position['current_price'],
                    position['liquidation_price']
                )
                position['travel_percent'] = travel_percent
                logger.debug(
                    f"[AFTER travel_percent calc] ID={position.get('id', 'N/A')} | travel_percent={travel_percent:.2f}%")

                # Final enriched position debug
                logger.debug(f"[ENRICHED position] {position}")
            else:
                position['travel_percent'] = None
                logger.debug("Missing one of entry_price, current_price, or liquidation_price; travel_percent set to None.")

            # Compute liquidation distance (absolute difference)
            liq_distance = calc.calculate_liquid_distance(
                position['current_price'],
                position['liquidation_price']
            )
            position['liquidation_distance'] = liq_distance
            logger.debug(f"Calculated liquidation_distance: {liq_distance}")

            # Compute composite risk index using the multiplicative model.
            composite_risk = calc.calculate_composite_risk_index(position)
            position["heat_index"] = composite_risk
            # *** FIX: Also update current_heat_index ***
            position["current_heat_index"] = composite_risk
            logger.debug(f"Computed composite risk index: {composite_risk} and set current_heat_index accordingly.")

            logger.debug(f"Enriched position: {position}")
            return position
        except Exception as e:
            logger.error(f"Error enriching position data: {e}", exc_info=True)
            raise

    def delete_position_and_cleanup(position_id: str, db_path: str = DB_PATH) -> None:
        """
        Deletes a position and cleans up all associated alerts and hedge references.

        Steps:
          1. Delete all alerts whose position_reference_id equals position_id.
          2. Clear hedge associations in positions that reference the position.
          3. Delete the position record from the database.
        """
        try:
            # Get the DataLocker instance
            dl = DataLocker.get_instance(db_path)
            # Instantiate AlertController for alert deletion operations
            alert_ctrl = AlertController(db_path)

            # Step 1: Delete associated alerts
            alerts = dl.get_alerts()
            alerts_deleted = 0
            for alert in alerts:
                if alert.get("position_reference_id") == position_id:
                    if alert_ctrl.delete_alert(alert["id"]):
                        alerts_deleted += 1
                        logger.info(f"Deleted alert {alert['id']} for position {position_id}")
                    else:
                        logger.error(f"Failed to delete alert {alert['id']} for position {position_id}")
            logger.info(f"Total alerts deleted for position {position_id}: {alerts_deleted}")

            # Step 2: Clear hedge associations referencing this position.
            # If the position is part of any hedge, reset its hedge_buddy_id to NULL.
            cursor = dl.db.get_cursor()
            cursor.execute("UPDATE positions SET hedge_buddy_id = NULL WHERE hedge_buddy_id = ?", (position_id,))
            dl.db.commit()
            logger.info(f"Cleared hedge associations for position {position_id}")

            # Step 3: Delete the position record
            dl.delete_position(position_id)
            logger.info(f"Position {position_id} deleted successfully.")

        except Exception as ex:
            logger.exception(f"Error during deletion of position {position_id}: {ex}")
            raise

    @staticmethod
    def fill_positions_with_latest_price(positions: List[Any]) -> List[Dict[str, Any]]:
        try:
            dl = DataLocker.get_instance()
            for i, pos in enumerate(positions):
                if not isinstance(pos, dict):
                    pos = dict(pos)
                    positions[i] = pos
                asset_type = pos.get('asset_type')
                if asset_type:
                    latest_price_data = dl.get_latest_price(asset_type)
                    if latest_price_data and 'current_price' in latest_price_data:
                        try:
                            pos['current_price'] = float(latest_price_data['current_price'])
                        except (ValueError, TypeError) as conv_err:
                            logger.error(f"Error converting latest price for asset '{asset_type}': {conv_err}")
                            pos['current_price'] = pos.get('current_price')
                    else:
                        logger.warning(f"No latest price found for asset type: {asset_type}")
                else:
                    logger.warning("Position missing 'asset_type' field.")
            return positions
        except Exception as e:
            logger.error(f"Error in fill_positions_with_latest_price: {e}", exc_info=True)
            raise

    @staticmethod
    @staticmethod
    def update_jupiter_positions(db_path: str = DB_PATH) -> dict:
        """
        Fetches latest Jupiter positions, maps them, and inserts them into the database.
        Logs every step and confirms wallet linkage.
        """
        logger.info("🔄 Updating Jupiter positions from API...")
        try:
            dl = DataLocker.get_instance(db_path)
            wallets_list = dl.read_wallets()
            if not wallets_list:
                logger.warning("⚠️ No wallets found in DB.")
                return {"message": "No wallets in DB", "imported": 0, "skipped": 0}

            new_positions = []

            for wallet in wallets_list:
                public_addr = wallet.get("public_address", "").strip()
                wallet_name = wallet.get("name")
                if not public_addr:
                    logger.warning(f"⚠️ Skipping wallet {wallet_name} — missing public address.")
                    continue

                print(f"[🛰️] Checking Jupiter for {wallet_name} → {public_addr}")
                try:
                    url = f"https://perps-api.jup.ag/v1/positions?walletAddress={public_addr}&showTpslRequests=true"
                    resp = requests.get(url)
                    resp.raise_for_status()
                    data = resp.json()
                    data_list = data.get("dataList", [])
                    print(f"[🌐] Found {len(data_list)} positions for {wallet_name}")
                except Exception as e:
                    print(f"[ERROR] Failed to fetch Jupiter positions for {wallet_name}: {e}")
                    continue

                for item in data_list:
                    try:
                        pos_id = item.get("positionPubkey")
                        if not pos_id:
                            print(f"[SKIP] Missing positionPubkey in item: {item}")
                            continue

                        updated_dt = datetime.fromtimestamp(float(item.get("updatedTime", 0)))
                        mint = item.get("marketMint", "")
                        asset_type = PositionService.MINT_TO_ASSET.get(mint, "BTC")
                        side = item.get("side", "short").capitalize()

                        pos_dict = {
                            "id": pos_id,
                            "asset_type": asset_type,
                            "position_type": side,
                            "entry_price": float(item.get("entryPrice", 0.0)),
                            "liquidation_price": float(item.get("liquidationPrice", 0.0)),
                            "collateral": float(item.get("collateral", 0.0)),
                            "size": float(item.get("size", 0.0)),
                            "leverage": float(item.get("leverage", 0.0)),
                            "value": float(item.get("value", 0.0)),
                            "last_updated": updated_dt.isoformat(),
                            "wallet_name": wallet_name,
                            "pnl_after_fees_usd": float(item.get("pnlAfterFeesUsd", 0.0)),
                            "travel_percent": float(item.get("pnlChangePctAfterFees", 0.0))
                        }

                        print(f"[MAP] {wallet_name} → Position {pos_id} mapped.")
                        new_positions.append(pos_dict)
                    except Exception as map_err:
                        print(f"[ERROR] Failed to map Jupiter position for {wallet_name}: {map_err}")
                        print(item)
                        continue

            imported, skipped = 0, 0
            for pos in new_positions:
                cursor = dl.db.get_cursor()
                cursor.execute("SELECT COUNT(*) FROM positions WHERE id = ?", (pos["id"],))
                dup = cursor.fetchone()[0]
                cursor.close()

                if dup == 0:
                    dl.create_position(pos)
                    print(f"[✅] Imported Jupiter position {pos['id']} for wallet {pos['wallet_name']}")
                    imported += 1
                else:
                    print(f"[⏩] Skipped duplicate position {pos['id']}")
                    skipped += 1

            return {
                "message": "Jupiter sync complete.",
                "imported": imported,
                "skipped": skipped
            }

        except Exception as e:
            logger.exception("❌ Jupiter update failed")
            return {"error": str(e)}

    @staticmethod
    def delete_all_jupiter_positions(db_path: str = DB_PATH):
        try:
            dl = DataLocker.get_instance(db_path)
            cursor = dl.db.get_cursor()
            cursor.execute("DELETE FROM positions WHERE wallet_name IS NOT NULL")
            dl.db.commit()
            cursor.close()
            logger.info("All Jupiter positions deleted.")
        except Exception as e:
            logger.error(f"Error deleting Jupiter positions: {e}", exc_info=True)
            raise

    @staticmethod
    def update_dydx_positions(db_path: str = DB_PATH) -> dict:
        try:
            from uuid import uuid4
            client = DydxAPI()
            wallet_address = "dydx1unfl20nw9xep6vyl78jktjgrywvr5m7z7ru9e8"
            subaccount_number = 0

            dydx_positions = client.get_perpetual_positions(wallet_address, subaccount_number)
            dl = DataLocker.get_instance(db_path)
            new_count = 0

            for pos in dydx_positions:
                pos_dict = {
                    "id": pos.get("id", str(uuid4())),
                    "asset_type": pos.get("market", "BTC"),
                    "position_type": pos.get("side", ""),
                    "entry_price": float(pos.get("entryPrice", 0.0)),
                    "liquidation_price": 0.0,
                    "travel_percent": 0.0,
                    "value": float(pos.get("size", 0.0)) * float(pos.get("entryPrice", 0.0)),
                    "collateral": 0.0,
                    "size": float(pos.get("size", 0.0)),
                    "leverage": 0.0,
                    "wallet_name": wallet_address,
                    "last_updated": pos.get("createdAt", datetime.now().isoformat()),
                    "current_price": float(pos.get("entryPrice", 0.0)),
                    "liquidation_distance": None,
                    "heat_index": 0.0,
                    "current_heat_index": 0.0,
                    "pnl_after_fees_usd": float(pos.get("pnlAfterFeesUsd", 0.0)) if pos.get("pnlAfterFeesUsd") else 0.0,
                }
                cursor = dl.db.get_cursor()
                cursor.execute("SELECT COUNT(*) FROM positions WHERE id = ?", (pos_dict["id"],))
                dup_count = cursor.fetchone()[0]
                cursor.close()
                if dup_count == 0:
                    dl.create_position(pos_dict)
                    new_count += 1

            msg = f"Imported {new_count} new dYdX position(s)."
            logger.info(msg)
            return {"message": msg, "imported": new_count}
        except Exception as e:
            logger.error("Error updating dYdX positions: %s", e, exc_info=True)
            return {"error": str(e)}

    @staticmethod
    def record_positions_snapshot(db_path: str = DB_PATH):
        try:
            positions = PositionService.get_all_positions(db_path)
            calc_services = CalcServices()
            totals = calc_services.calculate_totals(positions)
            dl = DataLocker.get_instance(db_path)
            dl.record_positions_totals_snapshot(totals)
            logger.info("Positions snapshot recorded.")
        except Exception as e:
            logger.error(f"Error recording positions snapshot: {e}", exc_info=True)
            raise

    @staticmethod
    def find_hedges(db_path: str = DB_PATH) -> list:
        try:
            dl = DataLocker.get_instance(db_path)
            raw_positions = dl.read_positions()
            positions = [dict(pos) for pos in raw_positions]
            from sonic_labs.hedge_manager import HedgeManager
            hedge_manager = HedgeManager(positions)
            hedges = hedge_manager.get_hedges()
            u_logger.log_operation("Hedge Updated", f"Hedge update complete; {len(hedges)} hedges created.",
                                   source=source)

            return hedges
        except Exception as e:
            UnifiedLogger().log_operation(
                operation_type="Hedge Error",
                primary_text=f"Error finding hedges: {e}",
                source="System",
                file="position_service.py"
            )
            return []

    @staticmethod
    def clear_hedge_data(db_path: str = DB_PATH) -> None:
        try:
            dl = DataLocker.get_instance(db_path)
            cursor = dl.db.get_cursor()
            cursor.execute("UPDATE positions SET hedge_buddy_id = NULL WHERE hedge_buddy_id IS NOT NULL")
            dl.db.commit()
            cursor.close()
            UnifiedLogger().log_operation(
                operation_type="Clear Hedge Data",
                primary_text="Cleared hedge association data from positions.",
                source="System",
                file="position_service.py"
            )
        except Exception as e:
            UnifiedLogger().log_operation(
                operation_type="Clear Hedge Data Error",
                primary_text=f"Error clearing hedge data: {e}",
                source="System",
                file="position_service.py"
            )
