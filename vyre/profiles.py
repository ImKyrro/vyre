import json
import re
from datetime import datetime

from .paths import BASE_DIR

_META = BASE_DIR / "profiles.json"
_DEFAULT = {"name": "Default", "file": "vault.dat"}


def _read() -> list:
    if _META.exists():
        try:
            data = json.loads(_META.read_text(encoding="utf-8"))
            if isinstance(data, list) and data:
                return data
        except (ValueError, OSError):
            pass
    return [dict(_DEFAULT)]


def _write(profiles: list) -> None:
    try:
        _META.write_text(json.dumps(profiles, indent=2), encoding="utf-8")
    except OSError:
        pass


def list_profiles() -> list:
    profiles = _read()
    for profile in profiles:
        profile["path"] = BASE_DIR / profile["file"]
    return profiles


def _slug(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "profile"
    return base


def add_profile(name: str):
    profiles = _read()
    existing = {p["file"] for p in profiles}
    slug = _slug(name)
    file = f"vault-{slug}.dat"
    counter = 1
    while file in existing:
        counter += 1
        file = f"vault-{slug}-{counter}.dat"
    profiles.append({"name": name, "file": file})
    _write(profiles)
    return BASE_DIR / file


def reset_profile(file: str) -> None:
    path = BASE_DIR / file
    if path.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = BASE_DIR / f"{file}.locked-{stamp}"
        try:
            path.rename(backup)
        except OSError:
            pass
