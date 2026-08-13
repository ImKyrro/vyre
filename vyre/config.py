import json

from .paths import CONFIG_FILE

_DEFAULTS = {
    "confirm_delete": True,
    "presence_auto_refresh": True,
    "presence_interval": 60,
    "minimize_to_tray": False,
    "start_with_windows": False,
    "launch_mode": "account",
    "saved_games": [
        {"name": "Grow a Garden", "place_id": "126884695634066"},
        {"name": "Brookhaven RP", "place_id": "4924922222"},
        {"name": "Blox Fruits", "place_id": "2753915549"},
    ],
    "open_web_external": False,
    "auto_lock_minutes": 0,
    "allow_multi_instance": False,
    "update_url": "https://api.github.com/repos/ImKyrro/Vyre-Roblox-Alt-Manager/releases/latest",
    "check_updates": True,
    "hide_info": False,
    "hide_images": False,
}


class Config:
    def __init__(self, data: dict):
        self._data = data

    @classmethod
    def load(cls) -> "Config":
        data = dict(_DEFAULTS)
        if CONFIG_FILE.exists():
            try:
                stored = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                if isinstance(stored, dict):
                    data.update(stored)
            except (ValueError, OSError):
                pass
        return cls(data)

    def get(self, key: str, default=None):
        return self._data.get(key, _DEFAULTS.get(key, default))

    def set(self, key: str, value) -> None:
        self._data[key] = value

    def update(self, values: dict) -> None:
        self._data.update(values)

    def save(self) -> None:
        try:
            CONFIG_FILE.write_text(json.dumps(self._data, indent=2), encoding="utf-8")
        except OSError:
            pass
