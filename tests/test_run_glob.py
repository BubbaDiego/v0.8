from pathlib import Path
from test_core.test_core import TestCore


def test_run_glob_filters_virtual_envs(tmp_path, monkeypatch):
    # Set up directory structure with various test files
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "test_valid.py").write_text("")

    for d in [".venv", "venv", "site-packages"]:
        (tmp_path / d).mkdir()
        (tmp_path / d / "test_ignore.py").write_text("")

    captured: list[Path] = []

    def fake_run_files(self, files):
        captured.extend(files)

    tc = TestCore()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(TestCore, "run_files", fake_run_files)

    tc.run_glob("test_*.py")

    assert captured == [Path("sub/test_valid.py")]
