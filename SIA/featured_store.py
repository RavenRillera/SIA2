"""Saves the videos/songs the user adds to Featured (data/featured.json)."""
import json
from pathlib import Path

FILE = Path(__file__).resolve().parent.parent / "data" / "featured.json"


def _load():
    try:
        data = json.loads(FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = {}
    return {"videos": list(data.get("videos", [])), "tracks": list(data.get("tracks", []))}


def _save(data):
    FILE.parent.mkdir(exist_ok=True)
    FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _key(entry):
    return entry.get("video_id") or entry.get("url")


def load(section):
    """section is 'videos' or 'tracks'."""
    return _load()[section]


def add(section, entry):
    """Returns False if it is already saved."""
    data = _load()
    if any(_key(e) == _key(entry) for e in data[section]):
        return False
    data[section].append(entry)
    _save(data)
    return True


def remove(section, entry):
    data = _load()
    data[section] = [e for e in data[section] if _key(e) != _key(entry)]
    _save(data)