"""Tests for dependency graph building."""

from pathlib import Path

from code_onboard.analysis.graph import (
    build_dependency_graph,
    _resolve_ts_import,
    _load_tsconfig_paths,
    _resolve_alias,
)
from code_onboard.parsing.parser_pool import parse_all_files
from code_onboard.discovery.file_walker import walk_repo

FIXTURES = Path(__file__).parent / "fixtures"


def test_python_graph():
    root = FIXTURES / "python_sample"
    files = walk_repo(root)
    summaries = parse_all_files(files, root)
    graph = build_dependency_graph(summaries, root)

    # main.py imports utils and models
    assert graph.in_degree("utils.py") >= 1
    assert graph.in_degree("models.py") >= 1

    # main.py has edges to utils and models
    main_deps = graph.successors("main.py")
    assert "utils.py" in main_deps or "models.py" in main_deps


def test_ts_graph():
    root = FIXTURES / "ts_sample"
    files = walk_repo(root)
    summaries = parse_all_files(files, root)
    graph = build_dependency_graph(summaries, root)

    # index.ts imports config.ts and services/userService.ts
    deps = graph.successors("index.ts")
    assert "config.ts" in deps or "services/userService.ts" in deps

    # config.ts is imported by multiple files
    assert graph.in_degree("config.ts") >= 1


def test_tsconfig_path_alias_resolution(tmp_path):
    """Test that tsconfig path aliases like @/* are resolved."""
    import json

    # Create a mini monorepo structure
    app_dir = tmp_path / "apps" / "web" / "src"
    pkg_dir = tmp_path / "packages" / "ui" / "src" / "components"
    app_dir.mkdir(parents=True)
    pkg_dir.mkdir(parents=True)

    # Create tsconfig with path aliases
    tsconfig = {
        "compilerOptions": {
            "paths": {
                "@/*": ["./src/*"],
                "@shared/ui/*": ["../../packages/ui/src/*"],
            }
        }
    }
    (tmp_path / "apps" / "web" / "tsconfig.json").write_text(json.dumps(tsconfig))

    # Create source files
    (app_dir / "index.ts").write_text("export const x = 1;")
    (app_dir / "lib" ).mkdir()
    (app_dir / "lib" / "utils.ts").write_text("export const cn = () => {};")
    (pkg_dir / "button.tsx").write_text("export const Button = () => {};")

    all_paths = {
        "apps/web/src/index.ts",
        "apps/web/src/lib/utils.ts",
        "packages/ui/src/components/button.tsx",
    }

    tsconfig_paths = _load_tsconfig_paths(tmp_path)

    # @/lib/utils should resolve from within apps/web/
    result = _resolve_alias("@/lib/utils", "apps/web/src/index.ts", tsconfig_paths, all_paths)
    assert result == "apps/web/src/lib/utils.ts"

    # @shared/ui/components/button should resolve to packages/ui/
    result = _resolve_alias("@shared/ui/components/button", "apps/web/src/index.ts", tsconfig_paths, all_paths)
    assert result == "packages/ui/src/components/button.tsx"

    # Unknown alias should return None
    result = _resolve_alias("lodash", "apps/web/src/index.ts", tsconfig_paths, all_paths)
    assert result is None


def test_resolve_ts_import_with_aliases(tmp_path):
    """Test _resolve_ts_import uses aliases for non-relative imports."""
    import json

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "utils.ts").write_text("export const x = 1;")
    tsconfig = {"compilerOptions": {"paths": {"@/*": ["./src/*"]}}}
    (tmp_path / "tsconfig.json").write_text(json.dumps(tsconfig))

    all_paths = {"src/utils.ts"}
    tsconfig_paths = _load_tsconfig_paths(tmp_path)

    # Non-relative import using alias
    result = _resolve_ts_import("@/utils", False, "src/index.ts", all_paths, tsconfig_paths)
    assert result == "src/utils.ts"

    # Relative import still works
    result = _resolve_ts_import("./utils", True, "src/index.ts", all_paths, tsconfig_paths)
    assert result == "src/utils.ts"
