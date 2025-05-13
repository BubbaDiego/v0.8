import json
import time
import inspect
from datetime import datetime
from utils.fuzzy_wuzzy import fuzzy_match_key


class ConsoleLogger:
    logging_enabled = True
    module_log_control = {}
    group_map = {}
    group_log_control = {}
    timers = {}

    debug_trace_enabled = False
    trace_modules = set()

    COLORS = {
        "info": "\033[94m",  # 🔵 Light blue
        "success": "\033[92m",  # 🟢 Green
        "warning": "\033[93m",  # 🟡 Yellow
        "error": "\033[91m",  # 🔴 Red
        "confidence": "\033[96m",  # 🧊 Cyan
        "debug": "\033[38;5;208m",  # 🧡 Orange-ish
        "endc": "\033[0m",  # ⛔ Resets style
    }

    ICONS = {
        "info": "ℹ️",
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "confidence": "🐻",
        "debug": "🐞",
    }

    @staticmethod
    def _timestamp():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def _get_caller_module(cls):
        stack = inspect.stack()
        for frame in stack[2:]:
            module = inspect.getmodule(frame[0])
            if module and hasattr(module, "__name__"):
                mod_name = module.__name__
                if mod_name == "__main__":
                    filename = frame.filename.split("/")[-1]
                    return filename.replace(".py", "")
                return mod_name.split(".")[-1]
            elif hasattr(frame, "filename"):
                filename = frame.filename.split("/")[-1]
                return filename.replace(".py", "")
        return "unknown"

    @classmethod
    def _is_logging_allowed(cls, module: str) -> bool:

        if not cls.logging_enabled:
            return False

        # 🔒 Explicit module-level control
        if module in cls.module_log_control:
            return cls.module_log_control[module]

        # 🔒 Group-based control
        for group, modules in cls.group_map.items():
            if module in modules:
                if not cls.group_log_control.get(group, True):
                    return False

        # 🔒 Hard-coded prefix mute (optional)
        for prefix in cls.module_log_control:
            if not cls.module_log_control[prefix] and module.startswith(prefix):
                return False

        # ✅ Default = allowed
        return True

    @classmethod
    def _print(cls, level: str, message: str, source: str = None, payload: dict = None):
        caller_module = cls._get_caller_module()
        effective_source = source or caller_module

        if not cls._is_logging_allowed(effective_source):
            return

        if cls.debug_trace_enabled and (
                not cls.trace_modules or effective_source in cls.trace_modules
        ):
            print(f"[🧠 LOGGING DEBUG] caller='{caller_module}' source='{source}' → effective='{effective_source}'")
            print(f"                └─ FINAL DECISION: ✅ allowed")

        color = cls.COLORS.get(level, "")
        icon = cls.ICONS.get(level, "")
        endc = cls.COLORS["endc"]
        timestamp = cls._timestamp()
        label = f"{icon} {message} :: [{effective_source}] @ {timestamp}"

        inline_payload = ""
        if payload:
            try:
                # Simple types: keep inline
                if all(isinstance(v, (str, int, float, bool, type(None))) for v in payload.values()):
                    inline_payload = " → " + ", ".join(f"{k}: {v}" for k, v in payload.items())
                else:
                    try:
                        pretty = json.dumps(payload, indent=2, default=str)  # <== safe fallback
                        inline_payload = "\n" + "\n".join("    " + line for line in pretty.splitlines())
                    except Exception as je:
                        inline_payload = f" [payload JSON serialization failed: {je}]"
            except Exception as e:
                inline_payload = f" [payload processing error: {e}]"

        print(f"{color}{label}{inline_payload}{endc}")

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
        cls.success(f"Timer '{label}' completed in {elapsed:.2f}s", source)

    @classmethod
    def silence_module(cls, module: str):
        cls.module_log_control[module] = False

    @classmethod
    def enable_module(cls, module: str):
        cls.module_log_control[module] = True

    @classmethod
    def assign_group(cls, group: str, modules: list):
        cls.group_map[group] = modules

    @classmethod
    def silence_group(cls, group: str):
        cls.group_log_control[group] = False

    @classmethod
    def enable_group(cls, group: str):
        cls.group_log_control[group] = True

    @classmethod
    def set_trace_modules(cls, modules: list):
        cls.trace_modules = set(modules)
        cls.debug_trace_enabled = True

    @classmethod
    def silence_prefix(cls, prefix: str):
        cls.silence_module(prefix)

    @classmethod
    def silence_all(cls):
        cls.logging_enabled = False

    @classmethod
    def enable_all(cls):
        cls.logging_enabled = True

    @classmethod
    def init_status(cls):
        muted = [k for k, v in cls.module_log_control.items() if not v]
        enabled = [k for k, v in cls.module_log_control.items() if v]

        msg = "\n"
        if muted:
            msg += f"    🔒 Muted Modules:      {', '.join(muted)}\n"
        if enabled:
            msg += f"    🔊 Enabled Modules:    {', '.join(enabled)}\n"
        if cls.group_map:
            msg += f"    🧠 Groups:\n"
            for group, modules in cls.group_map.items():
                msg += f"        {group:<10} ➜ {', '.join(modules)}\n"

        cls.info("🧩 ConsoleLogger initialized.", source="Logger")
        print(msg.strip())

    @classmethod
    def debug_module(cls):
        mod = cls._get_caller_module()
        cls.debug(f"Detected module: {mod}", source="Logger")

    @classmethod
    def banner(cls, message: str):
        print("\n" + "=" * 60)
        print(f"🚀 {message.center(50)} 🚀")
        print("=" * 60 + "\n")

    @classmethod
    def hijack_logger(cls, target_logger_name: str):
        import logging

        def handler(record):
            mod = target_logger_name
            if cls._is_logging_allowed(mod):
                cls.info(record.getMessage(), source=mod)

        h = logging.StreamHandler()
        h.emit = handler
        hijacked_logger = logging.getLogger(target_logger_name)
        hijacked_logger.handlers = [h]
        hijacked_logger.propagate = False
        hijacked_logger.setLevel(logging.INFO)

        cls.info(f"🕵️ Logger '{target_logger_name}' has been hijacked by ConsoleLogger.", source="LoggerControl")

    @classmethod
    def print_dashboard_link(cls, host="127.0.0.1", port=5001, route="/dashboard"):
        url = f"http://{host}:{port}{route}"
        try:
            hyperlink = f"\033]8;;{url}\033\\🔗 Open Sonic Dashboard\033]8;;\033\\"
            print(f"\n🌐 Sonic Dashboard: {hyperlink}\n")
        except Exception:
            print(f"\n🌐 Sonic Dashboard: {url}\n")

    @classmethod
    def route(cls, message: str, source: str = None, payload: dict = None):
        """
        Specialized log method for route tracing.
        Uses cyan color and avoids all info-level mute blocks.
        """
        caller_module = cls._get_caller_module()
        effective_source = source or caller_module

        # Hardcoded bright cyan to bypass 'info' color mapping
        CYAN = "\033[96m"
        ENDC = "\033[0m"
        ICON = "🌐"
        timestamp = cls._timestamp()
        label = f"{ICON} {message} :: [{effective_source}] @ {timestamp}"

        inline_payload = ""
        if payload:
            try:
                if all(isinstance(v, (str, int, float, bool, type(None))) for v in payload.values()):
                    inline_payload = " → " + ", ".join(f"{k}: {v}" for k, v in payload.items())
                else:
                    pretty = json.dumps(payload, indent=2, default=str)
                    inline_payload = "\n" + "\n".join("    " + line for line in pretty.splitlines())
            except Exception as e:
                inline_payload = f" [payload error: {e}]"

        print(f"{CYAN}{label}{inline_payload}{ENDC}")
