# core/locker_factory.py
"""
Author: BubbaDiego
Purpose: Shared factory to consistently create modular DataLocker instances.
"""

def get_locker():
    from data.data_locker import DataLocker  # ✅ safe import
    from core.constants import DB_PATH
    return DataLocker(str(DB_PATH))

