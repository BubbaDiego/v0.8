# 🧠 SystemCore — updated for theme profile support

from alerts.threshold_service import ThresholdService
from system.wallet_service import WalletService
from system.theme_service import ThemeService
from core.logging import log

class SystemCore:
    def __init__(self, data_locker):
        self.log = log
        self.wallets = WalletService(data_locker)
        self.theme = ThemeService(data_locker)
        self.log.success("SystemCore initialized with Wallet + Theme services.")

    # --- Summary + Meta ---
    def get_system_summary(self):
        try:
            summary = {
                "wallet_count": len(self.wallets.list_wallets()),
                "theme_mode": self.theme.get_theme_mode()
            }
            self.log.debug(f"System summary: {summary}")
            return summary
        except Exception as e:
            self.log.error(f"Error generating system summary: {e}")
            return {}

    def get_portfolio_thresholds(self):
        svc = ThresholdService(self.theme.dl.db)
        return {
            "avg_leverage": svc.get_thresholds("AvgLeverage", "Portfolio", "ABOVE"),
            "total_value": svc.get_thresholds("TotalValue", "Portfolio", "ABOVE"),
            "total_size": svc.get_thresholds("TotalSize", "Portfolio", "ABOVE"),
            # etc...
        }

    def get_strategy_metadata(self):
        try:
            return self.theme.dl.system.get_last_update_times()
        except Exception as e:
            self.log.error(f"Failed to get strategy metadata: {e}", source="SystemCore")
            return {}

    # --- Theme Mode ---
    def get_theme_mode(self):
        return self.theme.get_theme_mode()

    def set_theme_mode(self, mode: str):
        self.theme.set_theme_mode(mode)

    # --- Theme Config (legacy JSON) ---
    def load_theme_config(self):
        return self.theme.load_theme_config()

    def save_theme_config(self, config: dict):
        self.theme.save_theme_config(config)

    # === 🚀 New: Theme Profile APIs ===

    def get_all_profiles(self) -> dict:
        return self.theme.get_all_profiles()

    def save_profile(self, name: str, config: dict):
        self.theme.save_profile(name, config)

    def delete_profile(self, name: str):
        self.theme.delete_profile(name)

    def set_active_profile(self, name: str):
        self.theme.set_active_profile(name)

    def get_active_profile(self) -> dict:
        return self.theme.get_active_profile()
