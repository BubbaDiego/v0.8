# launch_pad.py

import os
import sys
import subprocess
from datetime import datetime
from colorama import Fore, Style, init
from functools import wraps
from time import time as timer_time

# Initialize colorama
init(autoreset=True)

# --- Configuration ---
CRITICAL_PACKAGES = [
    "pytest",
    "requests",
    "flask",
    "colorama"
]


# --- Helper Functions ---

def clear_screen():
    """Clear the console screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def show_logo():
    """Display Launch Pad Logo and timestamp."""
    print(f"""{Fore.MAGENTA}
    __                   __            __           __     
   / /   ____  ____ ___  / /___  ____ _/ /____  ____/ /__   
  / /   / __ \/ __ `__ \/ / __ \/ __ `/ __/ _ \/ __  / _ \  
 / /___/ /_/ / / / / / / / /_/ / /_/ / /_/  __/ /_/ /  __/  
/_____/\____/_/ /_/ /_/_/\____/\__,_/\__/\___/\__,_/\___/   
{Style.RESET_ALL}""")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{Fore.CYAN}🎛️  Launch Pad started at {now}{Style.RESET_ALL}\n")


def check_and_install_critical_packages():
    """Ensure all critical packages are installed before Launch Pad runs."""
    missing = []
    for package in CRITICAL_PACKAGES:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        print(f"\n{Fore.RED}⚠️  Missing critical packages detected: {', '.join(missing)}{Style.RESET_ALL}")
        choice = input(
            f"{Fore.YELLOW}Would you like to auto-install missing packages? (y/n): {Style.RESET_ALL}").strip().lower()
        if choice == "y":
            for package in missing:
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                    print(f"{Fore.GREEN}✅ Installed {package}{Style.RESET_ALL}")
                except subprocess.CalledProcessError:
                    print(f"{Fore.RED}❌ Failed to install {package}{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Press ENTER to continue...{Style.RESET_ALL}")
            clear_screen()
        else:
            print(f"{Fore.RED}⚠️ Launch Pad may not work properly without required packages.{Style.RESET_ALL}")
            input(f"\n{Fore.YELLOW}Press ENTER to continue at your own risk...{Style.RESET_ALL}")
            clear_screen()


def timed_operation(func):
    """Decorator to measure operation execution time."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = timer_time()
        result = func(*args, **kwargs)
        end = timer_time()
        duration = end - start
        print(f"{Fore.CYAN}⏱️  Completed in {duration:.2f} seconds.{Style.RESET_ALL}\n")
        return result

    return wrapper


# --- Main Operations ---

@timed_operation
def run_tests():
    """Run all tests using Pytest."""
    print(f"\n{Fore.CYAN}🔎 Running all tests with Pytest...\n{Style.RESET_ALL}")
    try:
        subprocess.run([sys.executable, "-m", "pytest", "tests/"], check=True)
        print(f"\n{Fore.GREEN}✅ All tests passed!{Style.RESET_ALL}")
    except subprocess.CalledProcessError:
        print(f"\n{Fore.RED}❌ Some tests failed!{Style.RESET_ALL}")
    input(f"\n{Fore.YELLOW}Press ENTER to return to menu...{Style.RESET_ALL}")
    clear_screen()


@timed_operation
def run_audit():
    """Run the file path audit tool."""
    print(f"\n{Fore.MAGENTA}🛡️ Running Path Audit...\n{Style.RESET_ALL}")
    try:
        subprocess.run([sys.executable, "utils/path_audit.py"], check=True)
        print(f"\n{Fore.GREEN}✅ Path audit completed successfully!{Style.RESET_ALL}")
    except subprocess.CalledProcessError as e:
        print(f"\n{Fore.RED}🚨 Audit failed: {e}{Style.RESET_ALL}")
    input(f"\n{Fore.YELLOW}Press ENTER to return to menu...{Style.RESET_ALL}")
    clear_screen()


