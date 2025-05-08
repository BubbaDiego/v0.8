"""
hedge_manager.py

This module defines the HedgeManager class which is responsible for:
  - Scanning positions for hedge links (via hedge_buddy_id).
  - Creating Hedge instances that represent grouped positions.
  - Aggregating metrics such as total long size, total short size, long/short heat indices,
    and total heat index.
  - Providing access to hedge data via methods like get_hedges().
  - Logging operations using ConsoleLogger.
"""

from typing import List, Optional
from datetime import datetime
from uuid import uuid4
from data.models import Position, Hedge
from core.constants import DB_PATH
from data.data_locker import DataLocker
from utils.console_logger import ConsoleLogger as log


class HedgeManager:
    def __init__(self, positions: Optional[List[Position]] = None):
        self.positions: List[Position] = positions if positions is not None else []
        self.hedges: List[Hedge] = []
        self.build_hedges()

    def build_hedges(self):
        hedge_groups = {}
        for pos in self.positions:
            hedge_buddy_id = pos.get("hedge_buddy_id")
            if hedge_buddy_id:
                hedge_groups.setdefault(hedge_buddy_id, []).append(pos)

        self.hedges = []
        for key, pos_group in hedge_groups.items():
            if len(pos_group) >= 2:
                hedge = Hedge(id=str(uuid4()))
                hedge.positions = [p.get("id") for p in pos_group]

                total_long = total_short = long_heat = short_heat = 0.0

                for p in pos_group:
                    position_type = str(p.get("position_type", "")).lower()
                    size = float(p.get("size", 0))
                    heat_index = float(p.get("heat_index") or 0.0)

                    if position_type == "long":
                        total_long += size
                        long_heat += heat_index
                    elif position_type == "short":
                        total_short += size
                        short_heat += heat_index

                hedge.total_long_size = total_long
                hedge.total_short_size = total_short
                hedge.long_heat_index = long_heat
                hedge.short_heat_index = short_heat
                hedge.total_heat_index = long_heat + short_heat
                hedge.created_at = datetime.now()
                hedge.updated_at = datetime.now()
                hedge.notes = f"Hedge created from positions with hedge_buddy_id: {key}"

                self.hedges.append(hedge)

        log.success(
            f"Hedge check complete: {len(self.hedges)} hedges found.",
            source="HedgeManager",
            payload={
                "hedge_count": len(self.hedges),
                "file": "hedge_manager.py",
                "operation_type": "Hedge Check"
            }
        )

    def update_positions(self, positions: List[Position]):
        self.positions = positions
        self.build_hedges()

    def get_hedges(self) -> List[Hedge]:
        return self.hedges

    @staticmethod
    def find_hedges(db_path: str = DB_PATH) -> List[list]:
        log.debug("🔍 Entering find_hedges()", source="HedgeManager")
        try:
           #1 dl = DataLocker.get_instance(DB_PATH)
            dl = DataLocker(str(DB_PATH))
            raw_positions = dl.read_positions()
            log.debug(f"Retrieved {len(raw_positions)} raw positions", source="HedgeManager")

            positions = [dict(pos) for pos in raw_positions]
            log.debug(f"Converted positions to dicts", source="HedgeManager")

            groups = {}
            for pos in positions:
                wallet = pos.get("wallet_name")
                asset = pos.get("asset_type")
                if wallet and asset:
                    key = (wallet.strip(), asset.strip())
                    groups.setdefault(key, []).append(pos)
                    log.debug(f"→ Added position {pos['id']} to group {key}", source="HedgeManager")

            log.debug(f"Formed {len(groups)} candidate groups", source="HedgeManager")

            hedged_groups = []
            for key, pos_list in groups.items():
                types = [pos.get("position_type", "").strip().lower() for pos in pos_list]
                has_long = "long" in types
                has_short = "short" in types

                if has_long and has_short:
                    hedge_id = str(uuid4())
                    log.info(f"✅ Group {key} qualifies — hedge_id={hedge_id}", source="HedgeManager")

                    for pos in pos_list:
                        pos["hedge_buddy_id"] = hedge_id
                        cursor = dl.db.get_cursor()
                        cursor.execute("UPDATE positions SET hedge_buddy_id = ? WHERE id = ?", (hedge_id, pos["id"]))
                        dl.db.commit()
                        cursor.close()

                        log.debug(f"Updated position {pos['id']} with hedge_buddy_id", source="HedgeManager")

                    hedged_groups.append(pos_list)
                else:
                    log.debug(f"🚫 Group {key} skipped: needs long + short", source="HedgeManager")

            log.success(f"✅ Found {len(hedged_groups)} hedge group(s)", source="HedgeManager")
            return hedged_groups

        except Exception as e:
            log.error(f"❌ Error in find_hedges: {e}", source="HedgeManager")
            return []

    @staticmethod
    def clear_hedge_data(db_path: str = DB_PATH) -> None:
        try:
            dl = DataLocker.get_instance(db_path)
            cursor = dl.db.get_cursor()
            cursor.execute("UPDATE positions SET hedge_buddy_id = NULL WHERE hedge_buddy_id IS NOT NULL")
            dl.db.commit()
            cursor.close()
            log.success("🧹 Cleared hedge association data", source="HedgeManager")
        except Exception as e:
            log.error(f"❌ Error clearing hedge data: {e}", source="HedgeManager")
