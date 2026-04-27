"""Tests for entry point detection."""

from pathlib import Path

from code_onboard.analysis.entry_points import find_entry_points, _is_test_file
from code_onboard.analysis.graph import build_dependency_graph
from code_onboard.discovery.file_walker import walk_repo
from code_onboard.parsing.parser_pool import parse_all_files

FIXTURES = Path(__file__).parent / "fixtures"


def test_python_main_guard_detected():
    root = FIXTURES / "python_sample"
    files = walk_repo(root)
    summaries = parse_all_files(files, root)
    graph = build_dependency_graph(summaries, root)
    entries = find_entry_points(summaries, graph, root)

    paths = [ep.path for ep in entries]
    assert "main.py" in paths

    main_ep = next(ep for ep in entries if ep.path == "main.py")
    assert main_ep.kind == "main_guard"


def test_test_files_filtered():
    """Test files (.spec.ts, .test.ts, etc.) should not appear as entry points."""
    assert _is_test_file("src/lib/auth.spec.ts")
    assert _is_test_file("src/lib/auth.test.tsx")
    assert _is_test_file("src/components/Button.e2e.ts")
    assert _is_test_file("src/__tests__/helper.ts")
    assert _is_test_file("src/components/Button.stories.tsx")
    assert not _is_test_file("src/lib/auth.ts")
    assert not _is_test_file("src/components/Button.tsx")
    assert not _is_test_file("src/app/page.tsx")


def test_nextjs_routes_detected(tmp_path):
    """Next.js App Router files should be detected as entry points."""
    from code_onboard.analysis.entry_points import _infer_nextjs_route

    assert _infer_nextjs_route("apps/dashboard/src/app/page.tsx") == "/"
    assert _infer_nextjs_route("apps/dashboard/src/app/auth/sign-in/page.tsx") == "/auth/sign-in"
    assert _infer_nextjs_route("apps/dashboard/src/app/(protected)/dashboard/page.tsx") == "/dashboard"
    assert _infer_nextjs_route("apps/dashboard/src/app/api/auth/logout/route.ts") == "/api/auth/logout"
    assert _infer_nextjs_route("src/lib/utils.ts") is None
