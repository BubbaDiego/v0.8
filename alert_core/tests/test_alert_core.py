import sys
import os
# Ensure repository root is on the path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import asyncio
from datetime import datetime
from uuid import uuid4

from data.data_locker import DataLocker
from config.config_loader import load_config
from alert_core.alert_core import AlertCore
from data.alert import AlertType, Condition
from core.constants import DB_PATH


def build_portfolio_alert():
    return {
        "id": str(uuid4()),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "alert_type": AlertType.TotalValue.value,
        "alert_class": "Portfolio",
        "asset": "PORTFOLIO",
        "asset_type": "ALL",
        "trigger_value": 50000.0,
        "condition": Condition.ABOVE.value,
        "notification_type": "SMS",
        "level": "Normal",
        "last_triggered": None,
        "status": "Active",
        "frequency": 1,
        "counter": 0,
        "liquidation_distance": 0.0,
        "travel_percent": 0.0,
        "liquidation_price": 0.0,
        "notes": "Test portfolio alert",
        "description": "total_value",
        "position_reference_id": None,
        "evaluated_value": 0.0,
        "position_type": "N/A"
    }


def build_position_alert(position_id="TEST_POS_123", asset_type="BTC"):
    return {
        "id": str(uuid4()),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "alert_type": AlertType.HeatIndex.value,
        "alert_class": "Position",
        "asset": asset_type,
        "asset_type": asset_type,
        "trigger_value": 50.0,
        "condition": Condition.ABOVE.value,
        "notification_type": "SMS",
        "level": "Normal",
        "last_triggered": None,
        "status": "Active",
        "frequency": 1,
        "counter": 0,
        "liquidation_distance": 0.0,
        "travel_percent": 0.0,
        "liquidation_price": 0.0,
        "notes": "Test position alert",
        "description": "heatindex",
        "position_reference_id": position_id,
        "evaluated_value": 0.0,
        "position_type": "long"
    }


async def run_test():
    print("\n🚀 Initializing AlertCore test run...")

    # Core bootstrapping
    data_locker = DataLocker(str(DB_PATH))
    config_loader = lambda: load_config()
    core = AlertCore(data_locker, config_loader)

    # Create alerts
    portfolio_alert = build_portfolio_alert()
    position_alert = build_position_alert()

    print("\n📦 Creating Portfolio Alert...")
    await core.create_alert(portfolio_alert)

    print("📦 Creating Position Alert...")
    await core.create_alert(position_alert)

    # Process them
    print("\n🔬 Enrich + Evaluate")
    await core.process_alerts()

    # Dump results
    alerts = core.repo.get_all_alerts()
    print(f"\n📊 Final Alert Snapshot ({len(alerts)} alerts):")
    for a in alerts:
        print(f"  - {a['id'][:8]} | {a['alert_class']} | {a['alert_type']} | val={a['evaluated_value']} | level={a['level']}")

    print("\n✅ AlertCore test run complete.")


if __name__ == "__main__":
    asyncio.run(run_test())


def test_alert_core_basic():
    asyncio.run(run_test())
