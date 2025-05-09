# cyclone/cyclone_hedge_service.py

#from sonic_labs.hedge_manager import HedgeManager
from positions.position_core import PositionCore
from data.data_locker import DataLocker
from core.core_imports import DB_PATH, log


class CycloneHedgeService:
    def __init__(self, data_locker):
        self.dl = data_locker
        self.data_locker = DataLocker(str(DB_PATH))


    async def update_hedges(self):
        log.info("🔄 Starting Hedge Update", source="CycloneHedge")
        try:
            hedge_groups = HedgeManager.find_hedges()
            log.info(f"Found {len(hedge_groups)} hedge group(s)", source="CycloneHedge")

            raw_positions = [dict(pos) for pos in self.dl.read_positions()]
            hedge_manager = HedgeManager(raw_positions)
            hedges = hedge_manager.get_hedges()

            log.success(
                f"✅ Built {len(hedges)} hedge(s) from {len(raw_positions)} positions",
                source="CycloneHedge"
            )
        except Exception as e:
            log.error(f"❌ Hedge update failed: {e}", source="CycloneHedge")

    async def link_hedges(self):
        log.info("🔗 Linking Hedges", source="CycloneHedge")
        try:
            hedge_groups = HedgeManager.find_hedges()
            count = len(hedge_groups)
            log.success(f"✅ Linked {count} hedge group(s)", source="CycloneHedge")
        except Exception as e:
            log.error(f"❌ Link Hedges failed: {e}", source="CycloneHedge")
