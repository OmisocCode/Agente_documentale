"""
Command-line interface for PDF Math Agent.
"""

import sys
from pathlib import Path

import click

from src.utils.logger import get_logger
from src.workflow import PDFSummarizerWorkflow

logger = get_logger(__name__)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    PDF Math Agent - Generate HTML summaries from mathematical PDFs.

    Examples:
        pdf-math-agent process document.pdf
        pdf-math-agent resume 20240109_143022_abc123
    """
    pass


@cli.command()
@click.argument("pdf_path", type=click.Path(exists=True))
@click.option(
    "--type",
    "pdf_type",
    default="auto",
    type=click.Choice(["auto", "latex_compiled", "scanned", "handwritten"]),
    help="PDF type (auto-detects if not specified)",
)
@click.option(
    "--theme",
    "css_theme",
    default="math-document",
    type=click.Choice(["math-document", "lecture-notes", "presentation"]),
    help="CSS theme for HTML output",
)
@click.option(
    "--provider",
    "llm_provider",
    default="groq",
    type=click.Choice(["groq", "anthropic", "openai"]),
    help="LLM provider",
)
@click.option(
    "--no-checkpoints",
    is_flag=True,
    help="Disable checkpoint saving",
)
@click.option(
    "--output",
    "-o",
    "output_override",
    type=click.Path(),
    help="Override output directory",
)
def process(
    pdf_path: str,
    pdf_type: str,
    css_theme: str,
    llm_provider: str,
    no_checkpoints: bool,
    output_override: str,
):
    """
    Process a PDF and generate HTML summary.

    Examples:
        pdf-math-agent process document.pdf
        pdf-math-agent process paper.pdf --type latex_compiled --theme lecture-notes
        pdf-math-agent process book.pdf --provider groq --no-checkpoints
    """
    click.echo("=" * 60)
    click.echo("PDF Math Agent - Processing PDF")
    click.echo("=" * 60)
    click.echo(f"Input: {pdf_path}")
    click.echo(f"Type: {pdf_type}")
    click.echo(f"Theme: {css_theme}")
    click.echo(f"Provider: {llm_provider}")
    click.echo("=" * 60)

    try:
        # Create workflow
        workflow = PDFSummarizerWorkflow(
            llm_provider=llm_provider,
            css_theme=css_theme,
            enable_checkpoints=not no_checkpoints,
        )

        # Run workflow
        output_dir = workflow.run(
            pdf_path=pdf_path,
            pdf_type=pdf_type,
        )

        click.echo()
        click.secho("✓ Success!", fg="green", bold=True)
        click.echo(f"HTML generated in: {output_dir}")
        click.echo()
        click.echo("Open index.html to view the summary:")
        click.echo(f"  file://{Path(output_dir).absolute()}/index.html")

    except Exception as e:
        click.secho(f"✗ Error: {e}", fg="red", bold=True)
        logger.exception("Processing failed")
        sys.exit(1)


@cli.command()
@click.argument("session_id")
@click.option(
    "--provider",
    "llm_provider",
    default="groq",
    type=click.Choice(["groq", "anthropic", "openai"]),
    help="LLM provider",
)
@click.option(
    "--theme",
    "css_theme",
    default="math-document",
    type=click.Choice(["math-document", "lecture-notes", "presentation"]),
    help="CSS theme for HTML output",
)
def resume(session_id: str, llm_provider: str, css_theme: str):
    """
    Resume processing from a checkpoint.

    Examples:
        pdf-math-agent resume 20240109_143022_abc123
    """
    click.echo("=" * 60)
    click.echo("PDF Math Agent - Resuming from Checkpoint")
    click.echo("=" * 60)
    click.echo(f"Session: {session_id}")
    click.echo("=" * 60)

    try:
        # Create workflow
        workflow = PDFSummarizerWorkflow(
            llm_provider=llm_provider,
            css_theme=css_theme,
            enable_checkpoints=True,
        )

        # Resume workflow
        output_dir = workflow.resume(session_id=session_id)

        click.echo()
        click.secho("✓ Success!", fg="green", bold=True)
        click.echo(f"HTML generated in: {output_dir}")

    except Exception as e:
        click.secho(f"✗ Error: {e}", fg="red", bold=True)
        logger.exception("Resume failed")
        sys.exit(1)


@cli.command("list-checkpoints")
@click.option(
    "--session",
    "session_filter",
    help="Filter by session ID",
)
def list_checkpoints(session_filter: str):
    """
    List available checkpoints.

    Examples:
        pdf-math-agent list-checkpoints
        pdf-math-agent list-checkpoints --session 20240109
    """
    from src.utils.checkpoint_manager import get_checkpoint_manager

    manager = get_checkpoint_manager()
    checkpoints = manager.list_checkpoints(session_id=session_filter)

    if not checkpoints:
        click.echo("No checkpoints found")
        return

    click.echo(f"Found {len(checkpoints)} checkpoint(s):")
    click.echo()

    for cp in checkpoints:
        click.echo(f"Session: {cp['session_id']}")
        click.echo(f"  Task: {cp['task'] or 'latest'}")
        click.echo(f"  Saved: {cp['saved_at']}")
        click.echo(f"  File: {cp['file']}")
        click.echo()


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
