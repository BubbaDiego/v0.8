import json
import os
from datetime import datetime, timezone

def get_ledger_status(ledger_file_path):
    """
    Returns a dict: {'age_seconds': X, 'last_timestamp': 'isoformat'}
    """
    try:
        if not os.path.exists(ledger_file_path):
            return {"age_seconds": 9999, "last_timestamp": None}
        
        with open(ledger_file_path, "r") as f:
            lines = f.readlines()
            if not lines:
                return {"age_seconds": 9999, "last_timestamp": None}
            last_entry = json.loads(lines[-1])
            last_ts_str = last_entry["timestamp"].replace("Z", "+00:00")
            last_ts = datetime.fromisoformat(last_ts_str)
            now = datetime.now(timezone.utc)
            age = (now - last_ts).total_seconds()
            return {"age_seconds": round(age), "last_timestamp": last_ts.isoformat()}
    except Exception as e:
        print(f"[ERROR] Ledger read error ({ledger_file_path}): {e}")
        return {"age_seconds": 9999, "last_timestamp": None}

def get_ledger_age_seconds():
    try:
        stat = os.stat(LEDGER_FILE)
        age = time.time() - stat.st_mtime
        return age
    except Exception:
        return float('inf')