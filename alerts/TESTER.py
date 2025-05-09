import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data.data_locker import DataLocker
from core.logging import log

DB_PATH = "test_alerts.db"  # 💾 update if needed
BACKUP_FILE = "wallet_backup.json"

def run_wallet_restore_test():
    log.banner("🔐 Wallet Reinjection Test")

    # ✅ Init DataLocker
    dl = DataLocker(DB_PATH)

    # ✅ Load wallet data
    if not os.path.exists(BACKUP_FILE):
        log.error(f"Backup file not found: {BACKUP_FILE}", source="WalletRestore")
        return

    with open(BACKUP_FILE, "r") as f:
        wallets = json.load(f)

    restored = 0
    for w in wallets:
        try:
            # Map fields defensively
            wallet_data = {
                "id": w.get("id"),
                "name": w.get("name"),
                "address": w.get("address"),
                "public_address": w.get("public_address", w.get("address")),
                "network": w.get("network"),
                "label": w.get("label"),
                "type": w.get("type")
            }
            dl.wallets.create_wallet(wallet_data)
            restored += 1
        except Exception as e:
            log.error(f"❌ Failed to insert wallet {w.get('id')}: {e}", source="WalletRestore")

    log.success("✅ Wallet Reinjection Complete", payload={"count": restored})
    print("\n🧪 Test complete.\n")

if __name__ == "__main__":
    run_wallet_restore_test()
