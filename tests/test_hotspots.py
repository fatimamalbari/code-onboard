"""Tests for hotspot ranking."""

from pathlib import Path

from code_onboard.analysis.graph import build_dependency_graph
from code_onboard.analysis.hotspots import rank_hotspots
from code_onboard.discovery.file_walker import walk_repo
from code_onboard.parsing.parser_pool import parse_all_files

FIXTURES = Path(__file__).parent / "fixtures"


def test_hotspots_returns_ranked_list():
    root = FIXTURES / "python_sample"
    files = walk_repo(root)
    summaries = parse_all_files(files, root)
    graph = build_dependency_graph(summaries, root)
    hotspots = rank_hotspots(summaries, graph, top_n=5)

    assert len(hotspots) <= 5
    assert len(hotspots) > 0
    # Should be sorted by score descending
    scores = [h.score for h in hotspots]
    assert scores == sorted(scores, reverse=True)


def test_hotspots_have_symbols():
    root = FIXTURES / "python_sample"
    files = walk_repo(root)
    summaries = parse_all_files(files, root)
    graph = build_dependency_graph(summaries, root)
    hotspots = rank_hotspots(summaries, graph, top_n=10)

    # At least one hotspot should have functions or classes
    has_symbols = any(h.functions or h.classes for h in hotspots)
    assert has_symbols
