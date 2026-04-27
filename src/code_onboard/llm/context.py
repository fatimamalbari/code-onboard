"""Build structured JSON context for LLM prompts (never send raw source)."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

from code_onboard.analysis.entry_points import EntryPoint
from code_onboard.analysis.graph import DependencyGraph
from code_onboard.analysis.hotspots import Hotspot
from code_onboard.parsing.models import FileSummary


def build_llm_context(
    entries: list[EntryPoint],
    hotspots: list[Hotspot],
    reading_order: list[str],
    graph: DependencyGraph,
    summaries: list[FileSummary],
    repo_root: Path,
) -> dict[str, str]:
    """Return JSON strings for each prompt section."""

    # Entry points
    entry_data = [
        {"path": ep.path, "kind": ep.kind, "description": ep.description}
        for ep in entries
    ]

    # Architecture: directory-level module map with dependencies
    dir_deps: dict[str, dict] = {}
    for s in summaries:
        d = str(PurePosixPath(s.relative_path).parent)
        if d == ".":
            d = "(root)"
        if d not in dir_deps:
            dir_deps[d] = {"files": 0, "functions": 0, "imports_from": set()}
        dir_deps[d]["files"] += 1
        dir_deps[d]["functions"] += len(s.functions)

        for tgt in graph.successors(s.relative_path):
            tgt_dir = str(PurePosixPath(tgt).parent)
            if tgt_dir == ".":
                tgt_dir = "(root)"
            if tgt_dir != d:
                dir_deps[d]["imports_from"].add(tgt_dir)

    arch_data = {
        d: {"files": info["files"], "functions": info["functions"],
            "depends_on": sorted(info["imports_from"])}
        for d, info in sorted(dir_deps.items())
    }

    # Hotspots
    hotspot_data = [
        {"path": h.path, "score": h.score, "in_degree": h.in_degree,
         "call_count": h.call_count, "key_symbols": h.classes[:3] + h.functions[:5]}
        for h in hotspots
    ]

    # Module map summary
    module_data: dict[str, dict] = {}
    for s in summaries:
        d = str(PurePosixPath(s.relative_path).parent)
        if d == ".":
            d = "(root)"
        if d not in module_data:
            module_data[d] = {"files": [], "total_lines": 0}
        module_data[d]["files"].append(s.relative_path)
        module_data[d]["total_lines"] += s.line_count

    # Module responsibilities: richer data for LLM
    module_resp: dict[str, dict] = {}
    for s in summaries:
        d = str(PurePosixPath(s.relative_path).parent)
        if d == ".":
            d = "(root)"
        if d not in module_resp:
            module_resp[d] = {
                "files": 0,
                "key_functions": [],
                "key_classes": [],
                "depends_on": set(),
                "depended_on_by": set(),
            }
        module_resp[d]["files"] += 1
        module_resp[d]["key_functions"].extend(f.name for f in s.functions[:3])
        module_resp[d]["key_classes"].extend(c.name for c in s.classes[:2])

        for tgt in graph.successors(s.relative_path):
            tgt_dir = str(PurePosixPath(tgt).parent)
            if tgt_dir == ".":
                tgt_dir = "(root)"
            if tgt_dir != d:
                module_resp[d]["depends_on"].add(tgt_dir)

        for src in graph.predecessors(s.relative_path):
            src_dir = str(PurePosixPath(src).parent)
            if src_dir == ".":
                src_dir = "(root)"
            if src_dir != d:
                module_resp[d]["depended_on_by"].add(src_dir)

    module_resp_data = {
        d: {
            "files": info["files"],
            "key_functions": info["key_functions"][:5],
            "key_classes": info["key_classes"][:3],
            "depends_on": sorted(info["depends_on"]),
            "used_by_count": len(info["depended_on_by"]),
        }
        for d, info in sorted(module_resp.items())
    }

    return {
        "entry_points_json": json.dumps(entry_data, indent=2),
        "architecture_json": json.dumps(arch_data, indent=2),
        "hotspots_json": json.dumps(hotspot_data, indent=2),
        "reading_order_json": json.dumps(reading_order, indent=2),
        "module_map_json": json.dumps(
            {d: {"file_count": len(info["files"]), "total_lines": info["total_lines"]}
             for d, info in sorted(module_data.items())},
            indent=2,
        ),
        "module_responsibilities_json": json.dumps(module_resp_data, indent=2),
    }
