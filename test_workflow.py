"""Comprehensive test suite for the Google ADK Multi-Agent YouTube Downloader."""

import json
import os
import shutil
import unittest

from agents.coordinator import create_coordinator_agent
from agents.converter_agent import create_converter_agent
from agents.search_agent import create_search_agent
from tools.youtube_tools import (
    search_youtube,
    download_and_convert_to_mp3,
    parse_search_results,
)


class TestYouTubeMultiAgent(unittest.TestCase):
    """Test suite for agents, tools, and multi-agent hierarchy."""

    def test_agent_hierarchy_creation(self):
        """Verify that Google ADK agents are properly instantiated with tools and subagents."""
        search_agent = create_search_agent()
        self.assertEqual(search_agent.name, "youtube_search_agent")
        self.assertEqual(len(search_agent.tools), 1)

        converter_agent = create_converter_agent()
        self.assertEqual(converter_agent.name, "youtube_converter_agent")
        self.assertEqual(len(converter_agent.tools), 1)

        coordinator = create_coordinator_agent()
        self.assertEqual(coordinator.name, "youtube_coordinator")
        self.assertEqual(len(coordinator.sub_agents), 2)
        sub_agent_names = [a.name for a in coordinator.sub_agents]
        self.assertIn("youtube_search_agent", sub_agent_names)
        self.assertIn("youtube_converter_agent", sub_agent_names)

    def test_search_youtube_tool(self):
        """Verify search_youtube tool retrieves top 5 results with metadata."""
        query = "classical piano relaxation"
        results_json = search_youtube(query=query, max_results=5)
        results = parse_search_results(results_json)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 5, f"Expected 5 results, got {len(results)}")

        first = results[0]
        self.assertIn("rank", first)
        self.assertEqual(first["rank"], 1)
        self.assertIn("title", first)
        self.assertTrue(len(first["title"]) > 0)
        self.assertIn("url", first)
        self.assertTrue(first["url"].startswith("https://www.youtube.com/watch?v="))
        self.assertIn("duration", first)
        self.assertIn("views", first)

    def test_download_and_convert_to_mp3_tool(self):
        """Verify download_and_convert_to_mp3 tool converts audio to valid MP3."""
        test_dir = "./test_downloads"
        os.makedirs(test_dir, exist_ok=True)

        try:
            # Short test video URL
            test_url = "https://www.youtube.com/watch?v=SdFYvBNBG1g"
            result_json = download_and_convert_to_mp3(
                video_url=test_url,
                output_dir=test_dir,
                preferred_quality="128",
            )
            result = json.loads(result_json)

            self.assertEqual(result.get("status"), "success", f"Download failed: {result}")
            self.assertIn("file_path", result)
            self.assertTrue(os.path.exists(result["file_path"]), "MP3 file should exist")
            self.assertTrue(result["file_path"].endswith(".mp3"), "File should have .mp3 extension")
            self.assertGreater(result.get("file_size_mb", 0), 0, "File size should be > 0 MB")
        finally:
            if os.path.exists(test_dir):
                shutil.rmtree(test_dir)


if __name__ == "__main__":
    unittest.main()
