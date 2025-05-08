import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import subprocess
from pathlib import Path
from core.core_imports import log


class TestRunnerManager:
    def __init__(self):
        self.report_dir = Path("reports")
        self.report_dir.mkdir(exist_ok=True)
        self.default_pattern = "tests/test_*.py"

    def run_tests_glob(self, pattern: str = None):
        """
        Discover test files matching pattern and run them.
        """
        pattern = pattern or self.default_pattern
        files = list(Path(".").rglob(pattern))
        if not files:
            log.warning(f"⚠️ No test files found for pattern: {pattern}", source="TestRunner")
            return
        self.run_tests(files)

    def run_tests(self, test_files: list[Path]):
        """
        Execute pytest with rich reporting: HTML + JSON + text log
        """
        html_report = self.report_dir / "last_test_report.html"
        json_report = self.report_dir / "last_test_report.json"
        txt_log = self.report_dir / "last_test_log.txt"

        log.banner(f"🧪 Test Run Started ({len(test_files)} file(s))")
        log.info(f"⏱ Running: {[str(f) for f in test_files]}", source="TestRunner")

        cmd = [
            sys.executable, "-m", "pytest",
            *[str(f) for f in test_files],
            "-q", "--tb=short",
            f"--html={html_report}", "--self-contained-html",
            "--json-report", f"--json-report-file={json_report}"
        ]

        try:
            with open(txt_log, "w", encoding="utf-8") as f:
                subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, check=True)

            log.success(f"✅ All tests completed!", source="TestRunner")
            log.info(f"📄 HTML Report: {html_report}", source="TestRunner")
            log.info(f"📄 Log File:    {txt_log}", source="TestRunner")
            self._open_html_report(html_report)

        except subprocess.CalledProcessError:
            log.error("❌ Test run failed. Check reports for details.", source="TestRunner")

    def _open_html_report(self, report_path: Path):
        """
        Try to open the HTML test report in the default browser.
        """
        if not report_path.exists():
            return
        try:
            import webbrowser
            webbrowser.open(report_path.resolve().as_uri())
        except Exception:
            pass

    def interactive_menu(self):
        """
        Optional: Run interactively
        """
        print("\n=== 🔍 Test Runner Console ===")
        print("1) Run all tests")
        print("2) Run test file pattern")
        print("3) Exit")

        while True:
            choice = input("Enter your choice (1-3): ").strip()
            if choice == "1":
                self.run_tests_glob()
            elif choice == "2":
                pattern = input("Pattern (e.g., tests/test_*.py): ").strip()
                self.run_tests_glob(pattern)
            elif choice == "3":
                break
            else:
                print("Invalid choice. Try again.")
