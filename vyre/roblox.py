import json
import urllib.error
import urllib.request

COOKIE_NAME = ".ROBLOSECURITY"
COOKIE_DOMAIN = ".roblox.com"
HOME_URL = "https://www.roblox.com/home"
LOGIN_URL = "https://www.roblox.com/login"
AUTH_API = "https://users.roblox.com/v1/users/authenticated"

_WARNING = "_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you"


def normalize_cookie(raw: str) -> str:
    value = raw.strip()
    if not value:
        return ""
    if value.lower().startswith(".roblosecurity"):
        _, _, value = value.partition("=")
        value = value.strip()
    return value


def is_valid_cookie(raw: str) -> bool:
    value = normalize_cookie(raw)
    return _WARNING in value and len(value) > 200


def fetch_identity(cookie: str, timeout: float = 12.0) -> dict:
    value = normalize_cookie(cookie)
    request = urllib.request.Request(
        AUTH_API,
        headers={
            "Cookie": f"{COOKIE_NAME}={value}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Vyre",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return {}
    return {
        "username": data.get("name", ""),
        "display_name": data.get("displayName", ""),
        "user_id": str(data.get("id", "")),
    }
