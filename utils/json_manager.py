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
                # Add mappings for SONIC_CONFIG and COMM_CONFIG if needed.
            }
            file_path = str(path_map.get(json_type, file_path))

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            caller = inspect.getframeinfo(inspect.stack()[1][0])
            json_str = json.dumps(data)
            if len(json_str) > 200:
                json_str = json_str[:200] + "..."
            type_info = f" [JSON Type: {json_type.name}]" if json_type else ""

            # --- Verification Block ---
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
            # You can add additional verification for other types if needed.

            if verification_passed:
                self.logger.log_operation(
                    operation_type="JSON Verified",
                    primary_text=(f"Verification passed for {file_path} (JSON Type: {json_type.name}). {verification_message}"),
                    source="system",
                    file=file_path,
                    extra_data={"json_type": json_type.name}
                )
            else:
                self.logger.log_operation(
                    operation_type="JSON Verification Failed",
                    primary_text=(f"Verification failed for {file_path} (JSON Type: {json_type.name}). {verification_message}"),
                    source="system",
                    file=file_path,
                    extra_data={"json_type": json_type.name}
                )

            return data
        except Exception as e:
            caller = inspect.getframeinfo(inspect.stack()[1][0])
            type_info = f" [JSON Type: {json_type.name}]" if json_type else ""
            self.logger.log_operation(
                operation_type="Load JSON Failed",
                primary_text=(f"Failed to load {file_path}{type_info} by system at {caller.filename}:{caller.lineno}: {e}"),
                source="system",
                file=f"{file_path} ({caller.filename}:{caller.lineno})",
                extra_data={"json_type": json_type.name if json_type else ""}
            )
            raise

    def save(self, file_path: str, data, json_type: JsonType = None):
        """Save the JSON data to the specified file path and validate the result."""
        if json_type:
            path_map = {
                JsonType.ALERT_LIMITS: ALERT_LIMITS_PATH,
                JsonType.THEME_CONFIG: THEME_CONFIG_PATH,
                JsonType.SONIC_SAUCE: SONIC_SAUCE_PATH,
                # Add additional mappings if needed.
            }
            file_path = str(path_map.get(json_type, file_path))

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                f.truncate()

            caller = inspect.getframeinfo(inspect.stack()[1][0])
            json_str = json.dumps(data)
            if len(json_str) > 200:
                json_str = json_str[:200] + "..."
            type_info = f" [JSON Type: {json_type.name}]" if json_type else ""

            self.logger.log_operation(
                operation_type="JSON Saved",
                primary_text=(
                    f"Successfully saved {file_path}{type_info} by system at {caller.filename}:{caller.lineno}. Data: {json_str}"),
                source="system",
                file=f"{file_path} ({caller.filename}:{caller.lineno})",
                extra_data={"json_type": json_type.name if json_type else ""}
            )

            # ✅ Post-Save Validation
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    json.load(f)
                self.logger.log_operation(
                    operation_type="JSON Validation",
                    primary_text=f"Post-save validation passed for {file_path}",
                    source="JsonManager",
                    file=file_path,
                    extra_data={"json_type": json_type.name if json_type else ""}
                )
            except json.JSONDecodeError as ve:
                self.logger.log_operation(
                    operation_type="JSON Validation Failed",
                    primary_text=f"Post-save validation failed for {file_path}: {ve}",
                    source="JsonManager",
                    file=file_path,
                    extra_data={"json_type": json_type.name if json_type else ""}
                )
                raise

        except Exception as e:
            caller = inspect.getframeinfo(inspect.stack()[1][0])
            type_info = f" [JSON Type: {json_type.name}]" if json_type else ""
            self.logger.log_operation(
                operation_type="Save JSON Failed",
                primary_text=(
                    f"Failed to save {file_path}{type_info} by system at {caller.filename}:{caller.lineno}: {e}"),
                source="system",
                file=f"{file_path} ({caller.filename}:{caller.lineno})",
                extra_data={"json_type": json_type.name if json_type else ""}
            )
            raise

    def resolve_key_fuzzy(self, input_key: str, json_dict: dict, threshold: float = 0.6, aliases: dict = None) -> \
    Optional[str]:
        """
        Attempts to resolve input_key to a key in json_dict using:
        1. Alias map (manual overrides)
        2. Normalized exact match
        3. Fuzzy matching
        """
        if not isinstance(json_dict, dict):
            raise ValueError("Provided json_dict must be a dictionary.")

        def normalize(k):
            return re.sub(r'[\W_]+', '', str(k).lower())

        norm_input = normalize(input_key)

        # 1. Alias resolution
        if aliases:
            for target_key, alias_list in aliases.items():
                if norm_input == normalize(target_key) or norm_input in map(normalize, alias_list):
                    return target_key

        # 2. Normalized key match
        norm_map = {normalize(k): k for k in json_dict.keys()}
        if norm_input in norm_map:
            return norm_map[norm_input]

        # 3. Fuzzy fallback
        close = get_close_matches(norm_input, norm_map.keys(), n=1, cutoff=threshold)
        return norm_map[close[0]] if close else None

    def deep_merge(self, source: dict, updates: dict) -> dict:
        """
        Recursively merges updates into the source dictionary.
        Logs operations for each key update and overall success or failure.
        """
        try:
            for key, value in updates.items():
                if key in source and isinstance(source[key], dict) and isinstance(value, dict):
                    self.logger.log_operation(
                        operation_type="Deep Merge",
                        primary_text=f"Deep merging key: {key}",
                        source="JsonManager",
                        file="JsonManager.deep_merge"
                    )
                    source[key] = self.deep_merge(source[key], value)
                else:
                    self.logger.log_operation(
                        operation_type="Deep Merge",
                        primary_text=f"Updating key: {key} with value: {value}",
                        source="JsonManager",
                        file="JsonManager.deep_merge"
                    )
                    source[key] = value
            self.logger.log_operation(
                operation_type="Deep Merge Success",
                primary_text="Deep merge completed successfully.",
                source="JsonManager",
                file="JsonManager.deep_merge"
            )
            return source
        except Exception as e:
            self.logger.log_operation(
                operation_type="Deep Merge Failure",
                primary_text=f"Deep merge failed with error: {e}",
                source="JsonManager",
                file="JsonManager.deep_merge"
            )
            raise
