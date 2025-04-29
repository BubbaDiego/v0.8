# clear_alerts.py
from data.data_locker import DataLocker
from utils.console_logger import ConsoleLogger as log

def clear_all_alerts():
    try:
        dl = DataLocker.get_instance()
        count_before = len(dl.get_alerts())
        dl.clear_alerts()
        count_after = len(dl.get_alerts())
        log.success(f"✅ Cleared {count_before} alert(s). Now {count_after} remain.", source="ClearAlerts")
    except Exception as e:
        log.error(f"❌ Failed to clear alerts: {e}", source="ClearAlerts")

if __name__ == "__main__":
    print("⚠️  WARNING: This will delete ALL alerts.")
    confirm = input("Are you sure you want to continue? (yes/no): ").strip().lower()
    if confirm == "yes":
        clear_all_alerts()
    else:
        print("Aborted. No alerts deleted.")
