# 🧠 SystemCore — centralized access to system-level services

from system.wallet_service import WalletService
from system.theme_service import ThemeService
from core.logging import log



class SystemCore:
    def __init__(self, data_locker):
        self.log = log

        # 🔌 Inject services
        self.wallets = WalletService(data_locker)
        self.theme = ThemeService(data_locker)

        self.log.success("SystemCore initialized with Wallet + Theme services.")

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

    # 🌗 Get current theme mode
    def get_theme_mode(self) -> str:
        return self.theme.get_theme_mode()

    # 🌗 Set theme mode
    def set_theme_mode(self, mode: str):
        self.theme.set_theme_mode(mode)

    # 🎨 Load saved theme config
    def load_theme_config(self) -> dict:
        return self.theme.load_theme_config()

    # 🎨 Save theme config
    def save_theme_config(self, config: dict):
        self.theme.save_theme_config(config)

    def get_strategy_metadata(self):
        try:
            return self.theme.dl.system.get_last_update_times()
        except Exception as e:
            self.logger.error(f"Failed to get strategy metadata: {e}", source="SystemCore")
            return {}

