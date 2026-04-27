"""Generate Mermaid diagram strings from analysis data."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from code_onboard.analysis.graph import DependencyGraph
from code_onboard.analysis.hotspots import Hotspot
from code_onboard.parsing.models import FileSummary


def _sanitize_id(name: str) -> str:
    """Make a string safe for Mermaid node IDs."""
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)


def _get_directory(path: str) -> str:
    parent = str(PurePosixPath(path).parent)
    return parent if parent != "." else "(root)"


def architecture_diagram(graph: DependencyGraph, repo_root: "Path") -> str:
    """Module-level graph LR diagram. Collapse directories with >5 files."""
    # Count files per directory
    dir_file_count: dict[str, int] = {}
    for node in graph.nodes:
        d = _get_directory(node)
        dir_file_count[d] = dir_file_count.get(d, 0) + 1

    # Directories with >5 files get collapsed
    collapsed_dirs = {d for d, count in dir_file_count.items() if count > 5}

    def node_label(path: str) -> str:
        d = _get_directory(path)
        if d in collapsed_dirs:
            return d
        return path

    # Build unique edges between module-level nodes
    edges: set[tuple[str, str]] = set()
    for src in graph.nodes:
        for tgt in graph.successors(src):
            src_label = node_label(src)
            tgt_label = node_label(tgt)
            if src_label != tgt_label:
                edges.add((src_label, tgt_label))

    if not edges:
        return ""

    lines = ["graph LR"]
    seen_nodes: set[str] = set()

    for src, tgt in sorted(edges):
        src_id = _sanitize_id(src)
        tgt_id = _sanitize_id(tgt)

        if src not in seen_nodes:
            lines.append(f'    {src_id}["{src}"]')
            seen_nodes.add(src)
        if tgt not in seen_nodes:
            lines.append(f'    {tgt_id}["{tgt}"]')
            seen_nodes.add(tgt)

        lines.append(f"    {src_id} --> {tgt_id}")

    return "\n".join(lines)


def hotspot_call_graph(hotspots: list[Hotspot], summaries: list[FileSummary]) -> str:
    """Symbol-level graph TD of top hotspot functions/classes."""
    if not hotspots:
        return ""

    # Build a map of all function/class names to their file
    symbol_to_file: dict[str, str] = {}
    for s in summaries:
        for fn in s.functions:
            symbol_to_file[fn.name] = s.relative_path
        for cls in s.classes:
            symbol_to_file[cls.name] = s.relative_path

    # Build call edges: caller function -> called function (if both known)
    call_edges: set[tuple[str, str]] = set()
    hotspot_paths = {h.path for h in hotspots}

    for s in summaries:
        if s.relative_path not in hotspot_paths:
            continue
        # For each function in this hotspot file, check what it calls
        current_functions = [f.name for f in s.functions]
        called_names = {c.name for c in s.calls}

        for fn_name in current_functions:
            for called in called_names:
                if called in symbol_to_file and called != fn_name:
                    call_edges.add((fn_name, called))

    if not call_edges:
        # Fall back to file-level connections
        return _hotspot_file_diagram(hotspots)

    lines = ["graph TD"]
    seen_nodes: set[str] = set()

    for caller, callee in sorted(call_edges)[:30]:  # Cap at 30 edges
        caller_id = _sanitize_id(caller)
        callee_id = _sanitize_id(callee)

        if caller not in seen_nodes:
            file_hint = symbol_to_file.get(caller, "")
            label = f"{caller}\\n({PurePosixPath(file_hint).name})" if file_hint else caller
            lines.append(f'    {caller_id}["{label}"]')
            seen_nodes.add(caller)

        if callee not in seen_nodes:
            file_hint = symbol_to_file.get(callee, "")
            label = f"{callee}\\n({PurePosixPath(file_hint).name})" if file_hint else callee
            lines.append(f'    {callee_id}["{label}"]')
            seen_nodes.add(callee)

        lines.append(f"    {caller_id} --> {callee_id}")

    return "\n".join(lines)


def _hotspot_file_diagram(hotspots: list[Hotspot]) -> str:
    """Fallback: just list hotspot files with scores."""
    lines = ["graph TD"]
    for i, h in enumerate(hotspots):
        node_id = _sanitize_id(h.path)
        label = f"{PurePosixPath(h.path).name}\\nscore={h.score:.0f}"
        lines.append(f'    {node_id}["{label}"]')
        if i > 0:
            prev_id = _sanitize_id(hotspots[i - 1].path)
            lines.append(f"    {prev_id} -.-> {node_id}")
    return "\n".join(lines)
