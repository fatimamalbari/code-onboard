"""Generate a suggested reading order via BFS from entry points."""

from __future__ import annotations

from collections import deque

from code_onboard.analysis.entry_points import EntryPoint
from code_onboard.analysis.graph import DependencyGraph
from code_onboard.analysis.hotspots import Hotspot


def suggested_reading_order(
    entries: list[EntryPoint],
    graph: DependencyGraph,
    hotspots: list[Hotspot],
) -> list[str]:
    """BFS from entry points, prioritizing hotspots."""
    visited: set[str] = set()
    order: list[str] = []
    hotspot_set = {h.path for h in hotspots}

    # Start BFS from each entry point
    queue: deque[str] = deque()
    for ep in entries:
        if ep.path in graph.nodes and ep.path not in visited:
            queue.append(ep.path)
            visited.add(ep.path)

    while queue:
        current = queue.popleft()
        order.append(current)

        # Get successors, prioritize hotspots
        successors = list(graph.successors(current))
        successors.sort(key=lambda s: (s not in hotspot_set, s))

        for succ in successors:
            if succ not in visited:
                visited.add(succ)
                queue.append(succ)

    # Add remaining hotspots not yet visited
    for h in hotspots:
        if h.path not in visited:
            order.append(h.path)
            visited.add(h.path)

    return order
