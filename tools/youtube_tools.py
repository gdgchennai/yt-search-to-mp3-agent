"""YouTube Search and MP3 Downloader Tools.

This module provides tools for:
1. Searching YouTube for queries and returning top results with metadata.
2. Downloading YouTube video audio and converting it to high-quality MP3 format.
"""

from __future__ import annotations

import json
import os
import shutil
from typing import Any, Dict, List, Optional

import static_ffmpeg
import yt_dlp

# Ensure static ffmpeg binaries are in PATH if system ffmpeg is missing
try:
    static_ffmpeg.add_paths()
except Exception:
    pass


def _format_duration(seconds: Optional[int | float]) -> str:
    """Format duration in seconds to HH:MM:SS or MM:SS format."""
    if seconds is None:
        return "N/A"
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _format_views(views: Optional[int]) -> str:
    """Format view counts into readable strings (e.g. 1.2M, 450K)."""
    if views is None:
        return "N/A"
    if views >= 1_000_000:
        return f"{views / 1_000_000:.1f}M views"
    if views >= 1_000:
        return f"{views / 1_000:.1f}K views"
    return f"{views} views"


def search_youtube(query: str, max_results: int = 5) -> str:
    """Searches YouTube for videos matching a user query and returns top results.

    Args:
        query: The search term or keywords to look up on YouTube.
        max_results: The maximum number of results to return (default: 5).

    Returns:
        A JSON string containing a list of video objects with rank, title,
        video_id, url, channel, duration, and view_count.
    """
    if not query or not query.strip():
        return json.dumps({"error": "Empty search query provided."})

    max_results = max(1, min(max_results, 10))
    search_spec = f"ytsearch{max_results}:{query.strip()}"

    ydl_opts: Dict[str, Any] = {
        "extract_flat": True,
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "ignoreerrors": True,
    }

    # Enable node JS runtime if node is present
    if shutil.which("node"):
        ydl_opts["js_runtimes"] = {"node": {}}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_data = ydl.extract_info(search_spec, download=False)
            if not search_data or "entries" not in search_data:
                return json.dumps({"error": f"No results found for query: {query}"})

            raw_entries = [e for e in search_data.get("entries", []) if e is not None]
            results: List[Dict[str, Any]] = []

            for index, entry in enumerate(raw_entries[:max_results], start=1):
                vid = entry.get("id") or ""
                url = entry.get("url")
                if not url or "watch?v=" not in url:
                    url = f"https://www.youtube.com/watch?v={vid}"

                results.append({
                    "rank": index,
                    "title": entry.get("title") or "Unknown Title",
                    "video_id": vid,
                    "url": url,
                    "channel": entry.get("uploader") or entry.get("channel") or "Unknown Channel",
                    "duration": _format_duration(entry.get("duration")),
                    "views": _format_views(entry.get("view_count")),
                })

            return json.dumps(results, indent=2)

    except Exception as exc:
        return json.dumps({"error": f"Failed to search YouTube: {str(exc)}"})


def download_and_convert_to_mp3(
    video_url: str,
    output_dir: str = "./downloads",
    preferred_quality: str = "192",
) -> str:
    """Downloads audio from a YouTube video and converts it into an MP3 file.

    Args:
        video_url: The full YouTube URL or 11-character video ID to download.
        output_dir: The directory where the resulting MP3 file will be saved.
        preferred_quality: Audio bitrate in kbps (e.g. '192', '256', '320').

    Returns:
        A JSON string containing the status, title, file_path, file_size_mb,
        duration, and a confirmation message.
    """
    if not video_url or not video_url.strip():
        return json.dumps({"status": "error", "message": "Video URL or ID is required."})

    cleaned_url = video_url.strip()
    if not cleaned_url.startswith("http://") and not cleaned_url.startswith("https://"):
        # Assume it's a video ID
        cleaned_url = f"https://www.youtube.com/watch?v={cleaned_url}"

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Check ffmpeg availability
    ffmpeg_available = bool(shutil.which("ffmpeg"))
    if not ffmpeg_available:
        try:
            static_ffmpeg.add_paths()
            ffmpeg_available = bool(shutil.which("ffmpeg"))
        except Exception:
            pass

    if not ffmpeg_available:
        return json.dumps({
            "status": "error",
            "message": "FFmpeg executable could not be located to convert audio to MP3."
        })

    ydl_opts: Dict[str, Any] = {
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": preferred_quality,
        }],
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }

    if shutil.which("node"):
        ydl_opts["js_runtimes"] = {"node": {}}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(cleaned_url, download=True)
            if not info:
                return json.dumps({
                    "status": "error",
                    "message": f"Failed to retrieve video metadata for {cleaned_url}"
                })

            title = info.get("title") or "Unknown Title"
            duration = _format_duration(info.get("duration"))

            # Determine the converted mp3 filepath
            prepared_filename = ydl.prepare_filename(info)
            base_name, _ = os.path.splitext(prepared_filename)
            mp3_path = f"{base_name}.mp3"

            # Check if file exists, or search in directory if name was sanitized differently
            if not os.path.exists(mp3_path):
                # Search output_dir for recently created mp3
                candidate_files = [
                    os.path.join(output_dir, f)
                    for f in os.listdir(output_dir)
                    if f.endswith(".mp3")
                ]
                if candidate_files:
                    # Pick most recent
                    mp3_path = max(candidate_files, key=os.path.getmtime)

            if os.path.exists(mp3_path):
                file_size_bytes = os.path.getsize(mp3_path)
                file_size_mb = round(file_size_bytes / (1024 * 1024), 2)

                return json.dumps({
                    "status": "success",
                    "title": title,
                    "file_path": os.path.abspath(mp3_path),
                    "file_size_mb": file_size_mb,
                    "duration": duration,
                    "video_url": cleaned_url,
                    "message": f"Successfully converted and downloaded '{title}' as MP3."
                }, indent=2)
            else:
                return json.dumps({
                    "status": "error",
                    "message": "Conversion completed but output MP3 file could not be verified."
                })

    except Exception as exc:
        return json.dumps({
            "status": "error",
            "message": f"Download / conversion failed: {str(exc)}"
        })


def parse_search_results(json_str: str) -> List[Dict[str, Any]]:
    """Helper function to parse the search JSON string into a python list."""
    try:
        data = json.loads(json_str)
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []
