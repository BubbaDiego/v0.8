import json
from datetime import datetime
import time

class ConsoleLogger:
    COLORS = {
        "info": "\033[94m",    # Blue
        "success": "\033[92m", # Green
        "warning": "\033[93m", # Yellow
        "error": "\033[91m",   # Red
        "debug": "\033[90m",   # Gray
        "endc": "\033[0m",     # Reset
    }

    ICONS = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "debug": "🐞",
    }

    timers = {}

    @staticmethod
    def _timestamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def _print(cls, level: str, message: str, source: str = None, payload: dict = None):
        color = cls.COLORS.get(level, "")
        icon = cls.ICONS.get(level, "")
        endc = cls.COLORS["endc"]
        source_tag = f"[{source}]" if source else ""
        print(f"{color}{icon} [{cls._timestamp()}] {source_tag} {message}{endc}")
        if payload:
            pretty = json.dumps(payload, indent=2)
            print(f"{color}{pretty}{endc}")

    @classmethod
    def info(cls, message: str, source: str = None, payload: dict = None):
        cls._print("info", message, source, payload)

    @classmethod
    def success(cls, message: str, source: str = None, payload: dict = None):
        cls._print("success", message, source, payload)

    @classmethod
    def warning(cls, message: str, source: str = None, payload: dict = None):
        cls._print("warning", message, source, payload)

    @classmethod
    def error(cls, message: str, source: str = None, payload: dict = None):
        cls._print("error", message, source, payload)

    @classmethod
    def debug(cls, message: str, source: str = None, payload: dict = None):
        cls._print("debug", message, source, payload)

    @classmethod
    def start_timer(cls, label: str):
        cls.timers[label] = time.time()

    @classmethod
    def end_timer(cls, label: str, source: str = None):
        if label not in cls.timers:
            cls.warning(f"No timer started for label '{label}'", source)
            return
        elapsed = time.time() - cls.timers.pop(label)
        cls.success(f"Timer '{label}' completed in {elapsed:.2f} seconds", source)

    @classmethod
    def banner(cls, message: str):
        print("\n" + "="*60)
        print(f"🚀 {message.center(50)} 🚀")
        print("="*60 + "\n")