@timed_operation
def run_flask():
    """Run the Flask development server."""
    print(f"\n{Fore.YELLOW}🚀 Starting Flask server...\n{Style.RESET_ALL}")
    try:
        subprocess.run([sys.executable, "sonic_app.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n{Fore.RED}🚨 Flask server failed to start: {e}{Style.RESET_ALL}")
    input(f"\n{Fore.YELLOW}Press ENTER to return to menu...{Style.RESET_ALL}")
    clear_screen()


@timed_operation
def run_operations_monitor_console():
    """Launch the Operations Monitor Console."""
    print(f"\n{Fore.BLUE}🛡️ Launching Operations Monitor Console...\n{Style.RESET_ALL}")
    try:
        subprocess.run([sys.executable, "monitor/operations_monitor_console.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n{Fore.RED}🚨 Operations Monitor Console failed to start: {e}{Style.RESET_ALL}")
    input(f"\n{Fore.YELLOW}Press ENTER to return to menu...{Style.RESET_ALL}")
    clear_screen()


@timed_operation
def run_healthcheck():
    """Run a health check manually."""
    print(f"\n{Fore.YELLOW}🩺 Running Health Check...\n{Style.RESET_ALL}")
    try:
        subprocess.run([sys.executable, "-m", "pytest", "tests/test_alert_controller.py"], check=True)
        print(f"\n{Fore.GREEN}✅ Health check passed!{Style.RESET_ALL}")
    except subprocess.CalledProcessError:
        print(f"\n{Fore.RED}❌ Health check FAILED!{Style.RESET_ALL}")
    input(f"\n{Fore.YELLOW}Press ENTER to return to menu...{Style.RESET_ALL}")
    clear_screen()


@timed_operation
def run_cyclone_tests():
    """Run Cyclone system tests."""
    print(f"\n{Fore.YELLOW}🌀 Running Cyclone System Tests...\n{Style.RESET_ALL}")
    try:
        subprocess.run([sys.executable, "-m", "pytest", "tests/test_cyclone.py"], check=True)
        print(f"\n{Fore.GREEN}✅ Cyclone tests passed!{Style.RESET_ALL}")
    except subprocess.CalledProcessError:
        print(f"\n{Fore.RED}❌ Cyclone tests FAILED!{Style.RESET_ALL}")
    input(f"\n{Fore.YELLOW}Press ENTER to return to menu...{Style.RESET_ALL}")
    clear_screen()


@timed_operation
def run_clear_caches():
    """Clear all __pycache__ folders."""
    print(f"\n{Fore.YELLOW}🧹 Clearing Python Caches...\n{Style.RESET_ALL}")
    try:
        subprocess.run([sys.executable, "utils/clear_caches.py"], check=True)
        print(f"\n{Fore.GREEN}✅ Cache clearing completed!{Style.RESET_ALL}")
    except subprocess.CalledProcessError:
        print(f"\n{Fore.RED}❌ Cache clearing failed!{Style.RESET_ALL}")
    input(f"\n{Fore.YELLOW}Press ENTER to return to menu...{Style.RESET_ALL}")
    clear_screen()

# --- Menu ---

def main_menu():
    """Display the command menu."""
    check_and_install_critical_packages()
    clear_screen()
    show_logo()

    while True:
        print(f"""{Fore.BLUE}
🎛️  Launch Pad Control Center
====================================
1. 🧪 Run All Tests
2. 🛡️ Run Path Audit
3. 🚀 Start Flask App
4. ❌ Exit
5. 🛡️ Launch Operations Monitor Console
6. 🩺 Run System Health Check
7. 🌀 Run Cyclone System Tests
8. 🧹 Clear Python Caches
====================================

{Style.RESET_ALL}""")

        choice = input("Select an option: ").strip()

        if choice == "1":
            clear_screen()
            run_tests()
        elif choice == "2":
            clear_screen()
            run_audit()
        elif choice == "3":
            clear_screen()
            run_flask()
        elif choice == "5":
            clear_screen()
            run_operations_monitor_console()
        elif choice == "6":
            clear_screen()
            run_healthcheck()
        elif choice == "7":
            clear_screen()
            run_cyclone_tests()
        elif choice == "8":
            clear_screen()
            run_clear_caches()
        elif choice == "4":
            print(f"{Fore.CYAN}Goodbye! 👋{Style.RESET_ALL}")
            sys.exit(0)
        else:
            print(f"{Fore.RED}⚠️ Invalid selection. Try again.{Style.RESET_ALL}")
            clear_screen()


if __name__ == "__main__":
    main_menu()
