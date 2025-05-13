from datetime import datetime, timezone
from uuid import uuid4
from data.models import AlertThreshold
from data.dl_thresholds import DLThresholdManager

# Optional: import for CLI support
import os
import sys

# 💾 Add your DB connection
DB_PATH = r"C:\v0.8\data\mother_brain.db"

class AlertThresholdSeeder:
    def __init__(self, db):
        self.dl = DLThresholdManager(db)

    def seed_all(self):
        definitions = [
            # 📦 Portfolio Metrics
            ("TotalValue", "Portfolio", "total_value"),
            ("TotalSize", "Portfolio", "total_size"),
            ("AvgLeverage", "Portfolio", "avg_leverage"),
            ("AvgTravelPercent", "Portfolio", "avg_travel_percent"),
            ("ValueToCollateralRatio", "Portfolio", "value_to_collateral_ratio"),
            ("TotalHeat", "Portfolio", "total_heat_index"),

            # 🧍 Position Metrics
            ("Profit", "Position", "profit"),
            ("HeatIndex", "Position", "heat_index"),
            ("TravelPercentLiquid", "Position", "travel_percent_liquid"),
            ("LiquidationDistance", "Position", "liquidation_distance"),

            # 📈 Market Metrics
            ("PriceThreshold", "Market", "current_price"),
        ]

        inserted = 0
        for alert_type, alert_class, metric_key in definitions:
            existing = self.dl.get_by_type_and_class(alert_type, alert_class, "ABOVE")
            if existing:
                continue

            threshold = AlertThreshold(
                id=str(uuid4()),
                alert_type=alert_type,
                alert_class=alert_class,
                metric_key=metric_key,
                condition="ABOVE",
                low=10.0,
                medium=25.0,
                high=50.0,
                enabled=True,
                last_modified=datetime.now(timezone.utc).isoformat(),
                low_notify="Email",
                medium_notify="Email,SMS",
                high_notify="Email,SMS,Voice"
            )

            self.dl.insert(threshold)
            inserted += 1

        return inserted


# 🧠 Standalone Runner
if __name__ == "__main__":
    try:
        from data.data_locker import DataLocker
        print(f"🧪 Connecting to DB: {DB_PATH}")
        dl = DataLocker(DB_PATH)
        seeder = AlertThresholdSeeder(dl.db)
        count = seeder.seed_all()
        print(f"✅ Seed complete → {count} thresholds created.")
    except Exception as e:
        print(f"❌ Seeder failed: {e}")
        sys.exit(1)
