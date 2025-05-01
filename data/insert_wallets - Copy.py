from data.data_locker import DataLocker
from utils.config_loader import save_config
from datetime import datetime
import uuid

def reset_database_except_wallets():
    dl = DataLocker.get_instance()

    # Step 1: Get all table names except wallets
    tables = dl.get_all_tables()
    tables_to_clear = [t for t in tables if t.lower() != "wallets"]

    for table in tables_to_clear:
        try:
            dl.cursor.execute(f"DELETE FROM {table}")
            print(f"✅ Cleared: {table}")
        except Exception as e:
            print(f"❌ Error clearing {table}: {e}")

    dl.conn.commit()

    # Step 2: Save default alert_limits.json
    default_alert_config = {
        "alert_ranges": {
            "PriceThreshold": {
                "LOW": 0.01,
                "MEDIUM": 0.02,
                "HIGH": 0.03
            },
            "Profit": {
                "LOW": 50,
                "MEDIUM": 100,
                "HIGH": 250
            },
            "TravelPercentLiquid": {
                "LOW": -5,
                "MEDIUM": -10,
                "HIGH": -15
            }
        },
        "global_alert_config": {
            "enabled": True,
            "data_fields": {
                "price": True,
                "profit": True,
                "travel_percent": True,
                "heat_index": True
            },
            "thresholds": {
                "profit": 100,
                "travel_percent": -25,
                "heat_index": 60,
                "price": {
                    "BTC": 60000,
                    "ETH": 3000,
                    "SOL": 200
                }
            }
        }
    }
    save_config("alert_limits.json", default_alert_config)

    # Step 3: Insert sample positions
    for asset in ["BTC", "ETH", "SOL"]:
        position = {
            "id": str(uuid.uuid4()),
            "asset_type": asset,
            "entry_price": 1000,
            "liquidation_price": 500,
            "position_type": "Long",
            "current_price": 1100,
            "pnl_after_fees_usd": 50.0,
            "current_heat_index": 25
        }
        dl.create_position(position)

    # Step 4: Insert fake prices
    for asset in ["BTC", "ETH", "SOL"]:
        price = {
            "id": str(uuid.uuid4()),
            "asset": asset,
            "current_price": 1000,
            "timestamp": datetime.now().isoformat()
        }
        dl.insert_price(price)

    print("✅ Database reset and reconstructed successfully.")

if __name__ == "__main__":
    reset_database_except_wallets()
