from datetime import datetime, timedelta
from data_locker import DataLocker

def seed_fake_portfolio_history(entries=12, start_time=None):
    dl = DataLocker.get_instance()

    if start_time is None:
        # Default to current time minus N hours
        start_time = datetime.now() - timedelta(hours=entries)

    for i in range(entries):
        snapshot_time = start_time + timedelta(hours=i)
        totals = {
            "total_value": 50000 + (i * 500),         # Simulate slight growth
            "total_collateral": 30000 + (i * 300),
            "total_size": 10000 + (i * 100),
            "avg_leverage": 3.0 + (i * 0.05),
            "avg_travel_percent": 10.0 + (i * 0.2),
            "avg_heat_index": 0.4 + (i * 0.01)
        }
        dl.record_positions_totals_snapshot(totals)
        print(f"[{i+1}] Seeded snapshot @ {snapshot_time.isoformat()}")

if __name__ == "__main__":
    seed_fake_portfolio_history()
