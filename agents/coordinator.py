"""YouTube Multi-Agent Coordinator using Google ADK."""

from __future__ import annotations

from google.adk import Agent
from agents.search_agent import create_search_agent
from agents.converter_agent import create_converter_agent

COORDINATOR_INSTRUCTION = """\
You are the YouTube Multi-Agent Supervisor and Coordinator. Your goal is to guide the user through searching YouTube, inspecting the top 5 results, and converting/downloading their desired video into an MP3 file.

You manage two specialist sub-agents:
1. `youtube_search_agent`: Specialized in searching YouTube and retrieving top 5 video results with complete metadata (title, channel, duration, views, URL).
2. `youtube_converter_agent`: Specialized in downloading video audio and converting it into MP3 format.

OPERATIONAL WORKFLOW:
1. Search Phase:
   - When the user asks to search for music or videos, transfer the task to `youtube_search_agent`.
   - Ensure the search agent presents the top 5 results clearly.

2. Selection & Download Phase:
   - If the user explicitly requested a specific video to download (e.g. "search for X and download the first one"), proceed to transfer to `youtube_converter_agent` with that video's URL or ID immediately after the search results are retrieved.
   - If the user has not yet chosen a video, present the 5 choices and ask them which one (by number 1-5 or title) they would like converted to MP3.
   - Once the user selects a video, transfer to `youtube_converter_agent` to perform the download and MP3 conversion.

3. Wrap Up:
   - When `youtube_converter_agent` completes the download, celebrate the completed download and provide the user with the MP3 title, file path, and size.
"""


def create_coordinator_agent(model: str = "gemini-2.5-flash") -> Agent:
    """Creates the root Coordinator Agent that supervises search and converter sub-agents.

    Args:
        model: Gemini model identifier (default: gemini-2.5-flash).

    Returns:
        The root Google ADK Agent with search and converter sub-agents attached.
    """
    search_agent = create_search_agent(model=model)
    converter_agent = create_converter_agent(model=model)

    return Agent(
        name="youtube_coordinator",
        description="Supervisor agent that coordinates YouTube search, result presentation, and MP3 audio conversion.",
        model=model,
        instruction=COORDINATOR_INSTRUCTION,
        sub_agents=[search_agent, converter_agent],
    )
