from unittest.mock import MagicMock

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from alert_core.alert_repository import AlertRepository

class MockDataLocker:
    def __init__(self):
        self.created_alerts = []

    def get_current_value(self, asset):
        # Simulated prices for different assets
        return {
            "BTC": 30250.12,
            "ETH": 1895.42,
            "SOL": 24.11
        }.get(asset, 0)

    def create_alert(self, alert_dict):
        self.created_alerts.append(alert_dict)
        return alert_dict

    def get_alerts(self):
        return self.created_alerts

    def update_alert_conditions(self, alert_id, update_dict):
        print(f"[UPDATE] Alert ID {alert_id} updated: {update_dict}")

    def get_current_timestamp(self):
        return "2025-05-04T12:34:56Z"


def test_starting_value_injection():
    data_locker = MockDataLocker()
    repo = AlertRepository(data_locker)

    # CASE 1: No starting_value provided
    alert_input = {
        "id": "test-123",
        "asset": "BTC",
        "wallet_name": "Main BTC",
        "trigger_value": 31000,
        "direction": "above",
        "level": "High"
    }

    created = repo.create_alert(alert_input)

    print("\n🔎 CASE 1 - No starting_value:")
    print(f"Starting Value: {created.get('starting_value')}")
    assert created["starting_value"] == 30250.12

    # CASE 2: starting_value is already defined
    alert_input2 = {
        "id": "test-124",
        "asset": "ETH",
        "wallet_name": "ETH Vault",
        "trigger_value": 2000,
        "starting_value": 1880.0,
        "direction": "above",
        "level": "Medium"
    }

    created2 = repo.create_alert(alert_input2)

    print("\n🔎 CASE 2 - Provided starting_value:")
    print(f"Starting Value: {created2.get('starting_value')}")
    assert created2["starting_value"] == 1880.0


if __name__ == "__main__":
    test_starting_value_injection()
