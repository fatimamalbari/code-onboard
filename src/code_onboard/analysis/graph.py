"""In-memory dependency graph built from import statements."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from code_onboard.parsing.models import FileSummary


@dataclass
class DependencyGraph:
    """Adjacency list graph: nodes = relative file paths, edges = imports."""
    nodes: set[str] = field(default_factory=set)
    # edges[source] = set of targets that source imports
    edges: dict[str, set[str]] = field(default_factory=lambda: dict())
    # reverse: who imports this file
    reverse_edges: dict[str, set[str]] = field(default_factory=lambda: dict())

    def add_edge(self, source: str, target: str) -> None:
        self.edges.setdefault(source, set()).add(target)
        self.reverse_edges.setdefault(target, set()).add(source)

    def in_degree(self, node: str) -> int:
        return len(self.reverse_edges.get(node, set()))

    def out_degree(self, node: str) -> int:
        return len(self.edges.get(node, set()))

    def successors(self, node: str) -> set[str]:
        return self.edges.get(node, set())

    def predecessors(self, node: str) -> set[str]:
        return self.reverse_edges.get(node, set())


def _resolve_python_import(module: str, is_relative: bool, source_path: str, all_paths: set[str]) -> str | None:
    """Try to resolve a Python import to a file in the repo."""
    if is_relative:
        source_dir = str(PurePosixPath(source_path).parent)
        candidate = f"{source_dir}/{module.replace('.', '/')}.py"
        if candidate in all_paths:
            return candidate
        candidate = f"{source_dir}/{module.replace('.', '/')}/__init__.py"
        if candidate in all_paths:
            return candidate

    # Absolute import
    candidate = f"{module.replace('.', '/')}.py"
    if candidate in all_paths:
        return candidate
    candidate = f"{module.replace('.', '/')}/__init__.py"
    if candidate in all_paths:
        return candidate

    # Try src/ prefix
    candidate = f"src/{module.replace('.', '/')}.py"
    if candidate in all_paths:
        return candidate
    candidate = f"src/{module.replace('.', '/')}/__init__.py"
    if candidate in all_paths:
        return candidate

    return None


def _normalize_posix_path(raw: str) -> str:
    """Normalize a POSIX path by resolving . and .. segments."""
    parts: list[str] = []
    for part in raw.split("/"):
        if part == "." or part == "":
            continue
        elif part == ".." and parts:
            parts.pop()
        else:
            parts.append(part)
    return "/".join(parts) if parts else "."


def _try_extensions(base: str, all_paths: set[str]) -> str | None:
    """Try common TS/JS extensions for a base path."""
    for ext in ("", ".ts", ".tsx", ".js", ".jsx", "/index.ts", "/index.tsx", "/index.js", "/index.jsx"):
        candidate = base + ext
        if candidate in all_paths:
            return candidate
    return None


# Type: maps a directory prefix (e.g. "apps/dashboard") to a list of
# (alias_pattern, resolved_base_paths) tuples.
# alias_pattern is like "@/*" or "@uzera-shared/ui/*"
# resolved_base_paths are absolute-in-repo paths like ["apps/dashboard/src"]
TsconfigPaths = dict[str, list[tuple[str, list[str]]]]


def _load_tsconfig_paths(repo_root: Path) -> TsconfigPaths:
    """Scan for tsconfig.json files and extract path alias mappings.

    Returns a dict mapping directory prefixes (relative to repo root)
    to their path alias rules. Also handles baseUrl for non-relative imports.
    """
    result: TsconfigPaths = {}

    for tsconfig_file in repo_root.rglob("tsconfig*.json"):
        # Skip node_modules
        rel = tsconfig_file.relative_to(repo_root).as_posix()
        if "node_modules" in rel:
            continue

        try:
            text = tsconfig_file.read_text(encoding="utf-8")
            data = json.loads(text)
        except (json.JSONDecodeError, OSError):
            continue

        compiler_opts = data.get("compilerOptions", {})
        paths = compiler_opts.get("paths")
        base_url = compiler_opts.get("baseUrl")

        if not paths and not base_url:
            continue

        tsconfig_dir = tsconfig_file.parent.relative_to(repo_root).as_posix()
        if tsconfig_dir == ".":
            tsconfig_dir = ""

        # Resolve baseUrl relative to tsconfig directory
        resolved_base_url = ""
        if base_url:
            if tsconfig_dir:
                raw_base = f"{tsconfig_dir}/{base_url}"
            else:
                raw_base = base_url
            resolved_base_url = _normalize_posix_path(raw_base)

        alias_rules: list[tuple[str, list[str]]] = []

        if paths:
            for alias_pattern, targets in paths.items():
                resolved_targets: list[str] = []
                for target in targets:
                    # Resolve target relative to baseUrl if set, else tsconfig directory
                    if resolved_base_url:
                        raw = f"{resolved_base_url}/{target}"
                    elif tsconfig_dir:
                        raw = f"{tsconfig_dir}/{target}"
                    else:
                        raw = target
                    # Remove trailing /* from the target
                    if raw.endswith("/*"):
                        raw = raw[:-2]
                    resolved = _normalize_posix_path(raw)
                    resolved_targets.append(resolved)
                alias_rules.append((alias_pattern, resolved_targets))

        # baseUrl enables bare imports (e.g. "components/Button" resolves to baseUrl/components/Button)
        if resolved_base_url:
            alias_rules.append(("__baseUrl__", [resolved_base_url]))

        if alias_rules:
            result[tsconfig_dir] = alias_rules

    return result


def _resolve_alias(module: str, source_path: str, tsconfig_paths: TsconfigPaths, all_paths: set[str]) -> str | None:
    """Try to resolve a non-relative TS import via tsconfig path aliases and baseUrl."""
    # Find the most specific tsconfig that covers this source file
    best_prefix = ""
    best_rules: list[tuple[str, list[str]]] = []

    for dir_prefix, rules in tsconfig_paths.items():
        if dir_prefix == "" or source_path.startswith(dir_prefix + "/"):
            if len(dir_prefix) > len(best_prefix):
                best_prefix = dir_prefix
                best_rules = rules

    if not best_rules:
        # Fall back to root tsconfig if present
        best_rules = tsconfig_paths.get("", [])

    base_url_bases: list[str] = []

    for alias_pattern, resolved_bases in best_rules:
        # Stash baseUrl for fallback
        if alias_pattern == "__baseUrl__":
            base_url_bases = resolved_bases
            continue

        if alias_pattern.endswith("/*"):
            # Wildcard: @/* matches @/foo/bar -> capture "foo/bar"
            prefix = alias_pattern[:-2]
            if module.startswith(prefix + "/"):
                remainder = module[len(prefix) + 1:]
                for base in resolved_bases:
                    candidate_base = f"{base}/{remainder}"
                    result = _try_extensions(candidate_base, all_paths)
                    if result:
                        return result
        elif alias_pattern == module:
            # Exact match: @uzera-shared/ui -> packages/ui/src
            for base in resolved_bases:
                result = _try_extensions(base, all_paths)
                if result:
                    return result

    # Fallback: try baseUrl for bare imports (e.g. "components/Button")
    for base in base_url_bases:
        candidate_base = f"{base}/{module}"
        result = _try_extensions(candidate_base, all_paths)
        if result:
            return result

    return None


def _resolve_ts_import(
    module: str,
    is_relative: bool,
    source_path: str,
    all_paths: set[str],
    tsconfig_paths: TsconfigPaths | None = None,
) -> str | None:
    """Try to resolve a TS/JS import to a file in the repo."""
    if is_relative:
        source_dir = PurePosixPath(source_path).parent
        resolved = (source_dir / module).as_posix()
        base = _normalize_posix_path(resolved)
        return _try_extensions(base, all_paths)

    # Non-relative: try tsconfig path aliases
    if tsconfig_paths:
        return _resolve_alias(module, source_path, tsconfig_paths, all_paths)

    return None


def _resolve_csharp_using(module: str, all_paths: set[str], namespace_map: dict[str, list[str]]) -> list[str]:
    """Resolve a C# using directive to files that declare that namespace."""
    return namespace_map.get(module, [])


