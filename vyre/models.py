import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return uuid.uuid4().hex


@dataclass
class Account:
    name: str
    cookie: str = ""
    username: str = ""
    display_name: str = ""
    user_id: str = ""
    note: str = ""
    proxy: str = ""
    color: str = "#e5484d"
    favorite: bool = False
    private_server_link: str = ""
    id: str = field(default_factory=_new_id)
    created_at: str = field(default_factory=_now)
    last_used: str = ""

    def touch(self) -> None:
        self.last_used = _now()

    def initials(self) -> str:
        source = (self.username or self.name).strip()
        if not source:
            return "?"
        parts = source.split()
        if len(parts) == 1:
            return parts[0][:2].upper()
        return (parts[0][0] + parts[1][0]).upper()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Account":
        fields = {
            "name", "cookie", "username", "display_name", "user_id",
            "note", "proxy", "color", "favorite", "private_server_link",
            "id", "created_at", "last_used",
        }
        clean = {key: value for key, value in data.items() if key in fields}
        return cls(**clean)
