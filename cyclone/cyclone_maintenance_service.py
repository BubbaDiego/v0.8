# cyclone/services/system_maintenance_service.py

from core.logging import log

class SystemMaintenanceService:
    def __init__(self, data_locker):
        self.dl = data_locker

    def clear_prices(self):
        try:
            cursor = self.dl.db.get_cursor()
            cursor.execute("DELETE FROM prices")
            self.dl.db.commit()
            deleted = cursor.rowcount
            cursor.close()
            log.success(f"🧹 Prices cleared: {deleted} record(s)", source="SystemMaintenance")
        except Exception as e:
            log.error(f"❌ Failed to clear prices: {e}", source="SystemMaintenance")

def clear_positions(self):
    try:
        cursor = self.dl.db.get_cursor()
        cursor.execute("DELETE FROM positions")
        self.dl.db.commit()
        deleted = cursor.rowcount
        cursor.close()
        log.success(f"🧹 Positions cleared: {deleted} record(s)", source="SystemMaintenance")
    except Exception as e:
        log.error(f"❌ Failed to clear positions: {e}", source="SystemMaintenance")

def clear_wallets(self):
    try:
        cursor = self.dl.db.get_cursor()
        cursor.execute("DELETE FROM wallets")
        self.dl.db.commit()
        deleted = cursor.rowcount
        cursor.close()
        log.success(f"🧹 Wallets cleared: {deleted} record(s)", source="SystemMaintenance")
    except Exception as e:
        log.error(f"❌ Failed to clear wallets: {e}", source="SystemMaintenance")

def clear_alerts(self):
    try:
        self.dl.alerts.clear_all_alerts()
        log.success("🧹 Alerts cleared", source="SystemMaintenance")
    except Exception as e:
        log.error(f"❌ Failed to clear alerts: {e}", source="SystemMaintenance")

def clear_all_tables(self):
    tables = ["alerts", "prices", "positions"]
    for table in tables:
        try:
            cursor = self.dl.db.get_cursor()
            cursor.execute(f"DELETE FROM {table}")
            self.dl.db.commit()
            cursor.close()
            log.success(f"✅ Cleared all rows from `{table}`", source="SystemMaintenance")
        except Exception as e:
            log.error(f"❌ Failed to clear `{table}`: {e}", source="SystemMaintenance")
