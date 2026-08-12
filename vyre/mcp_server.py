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


def main() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
