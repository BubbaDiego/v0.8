# operations_monitor_console.py

import time
import sys
from colorama import init, Fore, Style
from monitor.operations_monitor import OperationsMonitor

# Initialize colorama for colors
init(autoreset=True)

class OperationsMonitorConsoleApp:
    """
    Console App Interface for OperationsMonitor.
    """

    def __init__(self):
        self.monitor = OperationsMonitor(
            monitor_interval=300,   # Default 5 minutes
            continuous_mode=False,  # Manual control here
            notifications_enabled=False  # Start with no alerts unless needed
        )

    def main_menu(self):
        while True:
            print(f"""
{Fore.CYAN}
╔══════════════════════════════════════════════════╗
║          🛡️  Operations Monitor Console App         ║
╠══════════════════════════════════════════════════╣
║ {Fore.YELLOW}1.{Fore.CYAN} 🧪  Run Startup POST Test Immediately
║ {Fore.YELLOW}2.{Fore.CYAN} 🔄  Run One-Time Health Check
║ {Fore.YELLOW}3.{Fore.CYAN} 🚀  Start Background Continuous Monitor
║ {Fore.YELLOW}4.{Fore.CYAN} 💣  Exit
╚══════════════════════════════════════════════════╝
{Style.RESET_ALL}
""")
            choice = input(f"{Fore.GREEN}Select an option (1-4): {Style.RESET_ALL}").strip()

            if choice == "1":
                self.run_post()
            elif choice == "2":
                self.run_health_check()
            elif choice == "3":
                self.start_background_monitor()
            elif choice == "4":
                print(f"{Fore.MAGENTA}👋 Exiting Operations Monitor Console App.{Style.RESET_ALL}")
                sys.exit(0)
            else:
                print(f"{Fore.RED}⚠️ Invalid selection. Try again!{Style.RESET_ALL}")

    def run_post(self):
        print(f"{Fore.YELLOW}🧪 Starting POST test...{Style.RESET_ALL}")
        metadata = self.monitor.run_startup_post()
        print(f"{Fore.GREEN}✅ POST completed in {metadata['duration_seconds']:.2f} seconds.{Style.RESET_ALL}")

    def run_health_check(self):
        print(f"{Fore.YELLOW}🔄 Running health check...{Style.RESET_ALL}")
        metadata = self.monitor.run_continuous_health_check()
        if metadata.get("health_success"):
            print(f"{Fore.GREEN}✅ Health check passed in {metadata['duration_seconds']:.2f} seconds.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Health check failed!{Style.RESET_ALL}")

    def start_background_monitor(self):
        print(f"{Fore.YELLOW}🚀 Starting background monitor...{Style.RESET_ALL}")
        self.monitor.continuous_mode = True
        self.monitor.start_background_monitor()
        print(f"{Fore.CYAN}🛡️  Background monitor running every {self.monitor.monitor_interval} seconds.{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}💤 Press CTRL+C to stop.{Style.RESET_ALL}")
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}💥 Background monitor stopped by user.{Style.RESET_ALL}")

if __name__ == "__main__":
    app = OperationsMonitorConsoleApp()
    app.main_menu()
