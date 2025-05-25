import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from datetime import datetime, timezone
import logging
import subprocess

from monitor.base_monitor import BaseMonitor
from data.data_locker import DataLocker
from core.logging import log
from core.constants import DB_PATH, ALERT_LIMITS_PATH
from config.config_loader import load_config
from utils.schema_validation_service import SchemaValidationService


class OperationsMonitor(BaseMonitor):
    """
    OperationsMonitor handles system POST tests, health monitoring, and optional alerting.
    """
    def __init__(self, timer_config_path=None, ledger_filename=None, monitor_interval=300, continuous_mode=False, notifications_enabled=False):
        super().__init__(
            name="operations_monitor",
            timer_config_path=timer_config_path,
            ledger_filename=ledger_filename or "operations_ledger.json"
        )
        self.data_locker = DataLocker(str(DB_PATH))
        self.monitor_interval = monitor_interval
        self.continuous_mode = continuous_mode
        self.notifications_enabled = notifications_enabled
        self.logger = logging.getLogger("OperationsMonitor")

    def _do_work(self):
        """
        Perform a POST check and log to database ledger.
        """
        config_result = self.run_startup_configuration_test()
        post_result = self.run_startup_post()

        result = {
            "config_success": config_result.get("config_success"),
            "config_duration_seconds": config_result.get("duration_seconds"),
            "post_success": post_result.get("post_success"),
            "post_duration_seconds": post_result.get("duration_seconds"),
        }

        overall_success = result["config_success"] and result["post_success"]
        self.data_locker.ledger.insert_ledger_entry(
            monitor_name=self.name,
            status="Success" if overall_success else "Failed",
            metadata=result,
        )
        return result

    def run_startup_post(self) -> dict:
        """
        Run critical POST (Power-On Self Tests) during system startup.
        """
        log.banner("🧪 Running startup POST tests...")
        test_path = os.path.join(os.getcwd(), "tests", "test_alert_controller.py")

        if not os.path.exists(test_path):
            log.warning("Skipping POST: test file not found.", source=self.name)
            return {"post_success": True, "skipped": True}

        start_time = datetime.now()
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        success = (result.returncode == 0)
        duration = (datetime.now() - start_time).total_seconds()

        if not success:
            log.error("Startup POST tests failed!", source=self.name)
            log.error(result.stdout.decode(), source=self.name)
            log.error(result.stderr.decode(), source=self.name)
        else:
            log.success("Startup POST tests passed.", source=self.name)

        return {"post_success": success, "duration_seconds": duration}

    def run_startup_configuration_test(self) -> dict:
        """Validate alert_limits configuration on startup."""
        log.banner("🧪 Running startup configuration test...")
        start_time = datetime.now()

        config_path = str(ALERT_LIMITS_PATH)
        file_exists = os.path.exists(config_path)
        config_data = load_config(config_path)

        success = False

        if not file_exists:
            log.error(
                f"Config not found at {config_path}", source=self.name
            )
        elif not config_data:
            log.error(
                f"Config data empty at {config_path}", source=self.name
            )
        else:
            success = SchemaValidationService.validate_alert_ranges()
            if success:
                log.success(
                    "Alert limits configuration valid.", source=self.name
                )
            else:
                log.error(
                    "Alert limits configuration invalid.", source=self.name
                )

        duration = (datetime.now() - start_time).total_seconds()
        return {"config_success": success, "duration_seconds": duration}

if __name__ == "__main__":
    from core.core_imports import configure_console_log
    log.banner("🚀 SELF-RUN: OperationsMonitor")
    configure_console_log()

    monitor = OperationsMonitor()
    result = monitor._do_work()

    log.success("🧾 OperationsMonitor Run Complete", source="SelfTest", payload=result)
    log.banner("✅ Operations POST Finished")
