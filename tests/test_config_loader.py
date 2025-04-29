import pytest
import os
import json
from utils.config_loader import load_config
from utils.console_logger import ConsoleLogger as log

@pytest.fixture
def tmp_config_file(tmp_path):
    config = {
        "alert_cooldown_seconds": 300,
        "alert_ranges": {
            "price_alerts": {
                "BTC": {"enabled": True, "trigger_value": 70000, "condition": "ABOVE"}
            }
        }
    }
    config_path = tmp_path / "alert_limits.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f)
    return str(config_path)

def test_load_config_success(tmp_config_file):
    config = load_config(tmp_config_file)
    assert isinstance(config, dict)
    assert config.get("alert_cooldown_seconds") == 300
    log.success("Test passed: load_config_success", source="TestConfigLoader")

def test_load_config_missing_file():
    config = load_config("nonexistent/path/to/config.json")
    assert config == {}
    log.success("Test passed: load_config_missing_file", source="TestConfigLoader")

def test_load_config_invalid_json(tmp_path):
    bad_config_path = tmp_path / "bad_config.json"
    bad_config_path.write_text("this is not valid JSON")
    config = load_config(str(bad_config_path))
    assert config == {}
    log.success("Test passed: load_config_invalid_json", source="TestConfigLoader")
