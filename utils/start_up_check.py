from core.constants import (
    DB_PATH,
    CONFIG_PATH,
    ALERT_LIMITS_PATH,
    BASE_DIR,
)
# from utils.path_audit import maybe_create_mother_brain
import os
from pathlib import Path
import sqlite3

from utils.config_loader import save_config
from core.core_imports import log


def maybe_create_mother_brain(db_path: str) -> None:
    """Ensure the SQLite database file exists."""
    if not os.path.exists(db_path):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.close()
        log.info(f"📄 Created database: {db_path}", source="StartUpCheck")

class StartUpCheck:

    @staticmethod
    def run_all():
        log.banner("🧠 STARTUP CHECK")
        StartUpCheck.check_for_mother_brain()
        StartUpCheck.verify_required_paths()
        StartUpCheck.ensure_alert_limits()
        StartUpCheck.ensure_required_directories()
        log.success("✅ All startup checks passed.\n", source="StartUpCheck")

    @staticmethod
    def check_for_mother_brain():
        maybe_create_mother_brain(DB_PATH)

    @staticmethod
    def verify_required_paths():
        missing = []
        for path in [DB_PATH, CONFIG_PATH, ALERT_LIMITS_PATH]:
            if not os.path.exists(path):
                missing.append(path)

        if missing:
            log.critical("❌ Missing required file paths:")
            for p in missing:
                log.error(f"  - {p}", source="StartUpCheck")
            raise SystemExit("Startup check failed due to missing critical files.")
        else:
            log.info("✅ All required file paths present.", source="StartUpCheck")

    @staticmethod
    def ensure_alert_limits():
        if not os.path.exists(ALERT_LIMITS_PATH):
            log.warning("⚠️ alert_limitsz.json not found. Creating default template...")
            default = {
                "alert_ranges": {},
                "global_alert_config": {
                    "enabled": True,
                    "data_fields": {},
                    "thresholds": {}
                }
            }
            save_config("alert_limitsz.json", default)
            log.success("✅ Default alert_limitsz.json created.", source="StartUpCheck")
        else:
            log.info("✅ alert_limitsz.json found.", source="StartUpCheck")

    @staticmethod
    def ensure_required_directories():
        required_dirs = [os.path.join(BASE_DIR, "logs"), os.path.join(BASE_DIR, "data")]
        for d in required_dirs:
            Path(d).mkdir(parents=True, exist_ok=True)
            log.info(f"📁 Ensured directory exists: {d}", source="StartUpCheck")

# --- Allow Standalone Run ---
if __name__ == "__main__":
    StartUpCheck.run_all()
