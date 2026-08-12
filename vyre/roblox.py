import json
import urllib.error
import urllib.parse
import urllib.request

COOKIE_NAME = ".ROBLOSECURITY"
COOKIE_DOMAIN = ".roblox.com"
HOME_URL = "https://www.roblox.com/home"
LOGIN_URL = "https://www.roblox.com/login"
AUTH_API = "https://users.roblox.com/v1/users/authenticated"

_WARNING = "_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you"
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

PRESENCE_LABELS = {0: "Offline", 1: "Online", 2: "In game", 3: "In Studio", 4: "Offline"}
PRESENCE_KINDS = {0: "offline", 1: "online", 2: "ingame", 3: "studio", 4: "offline"}


def normalize_cookie(raw: str) -> str:
    value = (raw or "").strip()
    if not value:
        return ""
    if value.lower().startswith(".roblosecurity"):
        _, _, value = value.partition("=")
        value = value.strip()
    return value


def is_valid_cookie(raw: str) -> bool:
    value = normalize_cookie(raw)
    return _WARNING in value and len(value) > 200


def _open(request: urllib.request.Request, timeout: float):
    try:
        response = urllib.request.urlopen(request, timeout=timeout)
        return response.status, response.headers, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.headers, error.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, {}, b""


def _get(url: str, cookie: str = "", timeout: float = 12.0) -> dict:
    headers = {"User-Agent": _UA, "Accept": "application/json"}
    if cookie:
        headers["Cookie"] = f"{COOKIE_NAME}={normalize_cookie(cookie)}"
    status, _, body = _open(urllib.request.Request(url, headers=headers), timeout)
    if status != 200:
        return {}
    try:
        return json.loads(body.decode("utf-8"))
    except ValueError:
        return {}


