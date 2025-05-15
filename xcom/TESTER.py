# dump_active_profile.py

import sys
import os
import json

# Path adjust (if needed)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data.data_locker import DataLocker

DB_PATH = "sonic.sqlite"  # ⚠️ Update if needed

def dump_profile():
    dl = DataLocker(DB_PATH)
    profile = dl.system.get_active_theme_profile()

    print("\n🎯 Active Theme Profile:")
    print(json.dumps(profile, indent=4))

if __name__ == "__main__":
    dump_profile()
