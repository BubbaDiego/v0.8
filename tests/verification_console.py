import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path
import webbrowser
from tests.verification_manager import TestRunnerManager
from utils.console_logger import ConsoleLogger as log


class VerificationConsole:
    def __init__(self):
        self.runner = TestRunnerManager()
        self.report_dir = Path("reports")
        self.report_html = self.report_dir / "last_test_report.html"
        self.report_log = self.report_dir / "last_test_log.txt"

    def interactive_menu(self):
        while True:
            print("\n🔍 === Verification Console ===")
            print("1) 🧪 Run All Tests")
            print("2) 📄 Run Specific Test File")
            print("3) 🧬 Run by Pattern or Directory")
            print("4) 📑 View Last HTML Report")
            print("5) 🪵 View Last Test Log")
            print("0) 🔙 Exit to LaunchPad")

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.runner.run_tests_glob()

            elif choice == "2":
                file = input("📄 Enter file name (e.g. test_alerts.py): ").strip()
                fpath = Path("tests") / file
                if fpath.exists():
                    self.runner.run_tests([fpath])
                else:
                    log.error(f"❌ File not found: {fpath}", source="VerificationConsole")

            elif choice == "3":
                pattern = input("🧬 Enter glob (e.g. tests/test_eval*.py): ").strip()
                self.runner.run_tests_glob(pattern)

            elif choice == "4":
                if self.report_html.exists():
                    log.info("📑 Opening last HTML report...", source="VerificationConsole")
                    webbrowser.open(self.report_html.resolve().as_uri())
                else:
                    log.warning("⚠️ No HTML report found.", source="VerificationConsole")

            elif choice == "5":
                if self.report_log.exists():
                    log.info("🪵 Showing last test log...\n", source="VerificationConsole")
                    print("-" * 50)
                    print(self.report_log.read_text(encoding="utf-8"))
                    print("-" * 50)
                else:
                    log.warning("⚠️ No log file found.", source="VerificationConsole")

            elif choice == "0":
                print("👋 Returning to LaunchPad...")
                break

            else:
                print("❌ Invalid choice. Try again.")
