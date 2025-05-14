# test_xcom_components.py

import os
import sys

# Auto-inject root path if needed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.data_locker import DataLocker
from xcom.xcom_core import XComCore
from utils.console_logger import ConsoleLogger as log

DB_PATH = "sonic.sqlite"  # ⚠️ Update this if your DB lives elsewhere
PROFILE = "comms_seed_profile"

def run_test():
    log.banner("🧪 XComCore System Integration Test")

    # 1. Init DataLocker and activate comm profile
    dl = DataLocker(DB_PATH)
    dl.system.set_active_theme_profile(PROFILE)

    # 2. Init comm core
    xcom = XComCore(dl.system)

    # 3. Test payload
    subject = "🚀 Test Notification"
    body = (
        "Hello from XComCore!\n"
        "This is a live test of all communication channels.\n"
        "If you receive this — the system is working 🤖"
    )

    # 4. Dispatch tests
    log.route("📨 LOW Level Test → Email only")
    result_low = xcom.send_notification("LOW", subject, body)

    log.route("📨 MEDIUM Level Test → SMS only")
    result_med = xcom.send_notification("MEDIUM", subject, body)

    log.route("📨 HIGH Level Test → SMS + VOICE + SOUND")
    result_high = xcom.send_notification("HIGH", subject, body)

    # 5. Summary
    log.banner("✅ XComCore Dispatch Results")
    print("LOW   =", result_low)
    print("MEDIUM=", result_med)
    print("HIGH  =", result_high)

if __name__ == "__main__":
    run_test()
