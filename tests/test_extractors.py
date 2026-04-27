"""Tests for Python and TS extractors."""

from pathlib import Path

from code_onboard.parsing.parser_pool import parse_file

FIXTURES = Path(__file__).parent / "fixtures"


def test_python_functions():
    summary = parse_file(FIXTURES / "python_sample" / "utils.py", FIXTURES / "python_sample")
    assert summary is not None
    fn_names = [f.name for f in summary.functions]
    assert "helper_function" in fn_names
    assert "load_config" in fn_names
    assert "fetch_data" in fn_names


def test_python_classes():
    summary = parse_file(FIXTURES / "python_sample" / "models.py", FIXTURES / "python_sample")
    assert summary is not None
    cls_names = [c.name for c in summary.classes]
    assert "User" in cls_names
    assert "Admin" in cls_names
    # Check Admin bases
    admin = next(c for c in summary.classes if c.name == "Admin")
    assert "User" in admin.bases


def test_python_imports():
    summary = parse_file(FIXTURES / "python_sample" / "main.py", FIXTURES / "python_sample")
    assert summary is not None
    modules = [imp.module for imp in summary.imports]
    assert "utils" in modules
    assert "models" in modules


def test_python_main_guard():
    summary = parse_file(FIXTURES / "python_sample" / "main.py", FIXTURES / "python_sample")
    assert summary is not None
    assert summary.has_main_guard is True


def test_python_no_main_guard():
    summary = parse_file(FIXTURES / "python_sample" / "utils.py", FIXTURES / "python_sample")
    assert summary is not None
    assert summary.has_main_guard is False


def test_ts_functions():
    summary = parse_file(FIXTURES / "ts_sample" / "index.ts", FIXTURES / "ts_sample")
    assert summary is not None
    fn_names = [f.name for f in summary.functions]
    assert "main" in fn_names


def test_ts_classes():
    summary = parse_file(FIXTURES / "ts_sample" / "config.ts", FIXTURES / "ts_sample")
    assert summary is not None
    cls_names = [c.name for c in summary.classes]
    assert "Config" in cls_names


def test_ts_imports():
    summary = parse_file(FIXTURES / "ts_sample" / "index.ts", FIXTURES / "ts_sample")
    assert summary is not None
    modules = [imp.module for imp in summary.imports]
    assert "./services/userService" in modules
    assert "./config" in modules


def test_ts_exports():
    summary = parse_file(
        FIXTURES / "ts_sample" / "services" / "userService.ts",
        FIXTURES / "ts_sample",
    )
    assert summary is not None
    assert "UserService" in summary.exports
    assert "createService" in summary.exports


def test_ts_arrow_function():
    summary = parse_file(
        FIXTURES / "ts_sample" / "services" / "userService.ts",
        FIXTURES / "ts_sample",
    )
    assert summary is not None
    fn_names = [f.name for f in summary.functions]
    assert "createService" in fn_names
