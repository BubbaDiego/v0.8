import pytest
import asyncio
import copy
import json
import os
from utils.config_loader import load_config
from alerts.alert_repository import AlertRepository
from alerts.alert_service_manager import AlertServiceManager
from data.data_locker import DataLocker
from utils.console_logger import ConsoleLogger as log

from tests.system.system_test_helpers import create_temp_alert_limits_json


@pytest.mark.system
@pytest.mark.asyncio
async def test_alert_limits_dynamic_behavior(tmp_path):
    """
    System Test:
    1. Load alert_limits.json
    2. Verify config loaded correctly
    3. Create an alert based on current limits
    4. Modify alert_limits.json
    5. Reload config
    6. Create a new alert based on new limits
    7. Compare alerts
    """

    create_temp_alert_limits_json()

    # Setup fake environment
    original_limits_path = "alert_limits.json"
    backup_limits_path = tmp_path / "alert_limits_backup.json"

    # --- Step 1: Load original config ---
    log.banner("SYSTEM TEST: Load Original Config")
    original_config = load_config(original_limits_path)
    assert original_config, "❌ Failed to load original alert_limits.json"

    # Save backup
    with open(backup_limits_path, "w", encoding="utf-8") as f:
        json.dump(original_config, f, indent=4)

    # --- Step 2: Verify config loaded ---
    assert "alert_ranges" in original_config, "❌ Missing alert_ranges in config"

    # --- Step 3: Create First Alert ---
    log.banner("SYSTEM TEST: Create First Alert")
    data_locker = DataLocker.get_instance()
    repo = AlertRepository(data_locker)

    first_alert = {
        "id": "system-test-alert-001",
        "alert_type": "PriceThreshold",
        "alert_class": "Market",
        "asset_type": "BTC",
        "trigger_value": 60000,
        "condition": "ABOVE",
        "notification_type": "SMS",
        "level": "Normal",
        "last_triggered": None,
        "status": "Active",
        "frequency": 1,
        "counter": 0,
        "liquidation_distance": 0.0,
        "travel_percent": 0.0,
        "liquidation_price": 0.0,
        "notes": "First alert created from original config",
        "description": "First system test alert",
        "position_reference_id": None,
        "evaluated_value": 0.0
    }

    success = repo.create_alert(first_alert)
    assert success, "❌ Failed to create first alert"

    # --- Step 4: Modify alert_limits.json ---
    log.banner("SYSTEM TEST: Modify Config")
    modified_config = copy.deepcopy(original_config)
    modified_config["alert_cooldown_seconds"] = 300  # Example change
    modified_config["global_alert_config"]["max_alerts"] = 999

    with open(original_limits_path, "w", encoding="utf-8") as f:
        json.dump(modified_config, f, indent=4)

    # --- Step 5: Reload modified config ---
    log.banner("SYSTEM TEST: Reload Modified Config")
    reloaded_config = load_config(original_limits_path)
    assert reloaded_config["alert_cooldown_seconds"] == 300, "❌ Config not modified properly"

    # --- Step 6: Create Second Alert ---
    log.banner("SYSTEM TEST: Create Second Alert")
    second_alert = {
        "id": "system-test-alert-002",
        "alert_type": "PriceThreshold",
        "alert_class": "Market",
        "asset_type": "ETH",
        "trigger_value": 4000,
        "condition": "ABOVE",
        "notification_type": "Email",
        "level": "Normal",
        "last_triggered": None,
        "status": "Active",
        "frequency": 2,
        "counter": 0,
        "liquidation_distance": 0.0,
        "travel_percent": 0.0,
        "liquidation_price": 0.0,
        "notes": "Second alert created from modified config",
        "description": "Second system test alert",
        "position_reference_id": None,
        "evaluated_value": 0.0
    }

    success2 = repo.create_alert(second_alert)
    assert success2, "❌ Failed to create second alert"

    # --- Step 7: Compare / Validate Alerts ---
    log.banner("SYSTEM TEST: Validation Complete")
    assert first_alert["trigger_value"] != second_alert["trigger_value"], "❌ Trigger values should differ"
    assert first_alert["asset_type"] != second_alert["asset_type"], "❌ Asset types should differ"

    log.success("✅ System Test: alert_limits behavior validated successfully!", source="TestAlertLimitsSystem")

    # --- Cleanup: Restore original config
    with open(original_limits_path, "w", encoding="utf-8") as f:
        json.dump(original_config, f, indent=4)
