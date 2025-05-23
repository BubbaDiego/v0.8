import sys
import os
import types
import logging

# Automatically fix sys.path for tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Stub rich_logger and winsound to avoid optional deps during tests
rich_logger_stub = types.ModuleType("utils.rich_logger")
class RichLogger:
    def __getattr__(self, _):
        def no_op(*a, **k):
            pass
        return no_op
class ModuleFilter(logging.Filter):
    def filter(self, record):
        return True
rich_logger_stub.RichLogger = RichLogger
rich_logger_stub.ModuleFilter = ModuleFilter
sys.modules.setdefault("utils.rich_logger", rich_logger_stub)
sys.modules.setdefault("winsound", types.ModuleType("winsound"))

# Stub positions.hedge_manager to avoid circular import during DataLocker init
hedge_stub = types.ModuleType("positions.hedge_manager")
class HedgeManager:
    def __init__(self, *a, **k):
        pass
    def get_hedges(self):
        return []
    @staticmethod
    def find_hedges(db_path=None):
        return []
hedge_stub.HedgeManager = HedgeManager
sys.modules.setdefault("positions.hedge_manager", hedge_stub)
