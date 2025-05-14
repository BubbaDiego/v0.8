# monitor/core/monitor_core.py

class MonitorCore:
    """
    Central controller for all registered monitors.
    """
    def __init__(self, registry):
        self.registry = registry

    def run_all(self):
        """
        Run all registered monitors in sequence.
        """
        for name, monitor in self.registry.get_all_monitors().items():
            try:
                monitor.run_cycle()
            except Exception as e:
                print(f"[ERROR] Monitor {name} failed: {e}")

    def run_by_name(self, name: str):
        """
        Run a specific monitor by its registered name.
        """
        monitor = self.registry.get(name)
        if monitor:
            monitor.run_cycle()
        else:
            print(f"[WARN] Monitor '{name}' not found.")
