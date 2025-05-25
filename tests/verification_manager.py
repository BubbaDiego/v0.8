import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path
from test_core import TestCore


class TestRunnerManager(TestCore):
    """Backwards compatible wrapper around :class:`TestCore`."""

    def __init__(self) -> None:
        super().__init__()

    def run_tests_glob(self, pattern: str | None = None) -> None:  # pragma: no cover - legacy API
        self.run_glob(pattern)

    def run_tests(self, test_files: list[Path]) -> None:  # pragma: no cover - legacy API
        self.run_files(test_files)

    def interactive_menu(self) -> None:
        """Optional interactive CLI for running tests."""
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

