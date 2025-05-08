#!/usr/bin/env python
"""
launch_pad.py
Launch Pad Control Center for Sonic.
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from functools import wraps
from time import time as timer_time
#from tests.test_runner_manager import TestRunnerManager
from utils.schema_validation_service import SchemaValidationService
from tests.verification_console import VerificationConsole
from core.core_imports import log



# --- Configuration ---
CRITICAL_PACKAGES = [
    "pytest",
    "requests",
    "flask",
    "colorama"
]

# --- Helper Functions ---

def clear_screen():
    """Clear the console."""
    os.system('cls' if os.name == 'nt' else 'clear')

def check_and_install_critical_packages():
    """Ensure critical packages are installed."""
    missing = []
    for package in CRITICAL_PACKAGES:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        log.warning(f"Missing critical packages: {', '.join(missing)}", source="LaunchPad")
        choice = input("Would you like to auto-install them? (y/n): ").strip().lower()
        if choice == "y":
            for pkg in missing:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])
                    log.success(f"Installed {pkg}", source="LaunchPad")
                except subprocess.CalledProcessError:
                    log.error(f"Failed to install {pkg}", source="LaunchPad")
            input("\nPress ENTER to continue...")
            clear_screen()
        else:
            log.warning("Continuing without installing missing packages.", source="LaunchPad")
            input("\nPress ENTER to continue at your own risk...")
            clear_screen()

def timed_operation(func):
    """Decorator to time operations."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        log.start_timer(func.__name__)
        result = func(*args, **kwargs)
        log.end_timer(func.__name__, source="LaunchPad")
        return result
    return wrapper

# --- Main Operations ---

@timed_operation
def run_tests():
    """Run all tests."""
    log.info("Running tests with Pytest...", source="LaunchPad")
    try:
        subprocess.run([sys.executable, "-m", "pytest", "tests/"], check=True)
        log.success("All tests passed!", source="LaunchPad")
    except subprocess.CalledProcessError:
        log.error("Some tests failed!", source="LaunchPad")
    input("\nPress ENTER to return to menu...")
    clear_screen()

@timed_operation
def run_flask():
    """Run Flask app."""
    log.info("Starting Flask server...", source="LaunchPad")
    try:
        subprocess.run([sys.executable, "sonic_app.py"], check=True)
    except subprocess.CalledProcessError as e:
        log.error(f"Flask server failed to start: {e}", source="LaunchPad")
    input("\nPress ENTER to return to menu...")
    clear_screen()

@timed_operation
def run_path_audit():
    """Run the path audit tool."""
    log.info("Running Path Audit...", source="LaunchPad")
    try:
        subprocess.run([sys.executable, "utils/path_audit.py"], check=True)
        log.success("Path audit completed successfully!", source="LaunchPad")
    except subprocess.CalledProcessError as e:
        log.error(f"Path audit failed: {e}", source="LaunchPad")
    input("\nPress ENTER to return to menu...")
    clear_screen()

@timed_operation
def run_health_check():
    """Run a system health check."""
    log.info("Running Health Check...", source="LaunchPad")
    try:
        subprocess.run([sys.executable, "-m", "pytest", "tests/test_alert_controller.py"], check=True)
        log.success("Health check passed!", source="LaunchPad")
    except subprocess.CalledProcessError:
        log.error("Health check FAILED!", source="LaunchPad")
    input("\nPress ENTER to return to menu...")
    clear_screen()

@timed_operation
def run_cyclone_tests():
    """Run Cyclone system tests."""
    log.info("Running Cyclone system tests...", source="LaunchPad")
    try:
        subprocess.run([sys.executable, "-m", "pytest", "tests/test_cyclone.py"], check=True)
        log.success("Cyclone tests passed!", source="LaunchPad")
    except subprocess.CalledProcessError:
        log.error("Cyclone tests FAILED!", source="LaunchPad")
    input("\nPress ENTER to return to menu...")
    clear_screen()

@timed_operation
def run_clear_caches():
    """Clear Python caches."""
    log.info("Clearing Python caches...", source="LaunchPad")
    try:
        subprocess.run([sys.executable, "utils/clear_caches.py"], check=True)
        log.success("Cache clearing completed!", source="LaunchPad")
    except subprocess.CalledProcessError:
        log.error("Cache clearing failed!", source="LaunchPad")
    input("\nPress ENTER to return to menu...")
    clear_screen()

@timed_operation
def run_schema_validation_service():
    """Run the Schema Validation Service."""
    log.info("Running Schema Validation Service...", source="LaunchPad")
    SchemaValidationService.batch_validate()
    input("\nPress ENTER to return to menu...")
    clear_screen()

@timed_operation
def run_operations_monitor():
    """Run Operations Monitor Console."""
    log.info("Launching Operations Monitor Console...", source="LaunchPad")
    try:
        subprocess.run([sys.executable, "monitor/operations_monitor_console.py"], check=True)
    except subprocess.CalledProcessError:
        log.error("Operations Monitor Console failed to start!", source="LaunchPad")
    input("\nPress ENTER to return to menu...")
    clear_screen()

@timed_operation
def run_test_manager():
    """Run the Test Runner Manager (interactive menu)."""
    runner = TestRunnerManager(tests_folder="tests/")
    runner.interactive_menu()

def show_launchpad_banner():
    print("\n" + "=" * 60)
    print(r"""\
   __                          __       ____            __
  / /  ____ ___  ______  _____/ /_     / __ \____ _____/ /
 / /  / __ `/ / / / __ \/ ___/ __ \   / /_/ / __ `/ __  / 
/ /__/ /_/ / /_/ / / / / /__/ / / /  / ____/ /_/ / /_/ /   
\____/\__,_/\__,_/_/ /_/\___/_/ /_/  /_/    \__,_/\__,_/   
""")
    print("".center(60))
    print("=" * 60 + "\n")


# --- Menu ---

def main_menu():
    clear_screen()
    log.banner("🚀 LAUNCH PAD - CONTROL CENTER 🚀")

    print("""
    🖥️  CORE SERVICES
    ---------------------------
    1) 🚀 Start Flask App
    2) 🧪 Launch Test Manager
    3) 🧬 Launch Verification Console
    4) 🛡️ Launch Operations Monitor

    🛠️  UTILITIES
    ---------------------------
    5) 🧹 Clear Python Caches
    6) 📋 Run Schema Validation Service

    🩺  SYSTEM HEALTH
    ---------------------------
    7) 🩺 Run System Health Check
    8) 🌀 Run Cyclone System Tests

    ❌  OTHER
    ---------------------------
    0) ❌ Exit
    """)

    choice = input("Enter your choice (0-7): ").strip()

    if choice == "1":
        clear_screen()
        run_flask()
    elif choice == "2":
        clear_screen()
        run_test_manager()
    elif choice == "3":
        clear_screen()
        VerificationConsole().interactive_menu()
    elif choice == "4":
        clear_screen()
        run_operations_monitor()
    elif choice == "5":
        clear_screen()
        run_clear_caches()
    elif choice == "6":
        clear_screen()
        run_health_check()
    elif choice == "7":
        clear_screen()
        run_cyclone_tests()
    elif choice == "0":
        log.success("Goodbye! 👋", source="LaunchPad")
        sys.exit(0)
    else:
        log.warning("Invalid selection. Please try again.", source="LaunchPad")
        input("\nPress ENTER to continue...")
        clear_screen()


if __name__ == "__main__":
    main_menu()
