"""YouTube Search Agent using Google ADK."""

from __future__ import annotations

from google.adk import Agent
from tools.youtube_tools import search_youtube

SEARCH_AGENT_INSTRUCTION = """\
You are the YouTube Search Specialist Agent. Your primary role is to search YouTube for videos matching the user's intent and retrieve the top 5 results using the `search_youtube` tool.

INSTRUCTIONS:
1. When you receive a search query from the user or the coordinator agent, call `search_youtube(query=..., max_results=5)`.
2. Format the top 5 results clearly:
   - Rank (1 to 5)
   - Title
   - Channel / Uploader
   - Duration
   - Views
   - Full YouTube URL
3. Offer the results to the user and prompt them to select which video they would like to download and convert to MP3.
4. If the user already specified which video they want downloaded (e.g., 'download the first result'), provide the results and transfer or yield to the `youtube_converter_agent` with the selected video URL or ID.
"""


def create_search_agent(model: str = "gemini-2.5-flash") -> Agent:
    """Creates and returns the YouTube Search Agent.

    Args:
        model: Gemini model identifier (default: gemini-2.5-flash).

    Returns:
        A Google ADK Agent instance configured for YouTube searching.
    """
    return Agent(
        name="youtube_search_agent",
        description="Specialist agent that searches YouTube and retrieves the top 5 video results with complete metadata.",
        model=model,
        instruction=SEARCH_AGENT_INSTRUCTION,
        tools=[search_youtube],
    )
