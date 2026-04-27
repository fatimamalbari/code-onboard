"""Detect entry points: __main__, main guards, package.json, framework routes, zero-in-degree files."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from code_onboard.analysis.graph import DependencyGraph
from code_onboard.parsing.models import FileSummary

# Test file patterns — these are never real entry points
_TEST_PATTERNS = re.compile(
    r"\.(spec|test|e2e|cy)\.(ts|tsx|js|jsx)$"
    r"|/__tests__/"
    r"|/test/"
    r"|\.stories\.(ts|tsx|js|jsx)$"
)


def _is_test_file(path: str) -> bool:
    return bool(_TEST_PATTERNS.search(path))


# Next.js App Router conventions
_NEXTJS_PAGE_PATTERNS = {
    "page.tsx": "Next.js page component",
    "page.ts": "Next.js page component",
    "page.jsx": "Next.js page component",
    "page.js": "Next.js page component",
    "layout.tsx": "Next.js layout component",
    "layout.ts": "Next.js layout component",
    "layout.jsx": "Next.js layout component",
    "layout.js": "Next.js layout component",
    "route.tsx": "Next.js API route",
    "route.ts": "Next.js API route",
    "loading.tsx": "Next.js loading UI",
    "error.tsx": "Next.js error boundary",
    "not-found.tsx": "Next.js 404 page",
    "middleware.ts": "Next.js middleware",
    "middleware.js": "Next.js middleware",
}


def _infer_nextjs_route(relative_path: str) -> str | None:
    """Infer the URL route from a Next.js App Router file path."""
    parts = PurePosixPath(relative_path).parts
    # Find "app" directory
    try:
        app_idx = list(parts).index("app")
    except ValueError:
        return None
    # Route segments are between "app" and the filename
    route_parts = []
    for p in parts[app_idx + 1: -1]:
        # Route groups like (protected) are not in the URL
        if p.startswith("(") and p.endswith(")"):
            continue
        route_parts.append(p)
    route = "/" + "/".join(route_parts) if route_parts else "/"
    return route


@dataclass
class EntryPoint:
    path: str
    kind: str
    description: str


def find_entry_points(
    summaries: list[FileSummary],
    graph: DependencyGraph,
    repo_root: Path,
) -> list[EntryPoint]:
    entries: list[EntryPoint] = []
    seen: set[str] = set()

    # Python: __main__.py files
    for s in summaries:
        if s.path.name == "__main__.py":
            entries.append(EntryPoint(
                path=s.relative_path,
                kind="__main__",
                description=f"Package entry point ({s.path.parent.name})",
            ))
            seen.add(s.relative_path)

    # Python: if __name__ == "__main__" guard
    for s in summaries:
        if s.has_main_guard and s.relative_path not in seen:
            entries.append(EntryPoint(
                path=s.relative_path,
                kind="main_guard",
                description="Has `if __name__ == '__main__'` guard",
            ))
            seen.add(s.relative_path)

    # JS/TS: package.json main/bin
    pkg_json = repo_root / "package.json"
    if pkg_json.is_file():
        try:
            pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
            for field_name in ("main", "module"):
                if field_name in pkg:
                    val = pkg[field_name]
                    entries.append(EntryPoint(
                        path=val,
                        kind="package_json",
                        description=f"package.json {field_name}",
                    ))
                    seen.add(val)
            if "bin" in pkg:
                bins = pkg["bin"]
                if isinstance(bins, str):
                    bins = {"default": bins}
                for name, bpath in bins.items():
                    if bpath not in seen:
                        entries.append(EntryPoint(
                            path=bpath,
                            kind="bin",
                            description=f"CLI binary: {name}",
                        ))
                        seen.add(bpath)
        except (json.JSONDecodeError, KeyError):
            pass

    # Next.js App Router: page.tsx, layout.tsx, route.ts, etc.
    for s in summaries:
        if s.relative_path in seen:
            continue
        filename = s.path.name
        if filename in _NEXTJS_PAGE_PATTERNS:
            route = _infer_nextjs_route(s.relative_path)
            desc = _NEXTJS_PAGE_PATTERNS[filename]
            if route:
                desc += f" → `{route}`"
            entries.append(EntryPoint(
                path=s.relative_path,
                kind="nextjs_route",
                description=desc,
            ))
            seen.add(s.relative_path)

    # Zero in-degree files (nothing imports them) — exclude test files
    for s in summaries:
        if s.relative_path in seen:
            continue
        if _is_test_file(s.relative_path):
            continue
        if graph.in_degree(s.relative_path) == 0 and graph.out_degree(s.relative_path) > 0:
            entries.append(EntryPoint(
                path=s.relative_path,
                kind="zero_in_degree",
                description="No other file imports this (potential entry point)",
            ))
            seen.add(s.relative_path)

    return entries
