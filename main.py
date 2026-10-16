"""Main entrypoint for the YouTube Multi-Agent Search and MP3 Downloader.

Built using Google ADK (Agent Development Kit).
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt

# Load environment variables from .env file
load_dotenv()

from agents.coordinator import create_coordinator_agent
from tools.youtube_tools import (
    search_youtube,
    download_and_convert_to_mp3,
    parse_search_results,
)
from utils.formatter import (
    display_header,
    display_agent_banner,
    display_search_results,
    display_download_summary,
)

console = Console()


async def run_direct_multiagent_flow(
    query: str,
    auto_download_rank: Optional[int] = None,
    output_dir: str = "./downloads",
) -> None:
    """Executes the multi-agent workflow deterministically.

    1. Search Specialist searches YouTube and retrieves top 5 results.
    2. Results are formatted and displayed.
    3. User picks a video (or auto-download selects it).
    4. Converter Specialist downloads audio and converts it to MP3.
    """
    display_agent_banner("youtube_coordinator", "Received request. Delegating search task to Search Agent...")
    display_agent_banner("youtube_search_agent", f"Searching YouTube for: '[bold yellow]{query}[/bold yellow]'...")

    # Step 1: Execute YouTube search
    search_json = search_youtube(query=query, max_results=5)
    results = parse_search_results(search_json)

    if not results:
        console.print("[bold red]❌ No results found or search failed.[/bold red]")
        return

    # Step 2: Show results
    display_search_results(results)

    # Step 3: Selection
    selected_item = None
    if auto_download_rank is not None and 1 <= auto_download_rank <= len(results):
        selected_item = results[auto_download_rank - 1]
        console.print(f"\n[cyan]Auto-selected option #[bold yellow]{auto_download_rank}[/bold yellow]: {selected_item['title']}[/cyan]")
    else:
        while True:
            choice = Prompt.ask(
                "\n[bold green]Which video would you like to convert to MP3?[/bold green] (1-5, or 'q' to quit)",
                default="1",
            )
            if choice.lower() in ("q", "quit", "exit"):
                console.print("[dim]Exiting without downloading.[/dim]")
                return
            if choice.isdigit() and 1 <= int(choice) <= len(results):
                selected_item = results[int(choice) - 1]
                break
            console.print("[red]Invalid selection. Please enter a number between 1 and 5.[/red]")

    # Step 4: Downloader Specialist
    display_agent_banner(
        "youtube_coordinator",
        f"Video selected: '{selected_item['title']}'. Delegating to Converter Agent...",
    )
    display_agent_banner(
        "youtube_converter_agent",
        f"Downloading audio and converting to MP3 at [cyan]{output_dir}[/cyan]...",
    )

    with console.status("[bold green]Downloading stream and extracting audio via FFmpeg...[/bold green]", spinner="dots"):
        download_json = download_and_convert_to_mp3(
            video_url=selected_item["url"],
            output_dir=output_dir,
        )

    # Step 5: Summary
    display_download_summary(download_json)
    display_agent_banner("youtube_coordinator", "Workflow completed successfully!")


async def run_google_adk_runner(
    prompt_text: str,
    output_dir: str = "./downloads",
    model: str = "gemini-2.5-flash",
) -> None:
    """Runs the full Google ADK Agent Runner with Gemini LLM reasoning."""
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    coordinator = create_coordinator_agent(model=model)
    session_service = InMemorySessionService()

    runner = Runner(
        app_name="youtube_assistant",
        agent=coordinator,
        session_service=session_service,
        auto_create_session=True,
    )

    user_message = types.Content(
        role="user",
        parts=[types.Part.from_text(text=prompt_text)],
    )

    current_agent = ""
    console.print(f"\n[bold blue]🚀 Starting Google ADK Session with model:[/bold blue] [cyan]{model}[/cyan]\n")

    try:
        async for event in runner.run_async(
            user_id="user_default",
            session_id="session_youtube_1",
            new_message=user_message,
        ):
            # Check for agent handoffs
            if event.author and event.author != current_agent:
                current_agent = event.author
                display_agent_banner(current_agent, "handling turn...")

            # Check for tool / function calls
            function_calls = event.get_function_calls()
            if function_calls:
                for fc in function_calls:
                    console.print(f"[bold yellow]🛠️  Tool Invocated:[/bold yellow] [magenta]{fc.name}[/magenta] with arguments: {fc.args}")

            # Check for text responses
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        console.print(part.text, end="", highlight=True)

        console.print("\n")
    except Exception as exc:
        console.print(f"\n[bold red]Error in Google ADK Runner:[/bold red] {exc}")
        if "API key" in str(exc):
            console.print("[yellow]Falling back to direct multi-agent pipeline...[/yellow]")
            await run_direct_multiagent_flow(prompt_text, output_dir=output_dir)


def check_api_key() -> bool:
    """Checks whether GEMINI_API_KEY is configured."""
    return bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))


def print_api_key_help() -> None:
    """Prints instructions for obtaining and configuring a Gemini API key."""
    console.print("\n[bold yellow]💡 API Key Information:[/bold yellow]")
    console.print("To run with autonomous Gemini LLM reasoning, configure your [bold cyan]GEMINI_API_KEY[/bold cyan].")
    console.print("1. Get a free API key at Google AI Studio: [blue underline]https://aistudio.google.com/app/api-keys[/blue underline]")
    console.print("2. Set it in your environment: [green]export GEMINI_API_KEY=\"your_key_here\"[/green]")
    console.print("   OR copy [cyan].env.example[/cyan] to [cyan].env[/cyan] and paste your key.\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Multi-Agent YouTube Search and MP3 Downloader powered by Google ADK.",
    )
    parser.add_argument(
        "-q", "--query",
        type=str,
        default="",
        help="Search query for YouTube (e.g., 'ambient chill beats').",
    )
    parser.add_argument(
        "-d", "--auto-download",
        type=int,
        choices=[1, 2, 3, 4, 5],
        default=None,
        help="Automatically convert and download the result at this rank (1-5).",
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default="./downloads",
        help="Directory to save downloaded MP3 files (default: ./downloads).",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default="gemini-2.5-flash",
        help="Gemini model identifier (default: gemini-2.5-flash).",
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Run via direct multi-agent pipeline (bypasses LLM reasoning).",
    )
    return parser.parse_args()


async def main_async() -> None:
    args = parse_args()
    display_header()

    query = args.query.strip()
    has_key = check_api_key()

    if not has_key:
        print_api_key_help()

    if not query:
        console.print("[bold cyan]Welcome to the Multi-Agent YouTube Downloader![/bold cyan]")
        query = Prompt.ask("[bold green]Enter your YouTube search query[/bold green]")
        if not query.strip():
            console.print("[red]No query entered. Exiting.[/red]")
            return

    # Decide execution mode
    if args.direct or not has_key:
        await run_direct_multiagent_flow(
            query=query,
            auto_download_rank=args.auto_download,
            output_dir=args.output_dir,
        )
    else:
        # Full Google ADK Runner with Gemini model
        download_intent = ""
        if args.auto_download:
            download_intent = f" and convert/download result #{args.auto_download} as MP3"
        prompt_text = f"Search YouTube for '{query}', show top 5 results{download_intent}."
        await run_google_adk_runner(
            prompt_text=prompt_text,
            output_dir=args.output_dir,
            model=args.model,
        )


def main() -> None:
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        console.print("\n[dim]Process interrupted by user. Goodbye![/dim]")
        sys.exit(0)


if __name__ == "__main__":
    main()
