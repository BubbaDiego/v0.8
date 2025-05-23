import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from positions.hedge_manager import HedgeManager
from core.core_imports import log

class HedgeCore:
    """High level orchestration for hedge operations"""
    def __init__(self, data_locker):
        self.dl = data_locker

    def link_hedges(self):
        """Scan the DB and set hedge_buddy_id for qualifying groups"""
        log.info("🔗 Linking hedges", source="HedgeCore")
        try:
            groups = HedgeManager.find_hedges()
            log.success(f"✅ Linked {len(groups)} hedge group(s)", source="HedgeCore")
            return groups
        except Exception as e:
            log.error(f"❌ Link hedges failed: {e}", source="HedgeCore")
            return []

    def update_hedges(self):
        """Build Hedge objects from current positions"""
        log.info("🔄 Updating hedges", source="HedgeCore")
        try:
            # Ensure hedge_buddy_id values are up-to-date
            HedgeManager.find_hedges()
            raw_positions = [dict(p) for p in self.dl.read_positions()]
            hedge_manager = HedgeManager(raw_positions)
            hedges = hedge_manager.get_hedges()
            log.success(
                f"✅ Built {len(hedges)} hedge(s) from {len(raw_positions)} positions",
                source="HedgeCore"
            )
            return hedges
        except Exception as e:
            log.error(f"❌ Hedge update failed: {e}", source="HedgeCore")
            return []
