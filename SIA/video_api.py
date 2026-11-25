import os
import html
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_WATCH_URL = "https://www.youtube.com/watch"


def search_videos(term):
    """Search YouTube through the YouTube Data API v3."""
    term = term.strip()
    if not term:
        return []

    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "YouTube search requires an API key. Set the YOUTUBE_API_KEY "
            "environment variable."
        )

    response = requests.get(
        SEARCH_URL,
        params={
            "key": api_key,
            "part": "snippet",
            "q": term,
            "type": "video",
            "maxResults": 15,
            "videoEmbeddable": "true",
        },
        timeout=20,
    )
    response.raise_for_status()

    videos = []
    for item in response.json().get("items", []):
        video_id = item.get("id", {}).get("videoId")
        snippet = item.get("snippet", {})
        title = snippet.get("title")
        if not video_id or not title:
            continue

        videos.append(
            {
                "title": html.unescape(title),
                "channel": snippet.get("channelTitle") or "Unknown channel",
                "video_id": video_id,
                "video_url": f"{YOUTUBE_WATCH_URL}?v={video_id}",
            }
        )

    return videos
