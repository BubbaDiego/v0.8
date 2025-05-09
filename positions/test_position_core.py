# test_position_core.py

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from datetime import datetime
from uuid import uuid4

from data.data_locker import DataLocker
from core.constants import DB_PATH
from positions.position_core import PositionCore
from positions.position_sync_service import PositionSyncService
from utils.calc_services import CalcServices

from core.logging import log


def build_test_position(id=None):
    return {
        "id": id or str(uuid4()),
        "asset_type": "BTC",
        "position_type": "long",
        "entry_price": 42000.0,
        "current_price": 41000.0,
        "liquidation_price": 39000.0,
        "collateral": 1000.0,
        "size": 0.05,
        "leverage": 2.0,
        "value": 2000.0,
        "wallet_name": "TestWallet",
        "last_updated": datetime.now().isoformat(),
        "pnl_after_fees_usd": 50.0,
        "travel_percent": 5.0
    }


async def run_position_test():
    print("\n🚀 Running FULL PositionCore E2E Test")
    dl = DataLocker(str(DB_PATH))
    core = PositionCore(dl)
    sync = PositionSyncService(dl)

    # 🔁 Clear & inject test position
    print("\n🧹 Clearing existing positions...")
    core.clear_all_positions()

    print("\n📦 Inserting manual test position...")
    test_pos = build_test_position()
    core.create_position(test_pos)

    # 🧮 Capture pre-sync snapshot
    print("\n🧮 Capturing pre-sync portfolio totals...")
    pre_snapshot = dl.portfolio.get_latest_snapshot() or {}

    # 🔄 Sync from Jupiter
    print("\n🌐 Running Jupiter Sync...")
    result = sync.run_full_jupiter_sync(source="test_runner")
    if "error" in result:
        print(f"❌ Jupiter Sync Error: {result['error']}")
        return
    print(f"✅ Jupiter Sync Imported: {result['imported']} | Hedges: {result['hedges']}")

    # 📊 Fetch and show positions
    print("\n📊 Final enriched positions:")
    positions = core.get_all_positions()
    for p in positions[:5]:
        print(f"  - {p['id']} | {p['asset_type']} | {p['position_type']} | heat: {p.get('heat_index')}")

    # 💾 Verify snapshot was recorded
    print("\n🗃 Fetching latest snapshot...")
    post_snapshot = dl.portfolio.get_latest_snapshot() or {}
    if post_snapshot:
        print(f"📸 Snapshot @ {post_snapshot['snapshot_time']}: Total Value: {post_snapshot['total_value']}")
    else:
        print("⚠️ No snapshot found.")

    # 🔍 Compare snapshots
    def print_diff(pre, post, label):
        pre_val = pre.get(label, 0.0)
        post_val = post.get(label, 0.0)
        diff = round(post_val - pre_val, 4)
        print(f"  {label:<22}: {pre_val} → {post_val}  (Δ {diff})")

    print("\n🔍 Snapshot Diff Summary:")
    for field in [
        "total_size", "total_value", "total_collateral",
        "avg_leverage", "avg_travel_percent", "avg_heat_index"
    ]:
        print_diff(pre_snapshot, post_snapshot, field)

    print("\n✅ PositionCore E2E test complete.")



if __name__ == "__main__":
    asyncio.run(run_position_test())
