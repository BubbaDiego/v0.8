from __future__ import annotations

import sys
import contextlib
import os
import importlib
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
        files = [
            p
            for p in Path(".").rglob(pattern)
            # Exclude common virtual environment directories
            if not any(part in {".venv", "venv", "site-packages"} for part in p.parts)
        ]
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

        args = [*[str(f) for f in files], "-vv", "-s", "--tb=short", "-rA"]

        # Include optional plugins only if they are installed. This avoids
        # ``pytest`` failing when a plugin is referenced but not available in
        # the environment.
        for plugin in ["pytest_sugar", "pytest_spec", "pytest_console_scripts"]:
            if importlib.util.find_spec(plugin) is not None:
                args.extend(["-p", plugin])

        # ``pytest-html`` provides ``--html`` and ``--self-contained-html``.
        # These options must only be passed when the plugin is available.
        if importlib.util.find_spec("pytest_html") is not None:
            args.extend([
                f"--html={html_report}",
                "--self-contained-html",
            ])

        # ``pytest-json-report`` exposes the ``--json-report`` options. Avoid
        # using them when the plugin cannot be imported.
        if importlib.util.find_spec("pytest_jsonreport") is not None:
            args.extend([
                "--json-report",
                f"--json-report-file={json_report}",
            ])



        # Prevent auto-loading of external plugins which may introduce
        # unwanted dependencies (e.g. anchorpy's pytest plugin requiring
        # ``pytest_xprocess``).  Only the explicitly specified plugins
        # should be loaded during the test run.
        os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")

        with open(txt_log, "w", encoding="utf-8") as f, \
             contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            result = pytest.main(args)

        # After test run, parse results for a concise summary
        passed = failed = skipped = 0
        summary_lines = []
        try:
            import re
            pattern = re.compile(r"(PASSED|FAILED|ERROR|SKIPPED)\s+(\S+::\S+)")
            with open(txt_log, "r", encoding="utf-8") as lf:
                for line in lf:
                    match = pattern.search(line)
                    if match:
                        outcome, test_id = match.groups()
                        summary_lines.append(f"{test_id} {outcome}")
                        if outcome == "PASSED":
                            passed += 1
                        elif outcome in ("FAILED", "ERROR"):
                            failed += 1
                        elif outcome == "SKIPPED":
                            skipped += 1
        except Exception as e:  # pragma: no cover - summary best effort
            log.error(f"Failed to parse log summary: {e}", source="TestCore")

        for line in summary_lines:
            if line.endswith("PASSED"):
                log.success(f"✅ {line}", source="TestCore")
            elif line.endswith("FAILED") or line.endswith("ERROR"):
                log.error(f"❌ {line}", source="TestCore")
            elif line.endswith("SKIPPED"):
                log.warning(f"⚠️ {line}", source="TestCore")

        log.banner("Test Summary")
        log.info(
            f"✅ Passed: {passed}  ❌ Failed: {failed}  ⚠️ Skipped: {skipped}",
            source="TestCore",
        )

        total = passed + failed + skipped
        if total:
            pct = passed / total * 100
            log.info(
                f"🔢 Pass Rate: {pct:.1f}% ({passed}/{total})",
                source="TestCore",
            )

        if result == 0:
            log.success("✅ All tests completed!", source="TestCore")
        else:
            log.error("❌ Test run failed.", source="TestCore")
            try:
                with open(txt_log, "r", encoding="utf-8") as lf:
                    last_lines = lf.readlines()[-20:]
                print("\n==== ERROR DETAILS ====")
                for line in last_lines:
                    print(line.rstrip())
                print("=======================\n")
            except Exception as e:
                log.error(f"Failed to read log file: {e}", source="TestCore")

        log.info(f"📄 HTML Report: {html_report}", source="TestCore")
        log.info(f"🪵 Log File:    {txt_log}", source="TestCore")
        self._open_html_report(html_report)

    # ------------------------------------------------------------------
    def test_alert_core(self) -> None:
        """Run all AlertCore test cases."""
        self.run_glob("alert_core/**/test_*.py")

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
        print("3) Run Alert Core tests")
        print("4) Exit")

        while True:
            choice = input("Enter your choice (1-4): ").strip()
            if choice == "1":
                self.run_glob()
            elif choice == "2":
                pattern = input("Pattern (e.g., tests/test_*.py): ").strip()
                self.run_glob(pattern)
            elif choice == "3":
                self.test_alert_core()
            elif choice == "4":
                break
            else:
                print("Invalid choice. Try again.")

