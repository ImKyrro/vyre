import json
import urllib.error
import urllib.request

from . import __version__


def _parse(version: str) -> tuple:
    parts = []
    for chunk in str(version).strip().lstrip("v").split("."):
        digits = "".join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def is_newer(remote: str, local: str = __version__) -> bool:
    return _parse(remote) > _parse(local)


def check(url: str, timeout: float = 8.0) -> dict:
    if not url:
        return {}
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Vyre-Updater", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return {}

    if isinstance(data, dict) and "tag_name" in data:
        remote = data.get("tag_name", "")
        download = data.get("html_url", "")
        notes = data.get("body", "")
    else:
        remote = data.get("version", "") if isinstance(data, dict) else ""
        download = data.get("url", "") if isinstance(data, dict) else ""
        notes = data.get("notes", "") if isinstance(data, dict) else ""

    if remote and is_newer(remote):
        return {"version": remote.lstrip("v"), "url": download, "notes": notes}
    return {}
