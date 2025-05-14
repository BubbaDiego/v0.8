import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from datetime import datetime, timezone
import logging
import subprocess
import threading
import time

from base_monitor import BaseMonitor
from data.data_locker import DataLocker
from utils.console_logger import ConsoleLogger as log

DB_PATH = os.getenv("DB_PATH", "mother_brain.db")


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
        self.data_locker = DataLocker(DB_PATH)
        self.monitor_interval = monitor_interval
        self.continuous_mode = continuous_mode
        self.notifications_enabled = notifications_enabled
        self.logger = logging.getLogger("OperationsMonitor")

    def _do_work(self):
        """
        Perform a POST check and log to database ledger.
        """
        result = self.run_startup_post()
        self.data_locker.ledger.insert_ledger_entry(
            monitor_name=self.name,
            status="Success" if result.get("post_success") else "Failed",
            metadata=result
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
