from core.core_imports import log
# dl_wallets.py
"""
Author: BubbaDiego
Module: DLWalletManager
Description:
    Manages crypto wallet storage in the database. Supports create, read,
    update, and delete operations for wallet records.

Dependencies:
    - DatabaseManager from database.py
    - ConsoleLogger from console_logger.py
"""


from wallets.encryption import encrypt_key, decrypt_key


class DLWalletManager:
    def __init__(self, db):
        self.db = db
        log.info("DLWalletManager initialized.", source="DLWalletManager")

    def create_wallet(self, wallet: dict):
        try:
            cursor = self.db.get_cursor()
            cursor.execute(
                """
                INSERT INTO wallets (
                    name, public_address, private_address, image_path, balance
                ) VALUES (?, ?, ?, ?, ?)
            """,
                (
                    wallet["name"],
                    wallet["public_address"],
                    encrypt_key(wallet.get("private_address")),
                    wallet.get("image_path", ""),
                    wallet.get("balance", 0.0),
                ),
            )
            self.db.commit()  # ✅ not self.db.db
            log.success(f"Wallet created: {wallet['name']}", source="DLWalletManager")
        except Exception as e:
            log.error(f"Failed to create wallet: {e}", source="DLWalletManager")

    def get_wallets(self) -> list:
        try:
            cursor = self.db.get_cursor()
            cursor.execute("SELECT * FROM wallets")
            wallets = [dict(row) for row in cursor.fetchall()]
            for w in wallets:
                w["private_address"] = decrypt_key(w.get("private_address"))
            log.debug(f"Retrieved {len(wallets)} wallets", source="DLWalletManager")
            return wallets
        except Exception as e:
            log.error(f"Failed to fetch wallets: {e}", source="DLWalletManager")
            return []

    def update_wallet(self, name: str, wallet: dict):
        try:
            cursor = self.db.get_cursor()
            cursor.execute("""
                UPDATE wallets SET
                    public_address = ?,
                    private_address = ?,
                    image_path = ?,
                    balance = ?
                WHERE name = ?
            """, (
                wallet["public_address"],
                encrypt_key(wallet.get("private_address")),
                wallet.get("image_path", ""),
                wallet.get("balance", 0.0),
                name
            ))
            self.db.commit()
            log.info(f"Wallet updated: {name}", source="DLWalletManager")
        except Exception as e:
            log.error(f"Failed to update wallet {name}: {e}", source="DLWalletManager")



    def get_wallet_by_name(self, name: str) -> dict:
        try:
            cursor = self.db.get_cursor()
            cursor.execute("SELECT * FROM wallets WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                data = dict(row)
                data["private_address"] = decrypt_key(data.get("private_address"))
                return data
            return None
        except Exception as e:
            from core.logging import log
            log.error(f"DLWalletManager failed to get wallet '{name}': {e}", source="DLWalletManager")
            return None

    def delete_wallet(self, name: str):
        try:
            cursor = self.db.get_cursor()
            cursor.execute("DELETE FROM wallets WHERE name = ?", (name,))
            self.db.commit()
            log.info(f"Wallet deleted: {name}", source="DLWalletManager")
        except Exception as e:
            log.error(f"Failed to delete wallet {name}: {e}", source="DLWalletManager")
