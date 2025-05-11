# positions/position_core.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.core_imports import log
from positions.position_store import PositionStore
from positions.position_enrichment_service import PositionEnrichmentService
from positions.position_enrichment_service import PositionEnrichmentService

from positions.hedge_manager import HedgeManager
from utils.calc_services import CalcServices
from datetime import datetime

class PositionCore:
    def __init__(self, data_locker):
        self.dl = data_locker
        self.store = PositionStore(data_locker)
        self.enricher = PositionEnrichmentService(data_locker)

    def get_all_positions(self):
        raw = self.store.get_all()
        enriched = []

        for pos in raw:
            try:
                enriched.append(self.enricher.enrich(pos))
            except Exception as e:
                log.error(f"⚠️ Failed to enrich pos {pos.get('id')}: {e}", source="PositionCore")

        log.success(f"✅ Final enriched list: {len(enriched)}", source="PositionCore")
        return enriched

    def create_position(self, pos: dict):
        enriched = self.enricher.enrich(pos)
        return self.store.insert(enriched)

    def delete_position(self, pos_id: str):
        return self.store.delete(pos_id)

    def clear_all_positions(self):
        self.store.delete_all()

    def record_snapshot(self):
        try:
            raw = self.store.get_all()
            totals = CalcServices().calculate_totals(raw)
            self.dl.portfolio.record_snapshot(totals)  # ✅ HERE
            log.success("📸 Position snapshot recorded", source="PositionCore")
        except Exception as e:
            log.error(f"❌ Snapshot recording failed: {e}", source="PositionCore")

    def update_positions_from_jupiter(self, source="console"):
        """
        Legacy passthrough for console + engine.
        Uses PositionSyncService under the hood.
        """
        from positions.position_sync_service import PositionSyncService
        sync_service = PositionSyncService(self.dl)
        return sync_service.run_full_jupiter_sync(source=source)

    def link_hedges(self):
        """
        Runs hedge detection and returns a list of generated Hedge objects.
        """
        log.banner("🔗 Generating Hedges via PositionCore")

        try:
            positions = self.store.get_all()
            log.info("📥 Loaded positions for hedge scan", source="PositionCore", payload={"count": len(positions)})

            hedge_manager = HedgeManager(positions)
            hedges = hedge_manager.get_hedges()

            log.success("✅ Hedge generation complete", source="PositionCore", payload={"hedge_count": len(hedges)})
            return hedges

        except Exception as e:
            log.error(f"❌ Failed to generate hedges: {e}", source="PositionCore")
            return []


    async def enrich_positions(self):
        """
        Enriches all current positions and returns the list.
        """
        log.banner("🧠 Enriching All Positions via PositionCore")

        try:
            raw = self.store.get_all()
            enriched = []

            for pos in raw:
                try:
                    enriched.append(self.enricher.enrich(pos))
                except Exception as e:
                    log.error(f"⚠️ Failed to enrich position {pos.get('id')}: {e}", source="PositionCore")

            log.success("✅ Position enrichment complete", source="PositionCore", payload={"enriched": len(enriched)})
            return enriched

        except Exception as e:
            log.error(f"❌ enrich_positions() failed: {e}", source="PositionCore")
            return []
