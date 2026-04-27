"""Click CLI entry point."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console

from code_onboard import __version__
from code_onboard.config import Settings

console = Console()


@click.command()
@click.argument("repo_path", default=".", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", default="ONBOARDING.md", type=click.Path(path_type=Path), help="Output file path.")
@click.option("-n", "--top-n", default=10, type=int, help="Number of hotspots to show.")
@click.option("--max-files", default=500, type=int, help="Max files to analyze.")
@click.option("--provider", default="auto", help='"openai" | "anthropic" | "none" | "auto"')
@click.option("--model", default=None, help="Override model name.")
@click.option("--no-llm", is_flag=True, help="Skip LLM, analysis-only output.")
@click.option("--html", is_flag=True, help="Also generate an HTML report with rendered Mermaid diagrams.")
@click.option("-v", "--verbose", is_flag=True, help="Show progress details.")
@click.version_option(version=__version__)
def main(
    repo_path: Path,
    output: Path,
    top_n: int,
    max_files: int,
    provider: str,
    model: str | None,
    no_llm: bool,
    html: bool,
    verbose: bool,
) -> None:
    """Analyze a git repo and generate a newcomer-friendly ONBOARDING.md guide."""
    resolved = repo_path.resolve()
    if not resolved.is_dir():
        console.print(f"[red]Error: '{repo_path}' is not a directory.[/red]")
        raise SystemExit(1)

    settings = Settings(
        repo_path=resolved,
        output=output,
        top_n=top_n,
        max_files=max_files,
        provider=provider,
        model=model,
        no_llm=no_llm,
        html=html,
        verbose=verbose,
    )

    from code_onboard.pipeline import run_pipeline

    try:
        run_pipeline(settings, console)
    except KeyboardInterrupt:
        console.print("\n[yellow]Aborted.[/yellow]")
        raise SystemExit(130)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            console.print_exception()
        raise SystemExit(1)
