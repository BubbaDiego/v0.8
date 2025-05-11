
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
from core.logging import log
from core.constants import THEME_CONFIG_PATH

class ThemeService:
    def __init__(self, data_locker, config_path=THEME_CONFIG_PATH):
        self.dl = data_locker
        self.config_path = config_path
        self.logger = log

    def get_theme_mode(self) -> str:
        try:
            return self.dl.system.get_theme_mode()
        except Exception as e:
            self.logger.warn(f"Failed to get theme mode: {e}", source="ThemeService")
            return "light"

    def set_theme_mode(self, mode: str):
        try:
            current_mode = self.get_theme_mode()
            if current_mode == mode:
                self.logger.debug(f"Theme mode already '{mode}', skipping update.", source="ThemeService")
                return  # No-op
            self.dl.system.set_theme_mode(mode)
            self.logger.info(f"Theme mode set to {mode}", source="ThemeService")
        except Exception as e:
            self.logger.error(f"Failed to set theme mode: {e}", source="ThemeService")
            raise

    def load_theme_config(self) -> dict:
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Error loading theme config: {e}")
            return {}

    def save_theme_config(self, config: dict):
        try:
            with open(self.config_path, "w") as f:
                json.dump(config, f, indent=2)
            self.logger.success("Theme config saved.")
        except Exception as e:
            self.logger.error(f"Failed to save theme config: {e}")
            raise
