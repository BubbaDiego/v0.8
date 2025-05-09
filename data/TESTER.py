import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cyclone.cyclone_position_service import CyclonePositionService
from data.data_locker import DataLocker
from core.constants import DB_PATH

def test_jupiter_position_fetch():
    dl = DataLocker(str(DB_PATH))
    cps = CyclonePositionService(dl)

    print("🚀 Fetching & importing positions from Jupiter...")
    cps.update_positions_from_jupiter()

    print("\n🔍 Verifying stored positions...")
    all_positions = dl.read_positions()  # <- FIXED HERE
    for p in all_positions:
        print(f"📌 {p['wallet_name']} | {p['asset_type']} | {p['position_type']} | Size: {p['size']}")

if __name__ == "__main__":
    test_jupiter_position_fetch()
