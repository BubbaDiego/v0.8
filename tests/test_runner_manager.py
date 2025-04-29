import os
import subprocess
import sys
import platform
import webbrowser
from pathlib import Path
from utils.console_logger import ConsoleLogger as log
from datetime import datetime

class TestRunnerManager:
    """
    Handles loading, categorizing, and running test suites dynamically.
    Generates both console logs and HTML reports.
    """

    def __init__(self, tests_folder: str = "tests/"):
        self.tests_folder = Path(tests_folder)
        self.unit_tests = []
        self.simulation_tests = []
        self.health_tests = []
        self._discover_tests()

    def _discover_tests(self):
        if not self.tests_folder.exists():
            log.error(f"Tests folder not found at {self.tests_folder}", source="TestRunnerManager")
            return

        for file in self.tests_folder.rglob("test_*.py"):
            filename = file.name.lower()
            if "simulate" in filename or "simulation" in filename:
                self.simulation_tests.append(file)
            elif "health" in filename or "post" in filename:
                self.health_tests.append(file)
            else:
                self.unit_tests.append(file)

        log.success(
            f"Discovered {len(self.unit_tests)} unit tests, {len(self.simulation_tests)} simulation tests, {len(self.health_tests)} health tests.",
            source="TestRunnerManager"
        )

    def run_tests(self, test_files: list[Path]):
        if not test_files:
            log.warning("No tests to run!", source="TestRunnerManager")
            return

        report_dir = Path("reports")
        report_dir.mkdir(exist_ok=True)
        html_report = report_dir / "last_test_report.html"

        test_paths = [str(f) for f in test_files]
        log.banner(f"🧪 Starting Test Suite Run ({len(test_paths)} files)")

        try:
            subprocess.run([
                sys.executable,
                "-m", "pytest",
                *test_paths,
                "--tb=short",
                "-q",
                "--html", str(html_report),
                "--self-contained-html"
            ], check=True)
            log.success(f"✅ All tests ran. Detailed report saved to {html_report}", source="TestRunnerManager")
        except subprocess.CalledProcessError:
            log.error(f"❌ Some tests failed. See HTML report: {html_report}", source="TestRunnerManager")
        self._open_html_report(html_report)

    def run_unit_tests(self):
        log.info("Running unit tests...", source="TestRunnerManager")
        self.run_tests(self.unit_tests)

    def run_simulation_tests(self):
        log.info("Running simulation tests...", source="TestRunnerManager")
        self.run_tests(self.simulation_tests)

    def run_health_tests(self):
        log.info("Running health check tests...", source="TestRunnerManager")
        self.run_tests(self.health_tests)

    def run_all_tests(self):
        log.info("Running ALL tests...", source="TestRunnerManager")
        all_tests = self.unit_tests + self.simulation_tests + self.health_tests
        self.run_tests(all_tests)

    def _open_html_report(self, path: Path):
        """
        Open the HTML report in the default system browser (non-CI/headless only).
        """
        try:
            if os.environ.get("CI", "").lower() == "true":
                log.info("CI mode detected. Skipping report auto-open.", source="TestRunnerManager")
                return

            if platform.system() != "Linux" or os.environ.get("DISPLAY"):  # GUI-safe check
                webbrowser.open_new_tab(path.resolve().as_uri())
                log.info("📂 Opened HTML report in browser.", source="TestRunnerManager")
        except Exception as e:
            log.warning(f"⚠️ Could not auto-open report: {e}", source="TestRunnerManager")

    def interactive_menu(self):
        while True:
            print(f"""
🎛️ Test Runner Manager
====================================
1. 🧪 Run All Tests
2. ⚙️ Run Unit Tests Only
3. 🚀 Run Simulation Tests Only
4. 🛡️ Run Health Checks Only
0. ❌ Exit Test Manager
====================================
""")
            choice = input("Select an option: ").strip()

            if choice == "1":
                self.run_all_tests()
            elif choice == "2":
                self.run_unit_tests()
            elif choice == "3":
                self.run_simulation_tests()
            elif choice == "4":
                self.run_health_tests()
            elif choice == "0":
                log.success("Exiting Test Manager.", source="TestRunnerManager")
                break
            else:
                log.warning("Invalid choice. Please try again.", source="TestRunnerManager")
