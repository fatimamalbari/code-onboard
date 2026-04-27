"""Tests for file discovery / walking."""

from pathlib import Path

from code_onboard.discovery.file_walker import walk_repo

FIXTURES = Path(__file__).parent / "fixtures"


def test_walk_python_sample():
    files = walk_repo(FIXTURES / "python_sample")
    names = {f.name for f in files}
    assert "main.py" in names
    assert "models.py" in names
    assert "utils.py" in names


def test_walk_ts_sample():
    files = walk_repo(FIXTURES / "ts_sample")
    names = {f.name for f in files}
    assert "index.ts" in names
    assert "config.ts" in names
    assert "userService.ts" in names


def test_walk_respects_max_files():
    files = walk_repo(FIXTURES / "python_sample", max_files=1)
    assert len(files) == 1


def test_walk_skips_unsupported_extensions(tmp_path):
    (tmp_path / "readme.md").write_text("# Hello")
    (tmp_path / "app.py").write_text("print('hello')")
    files = walk_repo(tmp_path)
    assert len(files) == 1
    assert files[0].name == "app.py"


def test_walk_skips_gitignored_files(tmp_path):
    (tmp_path / ".gitignore").write_text("ignored.py\n")
    (tmp_path / "ignored.py").write_text("x = 1")
    (tmp_path / "kept.py").write_text("y = 2")
    files = walk_repo(tmp_path)
    names = {f.name for f in files}
    assert "ignored.py" not in names
    assert "kept.py" in names
