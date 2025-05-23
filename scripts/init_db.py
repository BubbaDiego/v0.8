#!/usr/bin/env python3
"""Initialize the SQLite database with all required tables.

Running this script will create ``mother_brain.db`` (or the DB_PATH set in the
``BASE_DIR`` environment) and ensure all tables exist. It simply instantiates
``DataLocker`` which performs table creation.
"""
from __future__ import annotations

from core.core_imports import DB_PATH
from data.data_locker import DataLocker


def main() -> int:
    locker = DataLocker(str(DB_PATH))
    locker.close()
    print(f"✅ Database initialized at: {DB_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
