"""Rank files by importance: in-degree and call count."""

from __future__ import annotations

from dataclasses import dataclass

from code_onboard.analysis.graph import DependencyGraph
from code_onboard.parsing.models import FileSummary


@dataclass
class Hotspot:
    path: str
    score: float
    in_degree: int
    call_count: int
    functions: list[str]
    classes: list[str]


def rank_hotspots(
    summaries: list[FileSummary],
    graph: DependencyGraph,
    top_n: int = 10,
) -> list[Hotspot]:
    hotspots: list[Hotspot] = []

    for s in summaries:
        in_deg = graph.in_degree(s.relative_path)
        call_count = len(s.calls)
        score = in_deg * 2 + call_count

        hotspots.append(Hotspot(
            path=s.relative_path,
            score=score,
            in_degree=in_deg,
            call_count=call_count,
            functions=[f.name for f in s.functions],
            classes=[c.name for c in s.classes],
        ))

    hotspots.sort(key=lambda h: h.score, reverse=True)
    return hotspots[:top_n]
