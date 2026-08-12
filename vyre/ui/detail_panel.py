from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import roblox
from ..models import Account
from ..theme import PALETTE
from .widgets import Avatar, StatChip


class _DetailWorker(QThread):
    done = Signal(str, dict)

    def __init__(self, account: Account, parent=None):
        super().__init__(parent)
        self._id = account.id
        self._cookie = account.cookie
        self._user_id = account.user_id

    def run(self) -> None:
        result = {}
        if not self._user_id:
            identity = roblox.fetch_identity(self._cookie)
            if identity:
                self._user_id = identity["user_id"]
                result["identity"] = identity
        if self._user_id:
            presence = roblox.fetch_presence(self._cookie, [self._user_id])
            info = presence.get(self._user_id, {})
            result["presence"] = info
            result["stats"] = roblox.fetch_stats(self._user_id)
            place = info.get("root_place_id") or info.get("place_id")
            if info.get("kind") == "ingame" and place:
                result["game"] = roblox.fetch_game_info(str(place))
                result["game"]["place_id"] = str(place)
                result["game"]["job_id"] = info.get("game_id") or ""
        self.done.emit(self._id, result)


class DetailPanel(QWidget):
    browse_requested = Signal(str)
    launch_requested = Signal(str)
    web_requested = Signal(str)
    copy_cookie_requested = Signal(str)
    copy_profile_requested = Signal(str)
    edit_requested = Signal(str)
    settings_web_requested = Signal(str)
    join_requested = Signal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("DetailPane")
        self._account: Account | None = None
        self._worker: _DetailWorker | None = None
        self._join = ("", "")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(34, 30, 34, 30)
        outer.setSpacing(18)

        head = QHBoxLayout()
        head.setSpacing(18)
        self._avatar = Avatar("?", PALETTE["accent"], 92)
        head.addWidget(self._avatar, 0, Qt.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(4)
        self._name = QLabel("")
        self._name.setObjectName("H1")
        info.addWidget(self._name)
        self._handle = QLabel("")
        self._handle.setObjectName("Muted")
        info.addWidget(self._handle)
        self._presence = QLabel("")
        self._presence.setStyleSheet("font-size: 13px; font-weight: 600;")
        info.addWidget(self._presence)
        self._join_btn = QPushButton("Join their game")
        self._join_btn.setObjectName("Primary")
        self._join_btn.setCursor(Qt.PointingHandCursor)
        self._join_btn.setFixedWidth(160)
        self._join_btn.clicked.connect(self._emit_join)
        self._join_btn.hide()
        info.addWidget(self._join_btn)
        info.addStretch(1)
        head.addLayout(info, 1)
        outer.addLayout(head)

        stats = QHBoxLayout()
        stats.setSpacing(12)
        self._friends = StatChip("—", "Friends")
        self._followers = StatChip("—", "Followers")
        self._following = StatChip("—", "Following")
        self._uid = StatChip("—", "User ID")
        for chip in (self._friends, self._followers, self._following, self._uid):
            stats.addWidget(chip)
        stats.addStretch(1)
        outer.addLayout(stats)

        actions = QGridLayout()
        actions.setSpacing(10)
        self._browse = QPushButton("Open browser session")
        self._browse.setObjectName("Primary")
        self._browse.setCursor(Qt.PointingHandCursor)
        self._browse.clicked.connect(lambda: self._emit(self.browse_requested))
        launch = QPushButton("Launch a game")
        launch.clicked.connect(lambda: self._emit(self.launch_requested))
        web = QPushButton("View profile on web")
        web.clicked.connect(lambda: self._emit(self.web_requested))
        edit = QPushButton("Edit account")
        edit.clicked.connect(lambda: self._emit(self.edit_requested))
        copy_cookie = QPushButton("Copy cookie")
        copy_cookie.clicked.connect(lambda: self._emit(self.copy_cookie_requested))
        copy_profile = QPushButton("Copy profile link")
        copy_profile.clicked.connect(lambda: self._emit(self.copy_profile_requested))
        account_settings = QPushButton("Account && email settings")
        account_settings.clicked.connect(lambda: self._emit(self.settings_web_requested))
        for button in (launch, web, edit, copy_cookie, copy_profile, account_settings):
            button.setCursor(Qt.PointingHandCursor)
        actions.addWidget(self._browse, 0, 0)
        actions.addWidget(launch, 0, 1)
        actions.addWidget(web, 0, 2)
        actions.addWidget(edit, 1, 0)
        actions.addWidget(copy_cookie, 1, 1)
        actions.addWidget(copy_profile, 1, 2)
        actions.addWidget(account_settings, 2, 0)
        outer.addLayout(actions)

        self._note = QLabel("")
        self._note.setObjectName("Muted")
        self._note.setWordWrap(True)
        outer.addWidget(self._note)
        outer.addStretch(1)

    def _emit(self, signal) -> None:
        if self._account:
            signal.emit(self._account.id)

    def _emit_join(self) -> None:
        if self._account and self._join[0]:
            self.join_requested.emit(self._account.id, self._join[0], self._join[1])

    def set_account(self, account: Account) -> None:
        self._account = account
        self._join = ("", "")
        self._join_btn.hide()
        self._avatar.update_data(account.initials(), account.color)
        self._avatar.set_status("offline")
        if account.user_id:
            self._avatar.set_image_url(
                "https://thumbnails.roblox.com/v1/users/avatar-headshot"
                f"?userIds={account.user_id}&size=352x352&format=Png&isCircular=false"
            )
        self._name.setText(account.display_name or account.username or account.name)
        self._handle.setText(f"@{account.username}" if account.username else account.name)
        self._presence.setText("Checking presence…")
        self._presence.setStyleSheet(f"color: {PALETTE['text_dim']}; font-size: 13px; font-weight: 600;")
        self._uid.set_value(account.user_id or "—")
        self._friends.set_value("—")
        self._followers.set_value("—")
        self._following.set_value("—")
        self._note.setText(account.note)

        self._worker = _DetailWorker(account, self)
        self._worker.done.connect(self._on_data)
        self._worker.start()

    def _on_data(self, account_id: str, data: dict) -> None:
        if not self._account or self._account.id != account_id:
            return
        presence = data.get("presence", {})
        kind = presence.get("kind", "offline")
        self._avatar.set_status(kind)
        label = presence.get("label", "Offline")
        color = PALETTE["online"] if kind in ("online", "ingame") else (
            PALETTE["studio"] if kind == "studio" else PALETTE["text_faint"]
        )
        game = data.get("game", {})
        if kind == "ingame" and game.get("name"):
            self._presence.setText(f"● In game — {game['name']}")
            self._join = (game.get("place_id", ""), game.get("job_id", ""))
            self._join_btn.show()
        elif kind == "ingame":
            self._presence.setText(f"● {presence.get('location') or 'In game'}")
        else:
            self._presence.setText(f"● {label}")
        self._presence.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 600;")

        stats = data.get("stats", {})
        if stats:
            self._friends.set_value(str(stats.get("friends", "—")))
            self._followers.set_value(str(stats.get("followers", "—")))
            self._following.set_value(str(stats.get("following", "—")))
        identity = data.get("identity", {})
        if identity:
            self._uid.set_value(identity.get("user_id", "—"))
