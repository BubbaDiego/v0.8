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
from utils.console_logger import ConsoleLogger as log
from tests.test_runner_manager import TestRunnerManager

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


def show_launchpad_banner_lightning():
    banner_lines = [
        "=" * 60,
        r"    __                             __      ____            __",
        r"   / /  ____ ___  ________   _____/ /     / __ \____ _____/ /",
        r"  / /  / __ `/ / / / / __ \/ ___/ __ \   / /_/ / __ `/ __  / ",
        r" / /__/ /_/ / /_/ / / / / / /__/ / / /  / ____/ /_/ / /_/ /  ",
        r"\____/\__,_/\__,_/_/ /_/\___  /_/ /_/  /_/    \__,_/\__,_/   ",
        "".center(60),
        "=" * 60
    ]

    for line in banner_lines:
        print(line)
        time.sleep(0.07)  # ~70 milliseconds between lines for lightning speed
    print("\n")

def thunder_crash():
    flashes = [
        "\033[97m⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡\033[0m",
        "\033[90m⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡\033[0m",
        "\033[97m⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡\033[0m",
        "\033[90m⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡\033[0m",
        "\033[97m⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡⚡\033[0m"
    ]

    for flash in flashes:
        print(flash)
        time.sleep(0.08)

    time.sleep(0.2)
    print("\n" + "⚡ CRASH ⚡".center(60))
    time.sleep(0.7)  # <-- Dramatic pause here
    print("\n")
    time.sleep(0.3)  # Optional: Slight extra pause before menu appears

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
    """Display the main LaunchPad menu."""
    check_and_install_critical_packages()
    clear_screen()

    show_launchpad_banner_lightning()

    while True:
        print(f"""
🎛️ Launch Pad Control Center
====================================
1. 🧪 Run All Tests
2. 🛡️ Run Path Audit
3. 🚀 Start Flask App (🖥️ Console)
4. 🩺 Run System Health Check
5. 🌀 Run Cyclone System Tests
6. 🧹 Clear Python Caches
7. 🛡️ Launch Operations Monitor Console (🖥️ Console)
8. 🧪 Launch Test Runner Manager (🖥️ Console)
0. ❌ Exit
====================================
""")

        choice = input("Select an option: ").strip()

        if choice == "1":
            clear_screen()
            run_tests()
        elif choice == "2":
            clear_screen()
            run_path_audit()
        elif choice == "3":
            clear_screen()
            run_flask()
        elif choice == "4":
            clear_screen()
            run_health_check()
        elif choice == "5":
            clear_screen()
            run_cyclone_tests()
        elif choice == "6":
            clear_screen()
            run_clear_caches()
        elif choice == "7":
            clear_screen()
            run_operations_monitor()
        elif choice == "8":
            clear_screen()
            run_test_manager()
        elif choice == "0":
            log.success("Goodbye! 👋", source="LaunchPad")
            sys.exit(0)
        else:
            log.warning("Invalid selection. Please try again.", source="LaunchPad")
            input("\nPress ENTER to continue...")
            clear_screen()

if __name__ == "__main__":
    main_menu()
