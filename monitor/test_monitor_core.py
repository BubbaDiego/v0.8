import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.core_imports import DB_PATH
import json
import traceback
from datetime import datetime, timezone
from flask.testing import FlaskClient

from monitor_core import MonitorCore
from monitor_registry import MonitorRegistry
from base_monitor import BaseMonitor
from monitor_api import app as monitor_api
from price_monitor import PriceMonitor
from utils.console_logger import ConsoleLogger as log
from data.data_locker import DataLocker

# ✅ DB PATH
DB_PATH = os.getenv("DB_PATH", "mother_brain.db")
locker = DataLocker(DB_PATH)

# === 🧪 SETUP ===

test_results = []

def report(name, passed, detail=""):
    status = "✅" if passed else "❌"
    log.success(f"{status} {name}" if passed else f"{status} {name} FAILED", source="Test", payload={"detail": detail} if detail else None)
    test_results.append((name, passed, detail))


# === 🧪 CORE / REGISTRY TESTS ===

class DummySuccessMonitor(BaseMonitor):
    def __init__(self):
        super().__init__("dummy_success")

    def _do_work(self):
        locker.ledger.insert_ledger_entry("dummy_success", "Success", {"x": 1})
        return {"test": "ok"}

class DummyFailMonitor(BaseMonitor):
    def __init__(self):
        super().__init__("dummy_fail")

    def _do_work(self):
        raise RuntimeError("intentional test failure")

def test_registry_lookup():
    reg = MonitorRegistry()
    reg.register("pass", DummySuccessMonitor())
    reg.register("fail", DummyFailMonitor())
    try:
        assert isinstance(reg.get("pass"), DummySuccessMonitor)
        assert reg.get("fail").name == "dummy_fail"
        report("Registry Lookup", True)
    except Exception as e:
        report("Registry Lookup", False, str(e))

def test_core_monitor_run_success():
    reg = MonitorRegistry()
    reg.register("pass", DummySuccessMonitor())
    core = MonitorCore(reg)
    try:
        core.run_by_name("pass")
        report("Core Run Success Monitor", True)
    except Exception as e:
        report("Core Run Success Monitor", False, str(e))

def test_core_monitor_run_failure():
    reg = MonitorRegistry()
    reg.register("fail", DummyFailMonitor())
    core = MonitorCore(reg)
    try:
        core.run_by_name("fail")
        report("Core Run Failing Monitor", False, "Expected exception not raised")
    except Exception:
        report("Core Run Failing Monitor", True)


# === 🧪 LOGGER TESTS ===

def test_logger_outputs():
    try:
        log.success("Logger success test", source="LoggerTest")
        log.info("Logger info test", payload={"alpha": 1})
        log.error("Logger error test", payload={"error": "boom!"})
        report("ConsoleLogger Output", True)
    except Exception as e:
        report("ConsoleLogger Output", False, str(e))


# === 🧪 API TESTS ===

def test_api_routes():
    try:
        monitor_api.testing = True
        client: FlaskClient = monitor_api.test_client()

        r1 = client.get("/monitors")
        assert r1.status_code == 200
        assert "price_monitor" in r1.get_json()

        r2 = client.post("/monitor/price_monitor")
        assert r2.status_code == 200

        r3 = client.post("/monitor/all")
        assert r3.status_code == 200
        assert "price_monitor" in r3.get_json().get("monitors", [])

        r4 = client.post("/monitor/not_a_real_monitor")
        assert r4.status_code == 404

        report("REST API Routes", True)
    except Exception as e:
        report("REST API Routes", False, traceback.format_exc())


# === 🧪 LEDGER DB TEST ===

def test_ledger_write_and_read():
    try:
        test_monitor = "test_monitor_sql"
        status = "Success"
        metadata = {"alpha": 123, "beta": True}

        # ✅ Write to DB
        locker.ledger.insert_ledger_entry(test_monitor, status, metadata)

        # ✅ Read it back
        last = locker.ledger.get_last_entry(test_monitor)
        assert last["status"] == status
        assert "alpha" in last["metadata"]
        assert "beta" in last["metadata"]

        # ✅ Check freshness
        status_info = locker.ledger.get_status(test_monitor)
        assert status_info["age_seconds"] < 60
        assert status_info["status"] == "Success"

        report("Ledger DB Write + Read", True)
    except Exception as e:
        report("Ledger DB Write + Read", False, traceback.format_exc())


# === 🚀 MAIN TEST RUN ===

def run_tests():
    log.banner("🧪 Starting Unified Monitor Test Suite")
    start = datetime.now()

    test_registry_lookup()
    test_core_monitor_run_success()
    test_core_monitor_run_failure()
    test_logger_outputs()
    test_api_routes()
    test_ledger_write_and_read()

    end = datetime.now()
    elapsed = (end - start).total_seconds()

    log.banner("📊 MONITOR TEST SUMMARY")

    passed = sum(1 for _, ok, _ in test_results if ok)
    total = len(test_results)

    for name, ok, detail in test_results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{status:10} :: {name}")

    print("\n🧠 Elapsed Time: %.2fs" % elapsed)
    print(f"🎯 Passed: {passed}/{total} ({round(100 * passed / total)}%)")

    if passed == total:
        log.success("🎉 ALL TESTS PASSED", source="TestSuite")
    else:
        log.error("💥 SOME TESTS FAILED", source="TestSuite")

if __name__ == "__main__":
    run_tests()
