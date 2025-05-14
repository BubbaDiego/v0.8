# xcom/xcom_config_service.py
class XComConfigService:
    def __init__(self, dl_sys):
        self.dl_sys = dl_sys

    def get_provider(self, name: str) -> dict:
        config = self.dl_sys.get_active_theme_profile()
        return config.get("communication", {}).get("providers", {}).get(name, {})
