# manage.py

import os
import sys
import unittest
import subprocess
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def run_tests():
    """Discover and run all unittests in the /tests/ directory."""
    print(f"\n{Fore.CYAN}🔎 Running all tests...\n{Style.RESET_ALL}")
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    loader = unittest.TestLoader()
    start_dir = os.path.join(PROJECT_ROOT, "tests")
    suite = loader.discover(start_dir)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    if result.wasSuccessful():
        print(f"\n{Fore.GREEN}✅ All tests passed!{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}❌ Some tests failed!{Style.RESET_ALL}")
    sys.exit(not result.wasSuccessful())

def run_audit():
    """Run the file path audit tool."""
    print(f"\n{Fore.MAGENTA}🛡️ Running Path Audit...\n{Style.RESET_ALL}")
    try:
        subprocess.run(["python", "utils/path_audit.py"], check=True)
        print(f"\n{Fore.GREEN}✅ Path audit completed successfully!{Style.RESET_ALL}")
    except subprocess.CalledProcessError as e:
        print(f"\n{Fore.RED}🚨 Audit failed: {e}{Style.RESET_ALL}")

def run_flask():
    """Run the Flask development server."""
    print(f"\n{Fore.YELLOW}🚀 Starting Flask server...\n{Style.RESET_ALL}")
    try:
        subprocess.run(["python", "sonic_app.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n{Fore.RED}🚨 Flask server failed to start: {e}{Style.RESET_ALL}")

def main_menu():
    """Display the command menu."""
    print(f"""{Fore.BLUE}
🎛️ Sonic Control Center
==========================
1. 🧪 {Fore.RESET}Run Tests
{Fore.BLUE}2. 🛡️  {Fore.RESET}Run Path Audit
{Fore.BLUE}3. 🚀 {Fore.RESET}Start Flask App
{Fore.BLUE}4. ❌ {Fore.RESET}Exit
==========================
{Style.RESET_ALL}""")

    choice = input("Select an option: ").strip()

    if choice == "1":
        run_tests()
    elif choice == "2":
        run_audit()
    elif choice == "3":
        run_flask()
    elif choice == "4":
        print(f"{Fore.CYAN}Goodbye! 👋{Style.RESET_ALL}")
        sys.exit(0)
    else:
        print(f"{Fore.RED}⚠️ Invalid choice, try again.{Style.RESET_ALL}")
        main_menu()

if __name__ == "__main__":
    main_menu()
