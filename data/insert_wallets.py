
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from core.core_imports import DB_PATH
from data.data_locker import DataLocker

dl = DataLocker(str(DB_PATH))

wallets_to_add = [
    {
        "name": "R2Vault",
        "public_address": "FhNRk...VALID1",
        "private_address": "privatekey1",
        "image_path": "",
        "balance": 1000.0
    },
    {
        "name": "LandoVault",
        "public_address": "DjsRU...VALID2",
        "private_address": "privatekey2",
        "image_path": "",
        "balance": 2500.0
    }
]

for w in wallets_to_add:
    try:
        dl.wallets.create_wallet(w)  # ✅ Use the wallets manager
    except Exception as e:
        print(f"❌ Failed to insert {w['name']}: {e}")
