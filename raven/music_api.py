import requests

SEARCH_URL = "https://itunes.apple.com/search"


def search_songs(term):
    """Ask the iTunes Search API for songs. Each hit includes a preview file URL."""
    term = term.strip()
    if not term:
        return []

    response = requests.get(
        SEARCH_URL,
        params={"term": term, "media": "music", "entity": "song", "limit": 15},
        timeout=20,
    )
    response.raise_for_status()

    songs = []
    for item in response.json().get("results", []):
        preview_url = item.get("previewUrl")
        title = item.get("trackName")
        if not preview_url or not title:
            continue
        songs.append(
            {
                "title": title,
                "artist": item.get("artistName") or "Unknown artist",
                "album": item.get("collectionName") or "",
                "preview_url": preview_url,
            }
        )
    return songs
