import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import requests
from datetime import datetime
from core.logging import log
from data.data_locker import DataLocker
from positions.position_enrichment_service import PositionEnrichmentService
from core.constants import DB_PATH
from utils.calc_services import CalcServices

#from positions.hedge


class PositionSyncService:
    def __init__(self, data_locker):
        self.dl = data_locker

    MINT_TO_ASSET = {
        "3NZ9JMVBmGAqocybic2c7LQCJScmgsAZ6vQqTDzcqmJh": "BTC",
        "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs": "ETH",
        "So11111111111111111111111111111111111111112": "SOL"
    }

    def run_full_jupiter_sync(self, source="user") -> dict:
        from positions.hedge_manager import HedgeManager  # if needed

        try:
            deleted = self.dl.positions.delete_all_positions()

            result = self.update_jupiter_positions()
            if "error" in result:
                return result

            log.success(f"✅ Jupiter positions imported: {result['imported']}", source="PositionSyncService")

            # Hedge generation (optional)
            positions = self.dl.positions.get_all_positions()
            hedge_manager = HedgeManager(positions)
            hedges = hedge_manager.get_hedges()
            log.success(f"🌐 HedgeManager created {len(hedges)} hedges", source="PositionSyncService")

            # Timestamp updates
            now = datetime.now()
            self.dl.system.set_last_update_times({
                "last_update_time_positions": now.isoformat(),
                "last_update_positions_source": source,
                "last_update_time_prices": now.isoformat(),
                "last_update_prices_source": source
            })

            self.dl.portfolio.record_snapshot(
                CalcServices().calculate_totals(positions)
            )

            return {
                "message": f"Sync complete: {result['imported']} positions, {len(hedges)} hedges",
                "imported": result["imported"],
                "hedges": len(hedges),
                "timestamp": now.isoformat()
            }

        except Exception as e:
            log.error(f"❌ run_full_jupiter_sync failed: {e}", source="PositionSyncService")
            return {"error": str(e)}

    def update_jupiter_positions(self):
        log.info("🔄 Updating positions from Jupiter...", source="PositionSyncService")
        try:
            log.info(f"📁 Writing to DB: {self.dl.db.db_path}", source="PositionSyncService")
            wallets = self.dl.wallets.get_wallets()
            log.debug(f"Found {len(wallets)} wallets", source="PositionSyncService")
            new_positions = []

            for wallet in wallets:
                pub = wallet.get("public_address", "").strip()
                name = wallet.get("name", "Unnamed")

                if not pub:
                    log.warning(f"Skipping {name} — missing address", source="PositionSyncService")
                    continue

                try:
                    url = f"https://perps-api.jup.ag/v1/positions?walletAddress={pub}&showTpslRequests=true"
                    res = requests.get(url)
                    res.raise_for_status()
                    data_list = res.json().get("dataList", [])

                    log.info(f"{name} → {len(data_list)} Jupiter positions", source="PositionSyncService")

                    for item in data_list:
                        pos_id = item.get("positionPubkey")
                        if not pos_id:
                            log.warning("Missing positionPubkey, skipping", source="PositionSyncService")
                            continue

                        raw_pos = {
                            "id": pos_id,
                            "asset_type": self.MINT_TO_ASSET.get(item.get("marketMint", ""), "BTC"),
                            "position_type": item.get("side", "short").capitalize(),
                            "entry_price": float(item.get("entryPrice", 0.0)),
                            "liquidation_price": float(item.get("liquidationPrice", 0.0)),
                            "collateral": float(item.get("collateral", 0.0)),
                            "size": float(item.get("size", 0.0)),
                            "leverage": float(item.get("leverage", 0.0)),
                            "value": float(item.get("value", 0.0)),
                            "last_updated": datetime.fromtimestamp(float(item.get("updatedTime", 0))).isoformat(),
                            "wallet_name": name,
                            "pnl_after_fees_usd": float(item.get("pnlAfterFeesUsd", 0.0)),
                            "travel_percent": float(item.get("pnlChangePctAfterFees", 0.0))
                        }

                        new_positions.append(raw_pos)
                except Exception as e:
                    log.error(f"{name} API error: {e}", source="PositionSyncService")

            imported = 0
            self.enricher = PositionEnrichmentService(self.dl)

            for pos in new_positions:
                cursor = self.dl.db.get_cursor()
                cursor.execute("SELECT COUNT(*) FROM positions WHERE id = ?", (pos["id"],))
                exists = cursor.fetchone()[0]
                cursor.close()

                if exists == 0:
                    enriched = self.enricher.enrich(pos)

                    for key in ["alert_reference_id", "hedge_buddy_id"]:
                        enriched.setdefault(key, None)

                    try:
                        self.dl.positions.create_position(enriched)
                        log.success(f"✅ Inserted: {enriched['id']}", source="InsertVerify")
                        imported += 1
                    except Exception as e:
                        log.error(f"❌ Insert failed for {enriched['id']}: {e}", source="InsertVerify")

            return {
                "message": "Jupiter sync complete",
                "imported": imported,
                "skipped": len(new_positions) - imported
            }

        except Exception as e:
            log.error(f"❌ Sync failed: {e}", source="PositionSyncService")
            return {"error": str(e)}
