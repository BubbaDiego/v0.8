import json
import types
import os
import pytest

import monitor.operations_monitor as om
from utils.schema_validation_service import SchemaValidationService


class DummySystem:
    def __init__(self):
        self.store = {}

    def get_var(self, key):
        return self.store.get(key)

    def set_var(self, key, value):
        self.store[key] = value


class DummyLocker:
    def __init__(self, *a, **k):
        self.ledger = types.SimpleNamespace(insert_ledger_entry=lambda *a, **k: None)
        self.system = DummySystem()


@pytest.fixture(autouse=True)
def patch_datalocker(monkeypatch):
    monkeypatch.setattr(om, "DataLocker", DummyLocker)


def test_run_configuration_test_missing_file(tmp_path, monkeypatch):
    missing = tmp_path / "missing.json"
    monkeypatch.setattr(om, "ALERT_LIMITS_PATH", missing)
    monkeypatch.setattr(SchemaValidationService, "ALERT_LIMITS_FILE", str(missing))

    monitor = om.OperationsMonitor()
    result = monitor.run_configuration_test()
    assert result["config_success"] is False


def test_run_configuration_test_valid_file(tmp_path, monkeypatch):
    valid_file = tmp_path / "alert_limits.json"
    valid_data = {
        "alert_ranges": {
            "liquidation_distance_ranges": {},
            "travel_percent_liquid_ranges": {},
            "heat_index_ranges": {},
            "profit_ranges": {},
            "price_alerts": {},
        },
        "cooldowns": {
            "alert_cooldown_seconds": 1,
            "call_refractory_period": 1,
            "snooze_countdown": 1,
        },
        "notifications": {"heat_index": {"low": {}, "medium": {}, "high": {}}},
    }
    with open(valid_file, "w", encoding="utf-8") as f:
        json.dump(valid_data, f)

    monkeypatch.setattr(om, "ALERT_LIMITS_PATH", valid_file)
    monkeypatch.setattr(SchemaValidationService, "ALERT_LIMITS_FILE", str(valid_file))

    monitor = om.OperationsMonitor()
    result = monitor.run_configuration_test()
    assert result["config_success"] is True


def test_check_for_config_updates(tmp_path, monkeypatch):
    cfg = tmp_path / "alert_limits.json"
    data = {"a": 1}
    with open(cfg, "w", encoding="utf-8") as f:
        json.dump(data, f)

    monkeypatch.setattr(om, "ALERT_LIMITS_PATH", cfg)

    monitor = om.OperationsMonitor()
    updated = monitor.check_for_config_updates()

    assert updated is True
    assert monitor.data_locker.system.get_var("alert_limits") == data
