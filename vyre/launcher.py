import os
import re
import time
import urllib.parse

from . import roblox

_PLACE_LAUNCHER = "https://assetgame.roblox.com/game/PlaceLauncher.ashx"


def parse_place_id(text: str) -> str:
    value = (text or "").strip()
    if value.isdigit():
        return value
    match = re.search(r"(?:games|game)/(\d+)", value)
    if match:
        return match.group(1)
    match = re.search(r"placeId=(\d+)", value, re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r"(\d{4,})", value)
    return match.group(1) if match else ""


def parse_access_code(text: str) -> str:
    value = (text or "").strip()
    match = re.search(r"(?:accessCode|privateServerLinkCode|linkCode|code)=([\w-]+)", value, re.IGNORECASE)
    if match:
        return match.group(1)
    return value


def build_deeplink(place_id: str, job_id: str = "", access_code: str = "", link_code: str = "") -> str:
    params = {"placeId": place_id}
    if job_id:
        params["gameInstanceId"] = job_id
    if access_code:
        params["accessCode"] = access_code
    if link_code:
        params["linkCode"] = link_code
    query = urllib.parse.urlencode(params)
    return f"roblox://experiences/start?{query}"


def _follow_launcher_url(user_id: str) -> str:
    params = {"request": "RequestFollowUser", "userId": user_id}
    return f"{_PLACE_LAUNCHER}?{urllib.parse.urlencode(params)}"


def _place_launcher_url(place_id: str, job_id: str, access_code: str, link_code: str) -> str:
    params = {"placeId": place_id, "isPlayTogetherGame": "false"}
    if job_id:
        params["request"] = "RequestGameJob"
        params["gameId"] = job_id
    elif access_code or link_code:
        params["request"] = "RequestPrivateGame"
        if access_code:
            params["accessCode"] = access_code
        if link_code:
            params["linkCode"] = link_code
    else:
        params["request"] = "RequestGame"
    return f"{_PLACE_LAUNCHER}?{urllib.parse.urlencode(params)}"


def _client_uri(ticket: str, launcher_url: str) -> str:
    timestamp = int(time.time() * 1000)
    parts = [
        "roblox-player:1",
        "launchmode:play",
        f"gameinfo:{ticket}",
        f"launchtime:{timestamp}",
        f"placelauncherurl:{urllib.parse.quote(launcher_url, safe='')}",
        "browsertrackerid:0",
        "robloxLocale:en_us",
        "gameLocale:en_us",
        "channel:",
    ]
    return "+".join(parts)


def spoof_roblox_hwid() -> None:
    try:
        import uuid
        import winreg
        new_guid = f"{{{uuid.uuid4()}}}"
        clean_guid = str(uuid.uuid4())
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Roblox\Common\RbxCrash") as key:
            winreg.SetValueEx(key, "CrashGUID", 0, winreg.REG_SZ, new_guid)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\RobloxSpaceGroup") as key:
            winreg.SetValueEx(key, "HardwareID", 0, winreg.REG_SZ, clean_guid)
            winreg.SetValueEx(key, "DeviceID", 0, winreg.REG_SZ, clean_guid)
    except (ImportError, OSError):
        pass


def _open(uri: str) -> bool:
    try:
        from .config import Config
        if Config.load().get("spoof_hwid"):
            spoof_roblox_hwid()
    except Exception:
        pass
    try:
        os.startfile(uri)
        return True
    except OSError:
        return False


def launch_deeplink(place_id: str, job_id: str = "", access_code: str = "", link_code: str = "") -> bool:
    return _open(build_deeplink(place_id, job_id, access_code, link_code))


def launch_as_account(
    cookie: str,
    place_id: str,
    job_id: str = "",
    access_code: str = "",
    link_code: str = "",
    proxy: str = "",
) -> tuple[bool, str]:
    ticket = roblox.get_auth_ticket(cookie, proxy=proxy)
    if not ticket:
        if launch_deeplink(place_id, job_id, access_code, link_code):
            return True, "Launched with the Roblox app's current account (ticket unavailable)."
        return False, "Could not launch. Is Roblox installed?"
    launcher_url = _place_launcher_url(place_id, job_id, access_code, link_code)
    if _open(_client_uri(ticket, launcher_url)):
        return True, "Launching as this account."
    return False, "Could not start the Roblox client."


def follow_user(cookie: str, user_id: str, proxy: str = "") -> tuple[bool, str]:
    ticket = roblox.get_auth_ticket(cookie, proxy=proxy)
    if not ticket:
        if _open(f"roblox://experiences/start?userId={user_id}"):
            return True, "Launched with the Roblox app's current account (ticket unavailable)."
        return False, "Could not launch. Is Roblox installed?"
    if _open(_client_uri(ticket, _follow_launcher_url(user_id))):
        return True, "Joining that user's game."
    return False, "Could not start the Roblox client."
