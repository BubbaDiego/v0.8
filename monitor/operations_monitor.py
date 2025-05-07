# operations_monitor.py
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from datetime import datetime, timezone

from monitor.monitor_utils import LedgerWriter  # 🔁 import here or at top
import subprocess
import threading
import time
#import timezone
import logging
from datetime import datetime
from monitor.monitor_utils import BaseMonitor
#from utils.unified_logger import UnifiedLogger

# Optional Notification Imports
from xcom.xcom import send_email, send_sms, load_com_config

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
        self.monitor_interval = monitor_interval
        self.continuous_mode = continuous_mode
        self.notifications_enabled = notifications_enabled
        self.logger = logging.getLogger("OperationsMonitor")
#        self.unified_logger = UnifiedLogger()

    def run_startup_post(self) -> dict:
        """
        Run critical POST (Power-On Self Tests) during system startup.
        """
        print("[🧪] Running startup POST tests...")
        test_path = os.path.join(os.getcwd(), "tests", "test_alert_controller.py")
        if not os.path.exists(test_path):
            print("[⚠️] Skipping POST: test file not found.")
            return {"post_success": True, "skipped": True}

        start_time = datetime.now()
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_alert_controller.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        success = (result.returncode == 0)
        duration = (datetime.now() - start_time).total_seconds()

        if not success:
            print("[❌] Startup POST tests failed!")
            self.logger.error(result.stdout.decode())
            self.logger.error(result.stderr.decode())
            if self.notifications_enabled:
                self.send_alert_notification("Startup POST failure detected!")
            sys.exit(1)
        else:
            print("[✅] Startup POST tests passed.")

        return {"post_success": success, "duration_seconds": duration}

    def run_continuous_health_check(self) -> dict:
        """
        Run health checks at runtime (continuous mode or on demand).
        """
        print("[🔄] Running health check...")
        return {"health_success": True, "duration_seconds": 0}

        # 🔥 THIS IS A STUB BITCH

    def start_background_monitor(self):
        """Start a background thread that runs continuous health checks."""
        if self.continuous_mode:
            print(f"[🛡️] Background monitoring enabled. Interval: {self.monitor_interval}s")
            threading.Thread(target=self._background_loop, daemon=True).start()

    def _background_loop(self):
        while True:
            metadata = self.run_continuous_health_check()
            self.heartbeat(metadata)

            xcom_result = self.check_for_xcom()
            self.log_xcom_status(xcom_result)  # ✅ go to correct file
            metadata["xcom"] = xcom_result  # 📝 still attached to operations heartbeat

            time.sleep(self.monitor_interval)

    def run_health_check(self, test_file="tests/test_alert_controller.py"):
        """Run health check against a specified test file."""
        print(f"[🔄] Running health check: {test_file}")

        os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

        start_time = datetime.now()
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        success = (result.returncode == 0)
        duration = (datetime.now() - start_time).total_seconds()

        if not success:
            self.logger.error("[❌] Health check failed.")
            self.logger.error(result.stdout.decode())
            self.logger.error(result.stderr.decode())
            if self.notifications_enabled:
                self.send_alert_notification(f"Health check FAILED on {test_file}")
        else:
            print("[✅] Health check passed.")

        return {"health_success": success, "duration_seconds": duration}

    def heartbeat(self, metadata: dict = None):
        """
        Log a simple heartbeat with optional metadata.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        entry = {
            "timestamp": timestamp,
            "component": self.name,
            "operation": "heartbeat",
            "status": "OK",
            "metadata": metadata or {}
        }
        self.ledger_writer.write(self.ledger_file, entry)
        self.logger.info(f"[❤️] Heartbeat at {timestamp} with metadata {metadata}")

    def check_for_xcom(self) -> dict:
        """
        Stubbed Xcom check — always returns positive for now.
        """
        return {
            "check_name": "xcom_heartbeat",
            "status": "success",
            "message": "Stubbed Xcom communication OK",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def log_xcom_status(self, result: dict):
        """
        Write Xcom check result to its own dedicated ledger file.
        """
        xcom_ledger_filename = "xcom_ledger.json"
        writer = LedgerWriter()
        writer.write(xcom_ledger_filename, {
            "timestamp": result["timestamp"],
            "component": "xcom_monitor",
            "operation": result["check_name"],
            "status": result["status"],
            "message": result["message"]
        })

        self.logger.info(f"[📡] Xcom log written: {result['status']}")

    def send_alert_notification(self, message: str):
        """
        Send Twilio/Email/SMS alert notification for failures.
        """
        try:
            config = load_com_config()
            twilio_cfg = config.get("twilio_config", {})
            notify_cfg = config.get("notification_config", {})

            trigger_twilio_flow(message, twilio_cfg)
            self.unified_logger.log_operation("NotificationSent", "Twilio sent.", source="OperationsMonitor")

            # Fallback to Email/SMS if needed
            send_email(
                recipient_email=notify_cfg.get("email", {}).get("recipient_email"),
                subject="Operations Monitor Alert",
                body=message,
                config=config
            )
            send_sms(
                phone_number=notify_cfg.get("sms", {}).get("recipient_number"),
                message=message,
                config=config
            )
            self.unified_logger.log_operation("FallbackSent", "Email/SMS fallback triggered.", source="OperationsMonitor")
        except Exception as e:
            self.logger.error(f"Notification failure: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    monitor = OperationsMonitor(
        monitor_interval=300,
        continuous_mode=True,
        notifications_enabled=True
    )
    monitor.run_startup_post()
    monitor.start_background_monitor()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Operations Monitor stopped by user.")
