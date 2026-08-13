import os

from mcp.server.mcpserver import MCPServer

from . import launcher, roblox
from .crypto import VaultError
from .storage import Vault

server = MCPServer(
    name="vyre",
    version="1.0.0",
    instructions="Manage Roblox alt accounts stored in Vyre: list accounts, check presence, browse servers, and launch games.",
)

_vault_cache: Vault | None = None


def _vault() -> Vault:
    global _vault_cache
    if _vault_cache is not None:
        return _vault_cache
    password = os.environ.get("VYRE_MASTER_PASSWORD", "")
    if not password:
        raise RuntimeError("Set VYRE_MASTER_PASSWORD to unlock the Vyre vault.")
    if not Vault.exists():
        raise RuntimeError("No Vyre vault found. Create one in the Vyre app first.")
    try:
        _vault_cache = Vault.unlock(password)
    except VaultError as error:
        raise RuntimeError(str(error))
    return _vault_cache


def _find(query: str):
    vault = _vault()
    query = query.strip().lower()
    for account in vault.accounts:
        if query in (account.id.lower(), account.name.lower(), account.username.lower()):
            return account
    for account in vault.accounts:
        if query and (query in account.name.lower() or query in account.username.lower()):
            return account
    return None


@server.tool(description="List all Roblox accounts saved in Vyre.")
def list_accounts() -> list[dict]:
    return [
        {
            "id": account.id,
            "name": account.name,
            "username": account.username,
            "user_id": account.user_id,
            "favorite": account.favorite,
        }
        for account in _vault().accounts
    ]


@server.tool(description="Get the live Roblox presence for a saved account by name, username, or id.")
def account_presence(account: str) -> dict:
    found = _find(account)
    if not found:
        return {"error": f"No account matching '{account}'."}
    if not found.user_id:
        return {"error": "Account has no verified user id."}
    presence = roblox.fetch_presence(found.cookie, [found.user_id])
    return presence.get(found.user_id, {"kind": "offline", "label": "Offline"})


@server.tool(description="Get details about a Roblox game by its place id.")
def game_info(place_id: str) -> dict:
    pid = launcher.parse_place_id(place_id)
    if not pid:
        return {"error": "Invalid place id."}
    return roblox.fetch_game_info(pid) or {"error": "Game not found."}


@server.tool(description="List public servers for a Roblox place id.")
def list_servers(place_id: str, limit: int = 25) -> list[dict]:
    pid = launcher.parse_place_id(place_id)
    if not pid:
        return [{"error": "Invalid place id."}]
    servers = roblox.list_servers(pid).get("servers", [])
    return [
        {"id": s.get("id"), "playing": s.get("playing"), "max": s.get("maxPlayers")}
        for s in servers[: max(1, limit)]
    ]


@server.tool(description="Launch a Roblox game on this machine as a saved account. Optionally join a specific server by job id.")
def launch_game(account: str, place_id: str, job_id: str = "") -> dict:
    found = _find(account)
    if not found:
        return {"error": f"No account matching '{account}'."}
    pid = launcher.parse_place_id(place_id)
    if not pid:
        return {"error": "Invalid place id."}
    ok, message = launcher.launch_as_account(found.cookie, pid, job_id)
    return {"ok": ok, "message": message}


@server.tool(description="Get stored details for a saved account (username, user id, favorite, note, created).")
def account_details(account: str) -> dict:
    found = _find(account)
    if not found:
        return {"error": f"No account matching '{account}'."}
    return {
        "id": found.id,
        "name": found.name,
        "username": found.username,
        "user_id": found.user_id,
        "favorite": found.favorite,
        "note": found.note,
        "created_at": found.created_at,
        "last_used": found.last_used,
    }


@server.tool(description="Check whether a saved account's Roblox cookie is still valid.")
def check_cookie(account: str) -> dict:
    found = _find(account)
    if not found:
        return {"error": f"No account matching '{account}'."}
    return {"valid": roblox.check_cookie(found.cookie)}


@server.tool(description="Launch Roblox as a saved account and follow another user into their current game.")
def join_user(account: str, target: str) -> dict:
    found = _find(account)
    if not found:
        return {"error": f"No account matching '{account}'."}
    user_id = roblox.resolve_username(target)
    if not user_id:
        return {"error": f"Could not resolve user '{target}'."}
    ok, message = launcher.follow_user(found.cookie, user_id)
    return {"ok": ok, "message": message}


@server.tool(description="Enable running multiple Roblox instances at once on this machine.")
def enable_multi_instance() -> dict:
    from . import multi_instance

    ok = multi_instance.enable()
    return {"ok": ok, "status": multi_instance.status()}


@server.tool(description="Control open Roblox windows: action is one of list, minimize, restore, grid, shrink, close.")
def roblox_windows(action: str = "list") -> dict:
    from . import wintools

    actions = {
        "minimize": wintools.minimize_all,
        "restore": wintools.restore_all,
        "grid": wintools.tile_grid,
        "shrink": wintools.shrink_titlebars,
        "close": wintools.close_all,
    }
    if action == "list":
        return {"open": wintools.count()}
    if action in actions:
        return {"affected": actions[action]()}
    return {"error": "Unknown action."}


def main() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
