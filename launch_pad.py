#!/usr/bin/env python3
"""Sonic Launch console."""

import os
import sys
import subprocess
import time
import webbrowser
from rich.console import Console
from rich.text import Text

from core.core_imports import configure_console_log
from core.logging import log
from monitor.operations_monitor import OperationsMonitor
from test_core import TestCore
from data.data_locker import DataLocker
from core.constants import DB_PATH
from utils.startup_service import StartUpService

console = Console()
configure_console_log()


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def show_banner():
    """Display the Sonic Launch banner."""
    try:
        from pyfiglet import Figlet
        art = Figlet(font="slant").renderText("Sonic Launch")
        console.print(Text(art, style="cyan"))
    except Exception:
        console.print(Text("Sonic Launch", style="bold cyan italic"), justify="center")
        console.print()


def launch_sonic_web():
    """Start the Sonic web server and open the browser."""
    console.print("[bold green]Launching Sonic Web...[/bold green]")
    proc = subprocess.Popen([sys.executable, "sonic_app.py"])
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:5000")
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


def launch_cyclone():
    """Launch the Cyclone interactive console."""
    console.print("[bold blue]Launching Cyclone...[/bold blue]")
    proc = subprocess.Popen([sys.executable, "cyclone_app.py"])
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


def launch_web_and_monitor():
    """Start the Sonic web server and Sonic monitor together."""
    console.print("[bold green]Launching Sonic App and Monitor...[/bold green]")
    web_proc = subprocess.Popen([sys.executable, "sonic_app.py"])
    monitor_proc = subprocess.Popen([sys.executable, os.path.join("monitor", "sonic_monitor.py")])
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:5000")
    try:
        web_proc.wait()
    except KeyboardInterrupt:
        web_proc.terminate()
        monitor_proc.terminate()


def operations_menu():
    """Operations utilities."""
    while True:
        clear_screen()
        console.print("[bold cyan]Operations[/bold cyan]")
        console.print("1) Run POST")
        console.print("2) 🛠️ Core Config Test")
        console.print("3) Recover Database")
        console.print("b) Back")
        choice = input("→ ").strip().lower()
        if choice == "1":
            monitor = OperationsMonitor()

            result = monitor.run_startup_post()
            log.info("POST Result", payload=result)
            input("Press ENTER to continue...")
        elif choice == "2":
            monitor = OperationsMonitor()

            result = monitor.run_configuration_test()
            log.info("Config Test Result", payload=result)
            input("Press ENTER to continue...")
        elif choice == "3":
            console.print("[yellow]Attempting database recovery...[/yellow]")
            dl = DataLocker(str(DB_PATH))
            dl.db.recover_database()
            dl.initialize_database()
            dl._seed_modifiers_if_empty()
            dl._seed_wallets_if_empty()
            dl._seed_thresholds_if_empty()
            dl.close()
            console.print("[green]Database recovery complete.[/green]")
            input("Press ENTER to continue...")
        elif choice == "b":
            break
        else:
            console.print("Invalid selection.", style="red")
            time.sleep(1)


def test_core_menu():
    """Run unit tests via :class:`TestCore`."""
    tester = TestCore()
    tester.interactive_menu()
    input("Press ENTER to return...")


def main_menu():
    while True:
        clear_screen()
        show_banner()
        console.print("1) 🦔 Sonic App + 🖥️ Sonic Monitor")
        console.print("2) 🌀 Launch Cyclone")
        console.print("3) Launch Sonic Web")
        console.print("4) 🌅 Startup Service")
        console.print("5) ⚙️ Operations")
        console.print("6) 🧪 Test Core")
        console.print("7) Exit")
        choice = input("→ ").strip()
        if choice == "1":
            launch_web_and_monitor()
        elif choice == "2":
            launch_cyclone()
        elif choice == "3":
            launch_sonic_web()
        elif choice == "4":
            StartUpService.run_all()
            input("Press ENTER to continue...")
        elif choice == "5":
            operations_menu()
        elif choice == "6":
            test_core_menu()
        elif choice == "7":
            console.print("Goodbye!", style="green")
            break
        else:
            console.print("Invalid selection.", style="red")
            time.sleep(1)


if __name__ == "__main__":
    main_menu()
