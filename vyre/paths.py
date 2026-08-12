import os
from pathlib import Path


def _base_dir() -> Path:
    root = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = Path(root) / "Vyre"
    path.mkdir(parents=True, exist_ok=True)
    return path


BASE_DIR = _base_dir()
VAULT_FILE = BASE_DIR / "vault.dat"
CONFIG_FILE = BASE_DIR / "config.json"
PROFILES_DIR = BASE_DIR / "profiles"

PROFILES_DIR.mkdir(parents=True, exist_ok=True)


def profile_dir(account_id: str) -> Path:
    path = PROFILES_DIR / account_id
    path.mkdir(parents=True, exist_ok=True)
    return path
