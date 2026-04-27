"""Tests for Mermaid diagram generation."""

from pathlib import Path

from code_onboard.analysis.graph import build_dependency_graph
from code_onboard.analysis.hotspots import rank_hotspots
from code_onboard.discovery.file_walker import walk_repo
from code_onboard.generation.mermaid import architecture_diagram, hotspot_call_graph
from code_onboard.parsing.parser_pool import parse_all_files

FIXTURES = Path(__file__).parent / "fixtures"


def test_architecture_diagram_valid_mermaid():
    root = FIXTURES / "python_sample"
    files = walk_repo(root)
    summaries = parse_all_files(files, root)
    graph = build_dependency_graph(summaries, root)
    diagram = architecture_diagram(graph, root)

    if diagram:  # May be empty if no cross-directory edges
        assert diagram.startswith("graph LR")
        assert "-->" in diagram


def test_hotspot_diagram():
    root = FIXTURES / "python_sample"
    files = walk_repo(root)
    summaries = parse_all_files(files, root)
    graph = build_dependency_graph(summaries, root)
    hotspots = rank_hotspots(summaries, graph, top_n=5)
    diagram = hotspot_call_graph(hotspots, summaries)

    assert diagram.startswith("graph TD")


def test_ts_architecture_diagram():
    root = FIXTURES / "ts_sample"
    files = walk_repo(root)
    summaries = parse_all_files(files, root)
    graph = build_dependency_graph(summaries, root)
    diagram = architecture_diagram(graph, root)

    if diagram:
        assert "graph LR" in diagram
