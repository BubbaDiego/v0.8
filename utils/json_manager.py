# json_manager.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import re

import json
import inspect
from enum import Enum
from typing import Optional
from utils.console_logger import ConsoleLogger

from config.config_constants import ALERT_LIMITS_PATH, THEME_CONFIG_PATH, SONIC_SAUCE_PATH

class JsonType(Enum):
    ALERT_LIMITS = "alert_limitsz.json"
    THEME_CONFIG = "theme_config.json"
    SONIC_SAUCE = "sonic_sauce.json"
    SONIC_CONFIG = "sonic_config.json"
    COMM_CONFIG = "comm_config.json"

class JsonManager:
    def __init__(self, logger=None):
        self.logger = logger or ConsoleLogger()

    def load(self, file_path: str, json_type: JsonType = None):
        """Load and return the JSON data from the specified file path."""
        if json_type:
            path_map = {
                JsonType.ALERT_LIMITS: ALERT_LIMITS_PATH,
                JsonType.THEME_CONFIG: THEME_CONFIG_PATH,
                JsonType.SONIC_SAUCE: SONIC_SAUCE_PATH,
            }
            file_path = str(path_map.get(json_type, file_path))

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 👁️ Context info
            type_info = json_type.name if json_type else "unspecified"
            json_str = json.dumps(data)
            if len(json_str) > 200:
                json_str = json_str[:200] + "..."

            # ✅ Verification
            verification_passed = True
            verification_message = "No verification rules applied."

            if json_type == JsonType.SONIC_SAUCE:
                required_keys = ["hedge_modifiers", "heat_modifiers"]
                missing_keys = [k for k in required_keys if k not in data]
                if missing_keys:
                    verification_passed = False
                    verification_message = f"Missing keys: {missing_keys}"
                else:
                    verification_message = f"All required keys present: {list(data.keys())}"
            elif json_type == JsonType.THEME_CONFIG:
                if not isinstance(data, dict):
                    verification_passed = False
                    verification_message = "Theme config is not a dictionary."
                else:
                    verification_message = f"Theme config keys: {list(data.keys())}"

            # 🧠 Logging
            if verification_passed:
                self.logger.success("✅ JSON verification passed", source="JsonManager", payload={
                    "file": file_path,
                    "type": type_info,
                    "details": verification_message
                })
            else:
                self.logger.warning("⚠️ JSON verification failed", source="JsonManager", payload={
                    "file": file_path,
                    "type": type_info,
                    "details": verification_message
                })

            return data

        except Exception as e:
            self.logger.error("❌ Failed to load JSON", source="JsonManager", payload={
                "file": file_path,
                "error": str(e),
                "type": json_type.name if json_type else "unknown"
            })
            raise

    def save(self, file_path: str, data, json_type: JsonType = None):
        """Save the JSON data to the specified file path and validate the result."""
        if json_type:
            path_map = {
                JsonType.ALERT_LIMITS: ALERT_LIMITS_PATH,
                JsonType.THEME_CONFIG: THEME_CONFIG_PATH,
                JsonType.SONIC_SAUCE: SONIC_SAUCE_PATH,
            }
            file_path = str(path_map.get(json_type, file_path))

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                f.truncate()

            self.logger.success("💾 JSON saved", source="JsonManager", payload={
                "file": file_path,
                "type": json_type.name if json_type else "unknown"
            })

            # 🔍 Post-save validation
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    json.load(f)
                self.logger.success("🔍 Post-save validation passed", source="JsonManager", payload={
                    "file": file_path
                })
            except json.JSONDecodeError as ve:
                self.logger.error("❌ Post-save validation failed", source="JsonManager", payload={
                    "file": file_path,
                    "error": str(ve)
                })
                raise

        except Exception as e:
            self.logger.error("❌ Failed to save JSON", source="JsonManager", payload={
                "file": file_path,
                "error": str(e)
            })
            raise

    def resolve_key_fuzzy(self, input_key: str, json_dict: dict, threshold: float = 0.6, aliases: dict = None) -> \
    Optional[str]:
        """
        Attempts to resolve input_key to a key in json_dict using:
        1. Alias map (manual overrides)
        2. Normalized exact match
        3. Fuzzy matching
        """
        import re
        from difflib import get_close_matches

        if not isinstance(json_dict, dict):
            raise ValueError("Provided json_dict must be a dictionary.")

        def normalize(k):
            return re.sub(r'[\W_]+', '', str(k).lower())

        norm_input = normalize(input_key)

        # 1. Alias resolution
        if aliases:
            for target_key, alias_list in aliases.items():
                if norm_input == normalize(target_key) or norm_input in map(normalize, alias_list):
                    self.logger.debug("🎯 Resolved via alias", source="JsonManager", payload={
                        "input": input_key, "resolved": target_key
                    })
                    return target_key

        # 2. Normalized key match
        norm_map = {normalize(k): k for k in json_dict.keys()}
        if norm_input in norm_map:
            resolved = norm_map[norm_input]
            self.logger.debug("🎯 Resolved via normalized match", source="JsonManager", payload={
                "input": input_key, "resolved": resolved
            })
            return resolved

        # 3. Fuzzy match
        close = get_close_matches(norm_input, norm_map.keys(), n=1, cutoff=threshold)
        if close:
            resolved = norm_map[close[0]]
            self.logger.debug("🤖 Resolved via fuzzy match", source="JsonManager", payload={
                "input": input_key, "resolved": resolved,
                "match_score": threshold
            })
            return resolved

        self.logger.warning("⚠️ Failed to resolve key", source="JsonManager", payload={"input": input_key})
        return None

    def deep_merge(self, source: dict, updates: dict) -> dict:
        """
        Recursively merges updates into the source dictionary.
        Logs operations for each key update and overall success or failure.
        """
        try:
            for key, value in updates.items():
                if key in source and isinstance(source[key], dict) and isinstance(value, dict):
                    self.logger.debug("🔀 Deep merging dict", source="JsonManager", payload={"key": key})
                    source[key] = self.deep_merge(source[key], value)
                else:
                    self.logger.debug("🧬 Updating value", source="JsonManager", payload={"key": key, "value": value})
                    source[key] = value

            self.logger.success("✅ Deep merge completed", source="JsonManager")
            return source

        except Exception as e:
            self.logger.error("❌ Deep merge failed", source="JsonManager", payload={
                "error": str(e),
                "updates": updates
            })
            raise

