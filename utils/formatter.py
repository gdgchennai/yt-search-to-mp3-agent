"""Console formatting utilities using Rich."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Union

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()


def display_header(title: str = "YouTube Multi-Agent Downloader", subtitle: str = "Powered by Google ADK (Agent Development Kit)") -> None:
    """Displays a stylized header for the application."""
    header_text = Text()
    header_text.append(f"🎧  {title}  🎧\n", style="bold cyan")
    header_text.append(subtitle, style="dim italic white")
    console.print(Panel(header_text, border_style="cyan", expand=False))


def display_agent_banner(agent_name: str, action_desc: str) -> None:
    """Displays a tag indicating which agent is currently active."""
    colors = {
        "youtube_coordinator": "bold blue",
        "youtube_search_agent": "bold magenta",
        "youtube_converter_agent": "bold green",
    }
    color = colors.get(agent_name, "bold yellow")
    console.print(f"\n[{color}]🤖 [{agent_name}][/{color}] {action_desc}")


def display_search_results(results_input: Union[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Displays a beautifully formatted table of YouTube search results.

    Args:
        results_input: Either a JSON string or a list of result dictionaries.

    Returns:
        The parsed list of video items.
    """
    if isinstance(results_input, str):
        try:
            results = json.loads(results_input)
        except Exception:
            console.print(f"[red]Failed to parse results: {results_input}[/red]")
            return []
    else:
        results = results_input

    if not isinstance(results, list) or not results:
        console.print("[yellow]⚠️  No search results to display.[/yellow]")
        return []

    table = Table(
        title="🔍 Top YouTube Search Results",
        header_style="bold cyan",
        border_style="dim",
        show_lines=True,
    )

    table.add_column("#", justify="center", style="bold yellow", width=4)
    table.add_column("Title", style="bold white", min_width=35)
    table.add_column("Channel", style="magenta", width=20)
    table.add_column("Duration", justify="center", style="green", width=10)
    table.add_column("Views", justify="right", style="cyan", width=14)
    table.add_column("URL", style="blue underline", overflow="fold")

    for item in results:
        rank = str(item.get("rank", ""))
        title = item.get("title", "Unknown Title")
        channel = item.get("channel", "Unknown Channel")
        duration = str(item.get("duration", "N/A"))
        views = str(item.get("views", "N/A"))
        url = item.get("url", "")

        table.add_row(rank, title, channel, duration, views, url)

    console.print(table)
    return results


def display_download_summary(download_result: Union[str, Dict[str, Any]]) -> None:
    """Displays a formatted summary panel of a completed MP3 download."""
    if isinstance(download_result, str):
        try:
            data = json.loads(download_result)
        except Exception:
            console.print(f"[bold green]Download Output:[/bold green] {download_result}")
            return
    else:
        data = download_result

    status = data.get("status", "unknown")
    if status == "success":
        title = data.get("title", "Unknown")
        file_path = data.get("file_path", "")
        file_size_mb = data.get("file_size_mb", 0)
        duration = data.get("duration", "N/A")

        summary_text = Text()
        summary_text.append("🎉 MP3 Conversion & Download Successful!\n\n", style="bold green")
        summary_text.append("🎵 Title: ", style="bold white")
        summary_text.append(f"{title}\n", style="cyan")
        summary_text.append("⏱️  Duration: ", style="bold white")
        summary_text.append(f"{duration}\n", style="yellow")
        summary_text.append("📦 File Size: ", style="bold white")
        summary_text.append(f"{file_size_mb} MB\n", style="yellow")
        summary_text.append("📁 Saved Path: ", style="bold white")
        summary_text.append(f"{file_path}\n", style="bold cyan underline")

        console.print(Panel(summary_text, title="[bold green]Download Complete[/bold green]", border_style="green"))
    else:
        err_msg = data.get("message", "An error occurred during download.")
        console.print(Panel(f"[bold red]❌ Download Error:[/bold red]\n{err_msg}", border_style="red"))
