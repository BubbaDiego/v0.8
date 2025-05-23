import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.logging import log

# Import your monitor classes here
from monitor.price_monitor import PriceMonitor
from monitor.position_monitor import PositionMonitor
from monitor.operations_monitor import OperationsMonitor
# Add any new monitors here

from monitor.monitor_registry import MonitorRegistry

class MonitorCore:
    """
    Central controller for all registered monitors.
    """
    def __init__(self):
        self.registry = MonitorRegistry()
        # Register all monitors here (ONLY place this ever happens)
        self.registry.register("price_monitor", PriceMonitor())
        self.registry.register("position_monitor", PositionMonitor())
        self.registry.register("operations_monitor", OperationsMonitor())
        # Add more monitors as needed

    def run_all(self):
        """
        Run all registered monitors in sequence.
        """
        for name, monitor in self.registry.get_all_monitors().items():
            try:
                log.info(f"Running monitor: {name}", source="MonitorCore")
                monitor.run_cycle()
                log.success(f"Monitor '{name}' completed successfully.", source="MonitorCore")
            except Exception as e:
                log.error(f"Monitor '{name}' failed: {e}", source="MonitorCore")

    def run_by_name(self, name: str):
        """
        Run a specific monitor by its registered name.
        """
        monitor = self.registry.get(name)
        if monitor:
            try:
                log.info(f"Running monitor: {name}", source="MonitorCore")
                monitor.run_cycle()
                log.success(f"Monitor '{name}' completed successfully.", source="MonitorCore")
            except Exception as e:
                log.error(f"Monitor '{name}' failed: {e}", source="MonitorCore")
        else:
            log.warning(f"Monitor '{name}' not found.", source="MonitorCore")
