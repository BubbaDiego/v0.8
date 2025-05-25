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


def operations_menu():
    """Operations utilities."""
    while True:
        clear_screen()
        console.print("[bold cyan]Operations[/bold cyan]")
        console.print("1) 🛠️ Core Config Test")
        console.print("b) Back")
        choice = input("→ ").strip().lower()
        if choice == "1":
            monitor = OperationsMonitor()
            result = monitor.run_configuration_test()
            log.info("Config Test Result", payload=result)
            input("Press ENTER to continue...")
        elif choice == "b":
            break
        else:
            console.print("Invalid selection.", style="red")
            time.sleep(1)


def main_menu():
    while True:
        clear_screen()
        show_banner()
        console.print("1) Launch Sonic Web")
        console.print("2) ⚙️ Operations")
        console.print("3) Exit")
        choice = input("→ ").strip()
        if choice == "1":
            launch_sonic_web()
        elif choice == "2":
            operations_menu()
        elif choice == "3":
            console.print("Goodbye!", style="green")
            break
        else:
            console.print("Invalid selection.", style="red")
            time.sleep(1)


if __name__ == "__main__":
    main_menu()
