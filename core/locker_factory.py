from core.constants import DB_PATH

_locker_instance = None

def get_locker():
    """
    Lazily import DataLocker to avoid circular import.
    """
    global _locker_instance
    if _locker_instance is None:
        from data.data_locker import DataLocker  # 👈 moved inside
        _locker_instance = DataLocker(str(DB_PATH))
    return _locker_instance
