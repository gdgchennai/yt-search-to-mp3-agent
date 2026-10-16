"""YouTube Audio Converter and Downloader Agent using Google ADK."""

from __future__ import annotations

from google.adk import Agent
from tools.youtube_tools import download_and_convert_to_mp3

CONVERTER_AGENT_INSTRUCTION = """\
You are the YouTube Audio Downloader & MP3 Converter Specialist Agent. Your primary role is to download audio from YouTube videos and convert it into high-quality MP3 format using the `download_and_convert_to_mp3` tool.

INSTRUCTIONS:
1. When you receive a video URL or video ID from the user or the coordinator agent, call `download_and_convert_to_mp3(video_url=...)`.
2. Inspect the result from the tool:
   - If successful, provide a clear and organized summary of the download:
     * Title of the song/video
     * Destination MP3 file path
     * File size in MB
     * Track duration
   - If an error occurred, explain the issue clearly to the user.
3. Hand back control to the user or coordinator agent with a friendly confirmation.
"""


def create_converter_agent(model: str = "gemini-2.5-flash") -> Agent:
    """Creates and returns the YouTube MP3 Converter Agent.

    Args:
        model: Gemini model identifier (default: gemini-2.5-flash).

    Returns:
        A Google ADK Agent instance configured for audio download and MP3 conversion.
    """
    return Agent(
        name="youtube_converter_agent",
        description="Specialist agent that downloads YouTube video audio streams and converts them into MP3 audio files.",
        model=model,
        instruction=CONVERTER_AGENT_INSTRUCTION,
        tools=[download_and_convert_to_mp3],
    )
