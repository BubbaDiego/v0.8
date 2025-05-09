import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
from datetime import datetime
from uuid import uuid4
from core.logging import log
from alerts.alert_core import AlertCore
from data.data_locker import DataLocker

# 🧪 Mock config loader with controllable thresholds
def mock_config_loader():
    return {
        "alert_ranges": {
            "profit": {"low": 10, "medium": 100, "high": 500},
            "heatindex": {"low": 2, "medium": 5, "high": 9},
            "travelpercentliquid": {"low": 10, "medium": 25, "high": 50},
        },
        "alert_limits": {
            "profit_ranges": {"low": 10, "medium": 100, "high": 500, "enabled": True},
            "heat_index_ranges": {"low": 2, "medium": 5, "high": 9, "enabled": True},
            "travel_percent_liquid_ranges": {"low": 10, "medium": 25, "high": 50, "enabled": True},
        }
    }

# 🔧 Simulated test data
TEST_POSITION = {
    "id": "test_pos_001",
    "asset_type": "BTC",
    "entry_price": 10000,
    "liquidation_price": 8000,
    "position_type": "LONG",
    "wallet_name": "TestWallet1",
    "current_heat_index": 6,
    "pnl_after_fees_usd": 200,
    "travel_percent": 0.0,
    "liquidation_distance": 0.0,
}

# 🧠 In-memory Alert Generator
def generate_test_alert(alert_type, trigger_value, value_override=None):
    alert_id = str(uuid4())
    return {
        "id": alert_id,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "alert_type": alert_type,
        "alert_class": "Position",
        "asset": "BTC",
        "asset_type": "BTC",
        "trigger_value": trigger_value,
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
        "notes": f"Test alert {alert_type}",
        "description": alert_type,
        "position_reference_id": "test_pos_001",
        "evaluated_value": value_override if value_override is not None else 0.0,
        "position_type": "LONG"
    }

# 🧪 Test Runner
async def run_e2e_alert_test():
    log.banner("🔥 E2E ALERT BARRAGE TEST BEGIN")

    # 🧬 Setup DataLocker and AlertCore
    dl = DataLocker(":memory:")
    dl.positions.insert_position(TEST_POSITION)
    alert_core = AlertCore(dl, mock_config_loader)

    # 🧪 Inject all state levels for each alert type
    alert_inputs = [
        # PROFIT
        generate_test_alert("profit", 10, value_override=0),
        generate_test_alert("profit", 10, value_override=50),
        generate_test_alert("profit", 10, value_override=200),
        generate_test_alert("profit", 10, value_override=700),
        # HEATINDEX
        generate_test_alert("heatindex", 2, value_override=1),
        generate_test_alert("heatindex", 2, value_override=4),
        generate_test_alert("heatindex", 2, value_override=6),
        generate_test_alert("heatindex", 2, value_override=10),
        # TRAVELPERCENT
        generate_test_alert("travelpercentliquid", 10, value_override=5),
        generate_test_alert("travelpercentliquid", 10, value_override=20),
        generate_test_alert("travelpercentliquid", 10, value_override=35),
        generate_test_alert("travelpercentliquid", 10, value_override=60),
    ]

    # 🚀 Create alerts
    created = 0
    for alert in alert_inputs:
        if await alert_core.create_alert(alert):
            created += 1
    log.success("🛠 All test alerts created", payload={"count": created})

    # 💥 Evaluate
    results = await alert_core.evaluate_all_alerts()
    log.banner("📊 ALERT EVALUATION RESULTS")

    for r in results:
        log.info(f"{r.alert_type} → value={r.evaluated_value} | level={r.level}", payload={"id": r.id})

    log.success("✅ End-to-End alert test completed.")
    log.print_dashboard_link()

# 🔁 Entry
if __name__ == "__main__":
    asyncio.run(run_e2e_alert_test())
