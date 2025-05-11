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

    def get_strategy_metadata(self):
        try:
            return self.theme.dl.system.get_last_update_times()
        except Exception as e:
            self.logger.error(f"Failed to get strategy metadata: {e}", source="SystemCore")
            return {}