def _build_csharp_namespace_map(summaries: list[FileSummary]) -> dict[str, list[str]]:
    """Build a map of C# namespace -> list of files that belong to it.

    We infer namespace from the file path and project naming conventions.
    E.g. src/Uzera.Platform.Domain/Data/Foo.cs -> Uzera.Platform.Domain.Data
    """
    ns_map: dict[str, list[str]] = {}
    for s in summaries:
        if s.language != "c_sharp":
            continue
        # Try to read namespace from imports — the file's own using statements
        # won't tell us its namespace, but the directory structure will.
        parts = PurePosixPath(s.relative_path).parts
        # Find the project folder (contains dots like Uzera.Platform.Domain)
        project_ns = ""
        remaining: list[str] = []
        for i, part in enumerate(parts):
            if "." in part and not part.endswith(".cs"):
                project_ns = part
                remaining = [p for p in parts[i + 1:] if not p.endswith(".cs")]
                break
        if project_ns:
            ns = project_ns
            if remaining:
                ns += "." + ".".join(remaining)
            ns_map.setdefault(ns, []).append(s.relative_path)
            # Also register the project root namespace
            if remaining:
                ns_map.setdefault(project_ns, []).append(s.relative_path)

    return ns_map


def build_dependency_graph(summaries: list[FileSummary], repo_root: Path) -> DependencyGraph:
    graph = DependencyGraph()
    all_paths = {s.relative_path for s in summaries}
    csharp_ns_map = _build_csharp_namespace_map(summaries)
    tsconfig_paths = _load_tsconfig_paths(repo_root)

    for s in summaries:
        graph.nodes.add(s.relative_path)

    for s in summaries:
        for imp in s.imports:
            if s.language == "python":
                target = _resolve_python_import(imp.module, imp.is_relative, s.relative_path, all_paths)
                if target and target != s.relative_path:
                    graph.add_edge(s.relative_path, target)
            elif s.language == "c_sharp":
                targets = _resolve_csharp_using(imp.module, all_paths, csharp_ns_map)
                for target in targets:
                    if target != s.relative_path:
                        graph.add_edge(s.relative_path, target)
            else:
                target = _resolve_ts_import(
                    imp.module, imp.is_relative, s.relative_path, all_paths, tsconfig_paths
                )
                if target and target != s.relative_path:
                    graph.add_edge(s.relative_path, target)

    return graph