def _post(url: str, cookie: str, payload: dict, timeout: float = 12.0, extra: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8")
    csrf = ""
    for _ in range(2):
        headers = {
            "User-Agent": _UA,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if cookie:
            headers["Cookie"] = f"{COOKIE_NAME}={normalize_cookie(cookie)}"
        if csrf:
            headers["X-CSRF-TOKEN"] = csrf
        if extra:
            headers.update(extra)
        status, resp_headers, body = _open(
            urllib.request.Request(url, data=data, headers=headers, method="POST"), timeout
        )
        if status == 403 and resp_headers.get("x-csrf-token"):
            csrf = resp_headers.get("x-csrf-token")
            continue
        if status == 200:
            try:
                return json.loads(body.decode("utf-8"))
            except ValueError:
                return {}
        return {}
    return {}


def fetch_identity(cookie: str, timeout: float = 12.0) -> dict:
    data = _get(AUTH_API, cookie, timeout)
    if not data:
        return {}
    return {
        "username": data.get("name", ""),
        "display_name": data.get("displayName", ""),
        "user_id": str(data.get("id", "")),
    }


def fetch_headshots(user_ids: list[str], size: str = "150x150") -> dict:
    ids = ",".join(str(i) for i in user_ids if i)
    if not ids:
        return {}
    url = (
        "https://thumbnails.roblox.com/v1/users/avatar-headshot"
        f"?userIds={ids}&size={size}&format=Png&isCircular=false"
    )
    data = _get(url)
    result = {}
    for item in data.get("data", []):
        if item.get("state") == "Completed" and item.get("imageUrl"):
            result[str(item.get("targetId"))] = item["imageUrl"]
    return result


def fetch_presence(cookie: str, user_ids: list[str]) -> dict:
    ids = [int(i) for i in user_ids if str(i).isdigit()]
    if not ids:
        return {}
    data = _post(
        "https://presence.roblox.com/v1/presence/users",
        cookie,
        {"userIds": ids},
    )
    result = {}
    for item in data.get("userPresences", []):
        ptype = item.get("userPresenceType", 0)
        result[str(item.get("userId"))] = {
            "kind": PRESENCE_KINDS.get(ptype, "offline"),
            "label": PRESENCE_LABELS.get(ptype, "Offline"),
            "location": item.get("lastLocation", ""),
            "place_id": item.get("placeId"),
            "root_place_id": item.get("rootPlaceId"),
            "game_id": item.get("gameId"),
            "universe_id": item.get("universeId"),
        }
    return result


def resolve_universe(place_id: str) -> str:
    data = _get(f"https://apis.roblox.com/universes/v1/places/{place_id}/universe")
    universe = data.get("universeId")
    return str(universe) if universe else ""


def fetch_game_info(place_id: str) -> dict:
    universe = resolve_universe(place_id)
    if not universe:
        return {}
    data = _get(f"https://games.roblox.com/v1/games?universeIds={universe}")
    items = data.get("data", [])
    if not items:
        return {"universe_id": universe}
    game = items[0]
    return {
        "universe_id": universe,
        "name": game.get("name", ""),
        "playing": game.get("playing", 0),
        "visits": game.get("visits", 0),
        "max_players": game.get("maxPlayers", 0),
        "creator": game.get("creator", {}).get("name", ""),
    }


def list_servers(place_id: str, cursor: str = "", limit: int = 100) -> dict:
    url = (
        f"https://games.roblox.com/v1/games/{place_id}/servers/Public"
        f"?sortOrder=Desc&excludeFullGames=false&limit={limit}"
    )
    if cursor:
        url += f"&cursor={urllib.parse.quote(cursor)}"
    data = _get(url)
    return {
        "servers": data.get("data", []),
        "next": data.get("nextPageCursor", ""),
    }


def fetch_stats(user_id: str) -> dict:
    if not str(user_id).isdigit():
        return {}
    friends = _get(f"https://friends.roblox.com/v1/users/{user_id}/friends/count")
    followers = _get(f"https://friends.roblox.com/v1/users/{user_id}/followers/count")
    following = _get(f"https://friends.roblox.com/v1/users/{user_id}/followings/count")
    return {
        "friends": friends.get("count", 0),
        "followers": followers.get("count", 0),
        "following": following.get("count", 0),
    }


def get_auth_ticket(cookie: str, timeout: float = 12.0) -> str:
    data = json.dumps({}).encode("utf-8")
    csrf = ""
    for _ in range(2):
        headers = {
            "User-Agent": _UA,
            "Content-Type": "application/json",
            "Referer": "https://www.roblox.com/",
            "Origin": "https://www.roblox.com",
            "RBXAuthenticationNegotiation": "1",
            "Cookie": f"{COOKIE_NAME}={normalize_cookie(cookie)}",
        }
        if csrf:
            headers["X-CSRF-TOKEN"] = csrf
        status, resp_headers, _ = _open(
            urllib.request.Request(
                "https://auth.roblox.com/v1/authentication-ticket",
                data=data,
                headers=headers,
                method="POST",
            ),
            timeout,
        )
        if status == 403 and resp_headers.get("x-csrf-token"):
            csrf = resp_headers.get("x-csrf-token")
            continue
        ticket = resp_headers.get("rbx-authentication-ticket") if resp_headers else ""
        return ticket or ""
    return ""


def resolve_username(username: str) -> str:
    name = (username or "").strip().lstrip("@")
    if not name:
        return ""
    if name.isdigit():
        return name
    data = _post(
        "https://users.roblox.com/v1/usernames/users",
        "",
        {"usernames": [name], "excludeBannedUsers": False},
    )
    items = data.get("data", [])
    return str(items[0].get("id")) if items else ""


def account_settings_url() -> str:
    return "https://www.roblox.com/my/account#!/info"


def profile_url(user_id: str) -> str:
    return f"https://www.roblox.com/users/{user_id}/profile"


def game_url(place_id: str) -> str:
    return f"https://www.roblox.com/games/{place_id}"
