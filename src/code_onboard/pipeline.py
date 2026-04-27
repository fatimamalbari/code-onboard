"""Main pipeline: discovery -> parsing -> analysis -> generation."""

from __future__ import annotations

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from code_onboard.analysis.entry_points import find_entry_points
from code_onboard.analysis.graph import build_dependency_graph
from code_onboard.analysis.hotspots import rank_hotspots
from code_onboard.analysis.reading_order import suggested_reading_order
from code_onboard.config import Settings
from code_onboard.discovery.file_walker import walk_repo
from code_onboard.generation.markdown import assemble_onboarding
from code_onboard.generation.mermaid import architecture_diagram, hotspot_call_graph
from code_onboard.llm.base import create_adapter
from code_onboard.llm.context import build_llm_context
from code_onboard.parsing.parser_pool import parse_all_files


def run_pipeline(settings: Settings, console: Console) -> None:
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        disable=not settings.verbose,
    ) as progress:
        # 1. Discover files
        task = progress.add_task("Discovering files...", total=None)
        files = walk_repo(settings.repo_path, settings.max_files)
        progress.update(task, description=f"Found {len(files)} source files")
        progress.remove_task(task)

        if not files:
            console.print("[yellow]No supported source files found.[/yellow]")
            return

        # 2. Parse ASTs
        task = progress.add_task("Parsing source files...", total=None)
        file_summaries = parse_all_files(files, settings.repo_path)
        progress.update(task, description=f"Parsed {len(file_summaries)} files")
        progress.remove_task(task)

        # 3. Build dependency graph
        task = progress.add_task("Analyzing dependencies...", total=None)
        graph = build_dependency_graph(file_summaries, settings.repo_path)
        entries = find_entry_points(file_summaries, graph, settings.repo_path)
        hotspots = rank_hotspots(file_summaries, graph, settings.top_n)
        reading_path = suggested_reading_order(entries, graph, hotspots)
        progress.remove_task(task)

        # 4. Generate diagrams
        task = progress.add_task("Generating diagrams...", total=None)
        arch_diagram = architecture_diagram(graph, settings.repo_path)
        hotspot_diagram = hotspot_call_graph(hotspots, file_summaries)
        progress.remove_task(task)

        # 5. LLM narratives (optional)
        narratives: dict[str, str] = {}
        provider = settings.detect_provider()
        if provider != "none":
            task = progress.add_task(f"Generating narratives via {provider}...", total=None)
            adapter = create_adapter(settings)
            llm_context = build_llm_context(
                entries, hotspots, reading_path, graph, file_summaries, settings.repo_path
            )
            narratives = adapter.generate_narratives(llm_context)
            progress.remove_task(task)

        # 6. Assemble output
        task = progress.add_task("Writing ONBOARDING.md...", total=None)
        md = assemble_onboarding(
            entries=entries,
            hotspots=hotspots,
            reading_path=reading_path,
            arch_diagram=arch_diagram,
            hotspot_diagram=hotspot_diagram,
            file_summaries=file_summaries,
            repo_path=settings.repo_path,
            narratives=narratives,
        )
        settings.output.write_text(md, encoding="utf-8")
        progress.remove_task(task)

        # 7. HTML report (optional)
        if settings.html:
            task = progress.add_task("Generating HTML report...", total=None)
            from code_onboard.generation.html import markdown_to_html

            html_content = markdown_to_html(md)
            html_path = settings.output.with_suffix(".html")
            html_path.write_text(html_content, encoding="utf-8")
            progress.remove_task(task)

    console.print(f"[green]Onboarding guide written to {settings.output}[/green]")
    if settings.html:
        html_path = settings.output.with_suffix(".html")
        console.print(f"[green]HTML report written to {html_path}[/green]")
