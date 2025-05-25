from __future__ import annotations

import sys
import contextlib
from pathlib import Path
import pytest
from core.core_imports import log


class TestCore:
    """Utility to run pytest with rich reporting."""

    def __init__(self, report_dir: str | Path = "reports", default_pattern: str = "tests/test_*.py") -> None:
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(exist_ok=True)
        self.default_pattern = default_pattern

    # ------------------------------------------------------------------
    def run_all(self) -> None:
        """Run all tests matching the default pattern."""
        self.run_glob(self.default_pattern)

    def run_glob(self, pattern: str | None = None) -> None:
        """Discover test files matching *pattern* and run them."""
        pattern = pattern or self.default_pattern
        files = [p for p in Path(".").rglob(pattern)]
        if not files:
            log.warning(f"⚠️ No test files found for pattern: {pattern}", source="TestCore")
            return
        self.run_files(files)

    def run_files(self, files: list[str | Path]) -> None:
        """Execute pytest for the provided *files* with reporting enabled."""
        html_report = self.report_dir / "last_test_report.html"
        json_report = self.report_dir / "last_test_report.json"
        txt_log = self.report_dir / "last_test_log.txt"

        log.banner(f"🧪 Test Run Started ({len(files)} file(s))")
        log.info(f"⏱ Running: {[str(f) for f in files]}", source="TestCore")

        args = [
            *[str(f) for f in files],
            "-q", "--tb=short",
            "-p", "pytest_sugar",
            "-p", "pytest_spec",
            "-p", "pytest_console_scripts",
            f"--html={html_report}", "--self-contained-html",
            "--json-report", f"--json-report-file={json_report}",
        ]

        with open(txt_log, "w", encoding="utf-8") as f, \
             contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            result = pytest.main(args)

        if result == 0:
            log.success("✅ All tests completed!", source="TestCore")
        else:
            log.error("❌ Test run failed. Check reports for details.", source="TestCore")

        log.info(f"📄 HTML Report: {html_report}", source="TestCore")
        log.info(f"🪵 Log File:    {txt_log}", source="TestCore")
        self._open_html_report(html_report)

    # ------------------------------------------------------------------
    def _open_html_report(self, report_path: Path) -> None:
        """Open *report_path* in a browser if possible."""
        if not report_path.exists():
            return
        try:
            import webbrowser
            webbrowser.open(report_path.resolve().as_uri())
        except Exception:
            pass

    # ------------------------------------------------------------------
    def interactive_menu(self) -> None:
        """Interactive CLI for running tests."""
        print("\n=== 🔍 Test Runner Console ===")
        print("1) Run all tests")
        print("2) Run test file pattern")
        print("3) Exit")

        while True:
            choice = input("Enter your choice (1-3): ").strip()
            if choice == "1":
                self.run_glob()
            elif choice == "2":
                pattern = input("Pattern (e.g., tests/test_*.py): ").strip()
                self.run_glob(pattern)
            elif choice == "3":
                break
            else:
                print("Invalid choice. Try again.")

