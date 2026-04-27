"""Walk a repository, respecting .gitignore and skip patterns."""

from __future__ import annotations

from pathlib import Path

import pathspec

SUPPORTED_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".cs"}

ALWAYS_SKIP = {
    ".git",
    "node_modules",
    "__pycache__",
    "venv",
    ".venv",
    "env",
    ".env",
    "dist",
    "build",
    ".eggs",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    ".nox",
    ".angular",
    ".next",
    ".nuxt",
    ".svelte-kit",
    "coverage",
    "wwwroot",
    "vendor",
    "bower_components",
    ".cache",
    ".history",
    "out",
    ".output",
    "obj",
    "bin",
}


def _load_gitignore(repo_root: Path) -> pathspec.PathSpec | None:
    gitignore = repo_root / ".gitignore"
    if gitignore.is_file():
        return pathspec.PathSpec.from_lines("gitignore", gitignore.read_text().splitlines())
    return None


def walk_repo(repo_root: Path, max_files: int = 500) -> list[Path]:
    """Return source files in the repo, filtered by extension and .gitignore."""
    spec = _load_gitignore(repo_root)
    results: list[Path] = []

    for path in sorted(repo_root.rglob("*")):
        if len(results) >= max_files:
            break

        # Skip always-skip directories
        if any(part in ALWAYS_SKIP for part in path.parts):
            continue

        if not path.is_file():
            continue

        if path.suffix not in SUPPORTED_EXTENSIONS:
            continue

        # Check .gitignore
        rel = path.relative_to(repo_root)
        if spec and spec.match_file(str(rel.as_posix())):
            continue

        results.append(path)

    return results
