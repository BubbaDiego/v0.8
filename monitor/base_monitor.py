import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import logging
from datetime import datetime, timezone

from monitor.monitor_utils import TimerConfig

class BaseMonitor:
    """
    Abstract base for monitors: handles timer config and run_cycle logic.
    Concrete monitors must implement _do_work() and handle ledger writing.
    """
    def __init__(self, name: str, timer_config_path=None, ledger_filename=None):
        self.name = name
        self.logger = logging.getLogger(name)
        self.timer = TimerConfig(timer_config_path)
        self.ledger_file = ledger_filename or f"{name}_ledger.json"

    def run_cycle(self):
        try:
            metadata = self._do_work()
            self._on_success(metadata)
        except Exception as e:
            self._on_error(e)
            raise
        self.timer.set(f"{self.name}_last_run", datetime.now(timezone.utc).isoformat())

    def _on_success(self, metadata: dict):
        """
        Hook for success — monitor should override this if needed
        """
        pass

    def _on_error(self, error: Exception):
        """
        Hook for failure — monitor should override this if needed
        """
        pass

    def _do_work(self):
        raise NotImplementedError("_do_work() must be implemented by subclass")
