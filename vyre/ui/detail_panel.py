from datetime import datetime, timezone

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from .. import roblox
from ..models import Account
from ..theme import PALETTE
from . import icons
from .widgets import Avatar, StatChip


def _fmt_date(iso: str) -> str:
    if not iso:
        return "—"
    try:
        moment = datetime.fromisoformat(iso)
    except ValueError:
        return "—"
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone().strftime("%b %d, %Y")


class _DetailWorker(QThread):
    done = Signal(str, dict)

    def __init__(self, account: Account, parent=None):
        super().__init__(parent)
        self._id = account.id
        self._cookie = account.cookie
        self._user_id = account.user_id
        self._proxy = account.proxy
        self._vip = getattr(account, "private_servers", [])

    def run(self) -> None:
        first = {}
        if not self._user_id:
            identity = roblox.fetch_identity(self._cookie, proxy=self._proxy)
            if identity:
                self._user_id = identity["user_id"]
                first["identity"] = identity
        info = {}
        if self._user_id:
            presence = roblox.fetch_presence(self._cookie, [self._user_id], self._proxy)
            info = presence.get(self._user_id, {"kind": "offline", "label": "Offline"})
            first["presence"] = info
        self.done.emit(self._id, first)

        if not self._user_id:
            return
        extra = {"stats": roblox.fetch_stats(self._user_id, self._proxy)}
        place = info.get("root_place_id") or info.get("place_id")
        if info.get("kind") == "ingame" and place:
            game = roblox.fetch_game_info(str(place))
            game["place_id"] = str(place)
            game["job_id"] = info.get("game_id") or ""
            extra["game"] = game
        self.done.emit(self._id, extra)

        if self._vip:
            vip_data = []
            for vip in self._vip:
                link = vip.get("link", "")
                name = vip.get("name", "VIP Server")
                from .. import launcher
                place_id = launcher.parse_place_id(link)
                icon_bytes = b""
                if place_id:
                    universe = roblox.resolve_universe(place_id)
                    if universe:
                        icon_url = roblox.fetch_game_icon(universe)
                        if icon_url:
                            import urllib.request
                            try:
                                icon_bytes = urllib.request.urlopen(icon_url, timeout=3.0).read()
                            except Exception:
                                pass
                vip_data.append({"name": name, "link": link, "icon_bytes": icon_bytes})
            self.done.emit(self._id, {"vip": vip_data})


class DetailPanel(QWidget):
    browse_requested = Signal(str)
    launch_requested = Signal(str)
    web_requested = Signal(str)
    copy_cookie_requested = Signal(str)
    copy_profile_requested = Signal(str)
    edit_requested = Signal(str)
    settings_web_requested = Signal(str)
    health_requested = Signal(str)
    refresh_cookie_requested = Signal(str)
    join_requested = Signal(str, str, str)
    vip_launch_requested = Signal(str, str)

    def __init__(self, config=None, parent=None):
        super().__init__(parent)
        self.setObjectName("DetailPane")
        self._config = config
        self._account: Account | None = None
        self._worker: _DetailWorker | None = None
        self._join = ("", "")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(32, 28, 32, 28)
        outer.setSpacing(16)

        head = QHBoxLayout()
        head.setSpacing(18)
        self._avatar = Avatar("?", PALETTE["accent"], 88)
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
        self._join_btn = QPushButton("  Join their game")
        self._join_btn.setObjectName("Primary")
        self._join_btn.setIcon(icons.icon("play", "#ffffff", 15))
        self._join_btn.setCursor(Qt.PointingHandCursor)
        self._join_btn.setFixedWidth(170)
        self._join_btn.clicked.connect(self._emit_join)
        self._join_btn.hide()
        info.addWidget(self._join_btn)

        self._vip_row = QWidget()
        vip_layout = QHBoxLayout(self._vip_row)
        vip_layout.setContentsMargins(0, 0, 0, 0)
        self._vip_combo = QComboBox()
        self._vip_launch = QPushButton("Launch VIP")
        self._vip_launch.setObjectName("Primary")
        self._vip_launch.clicked.connect(self._emit_vip_launch)
        vip_layout.addWidget(self._vip_combo, 1)
        vip_layout.addWidget(self._vip_launch)
        info.addWidget(self._vip_row)
        self._vip_row.hide()

        info.addStretch(1)
        head.addLayout(info, 1)
        outer.addLayout(head)

        self._stats_row = QWidget()
        stats = QHBoxLayout(self._stats_row)
        stats.setContentsMargins(0, 0, 0, 0)
        stats.setSpacing(12)
        self._friends = StatChip("—", "Friends")
        self._followers = StatChip("—", "Followers")
        self._following = StatChip("—", "Following")
        self._uid = StatChip("—", "User ID")
        for chip in (self._friends, self._followers, self._following, self._uid):
            stats.addWidget(chip)
        stats.addStretch(1)
        outer.addWidget(self._stats_row)

        actions = QGridLayout()
        actions.setSpacing(9)
        self._browse = self._action("Browse", "login", self.browse_requested, primary=True)
        launch = self._action("Launch", "play", self.launch_requested)
        web = self._action("View web", "external", self.web_requested)
        account_settings = self._action("Account", "mail", self.settings_web_requested)
        edit = self._action("Edit", "edit", self.edit_requested)
        copy_cookie = self._action("Copy cookie", "copy", self.copy_cookie_requested)
        copy_profile = self._action("Copy link", "link", self.copy_profile_requested)
        check = self._action("Check", "shield", self.health_requested)
        self._refresh_cookie = self._action("Refresh cookie", "refresh", self.refresh_cookie_requested)
        actions.addWidget(self._browse, 0, 0)
        actions.addWidget(launch, 0, 1)
        actions.addWidget(web, 0, 2)
        actions.addWidget(account_settings, 0, 3)
        actions.addWidget(edit, 1, 0)
        actions.addWidget(copy_cookie, 1, 1)
        actions.addWidget(copy_profile, 1, 2)
        actions.addWidget(check, 1, 3)
        actions.addWidget(self._refresh_cookie, 2, 0, 1, 4)
        for col in range(4):
            actions.setColumnStretch(col, 1)
        outer.addLayout(actions)

        cards = QHBoxLayout()
        cards.setSpacing(14)
        cards.addWidget(self._build_notes_card(), 1)
        cards.addWidget(self._build_session_card(), 1)
        outer.addLayout(cards, 1)

    def _action(self, text: str, icon_name: str, signal, primary: bool = False) -> QPushButton:
        button = QPushButton(f"  {text}")
        color = "#ffffff" if primary else PALETTE["text_dim"]
        button.setIcon(icons.icon(icon_name, color, 16))
        if primary:
            button.setObjectName("Primary")
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(lambda: self._emit(signal))
        return button

    def _build_notes_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)
        title = QLabel("NOTES")
        title.setObjectName("StatLabel")
        layout.addWidget(title)
        self._note = QLabel("No notes yet.")
        self._note.setObjectName("Muted")
        self._note.setWordWrap(True)
        self._note.setAlignment(Qt.AlignTop)
        layout.addWidget(self._note, 1)
        return card

    def _build_session_card(self) -> QWidget:
        card = QWidget()
        card.setObjectName("Card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        title = QLabel("SESSION")
        title.setObjectName("StatLabel")
        layout.addWidget(title)
        self._added_row = self._info_row("Added")
        self._used_row = self._info_row("Last used")
        self._cookie_row = self._info_row("Cookie")
        for row in (self._added_row, self._used_row, self._cookie_row):
            layout.addLayout(row)
        layout.addStretch(1)
        return card

    def _info_row(self, label: str):
        row = QHBoxLayout()
        name = QLabel(label)
        name.setObjectName("Faint")
        value = QLabel("—")
        value.setStyleSheet("font-size: 12px; font-weight: 600;")
        row.addWidget(name)
        row.addStretch(1)
        row.addWidget(value)
        row._value = value
        return row

    def _emit(self, signal) -> None:
        if self._account:
            signal.emit(self._account.id)

    def _emit_join(self) -> None:
        if self._account and self._join[0]:
            self.join_requested.emit(self._account.id, self._join[0], self._join[1])

    def _emit_vip_launch(self) -> None:
        idx = self._vip_combo.currentIndex()
        if idx >= 0 and self._account:
            link = self._vip_combo.itemData(idx)
            if link:
                self.vip_launch_requested.emit(self._account.id, link)

    def _hide_info(self) -> bool:
        return bool(self._config and self._config.get("hide_info"))

    def set_account(self, account: Account) -> None:
        self._account = account
        self._join = ("", "")
        self._join_btn.hide()
        self._vip_row.hide()
        self._vip_combo.clear()
        hidden = self._hide_info()
        self._stats_row.setVisible(not hidden)
        self._handle.setVisible(not hidden)

        self._avatar.update_data(account.initials(), account.color)
        self._avatar.set_status("offline")
        if account.user_id:
            self._avatar.set_image_url(
                "https://thumbnails.roblox.com/v1/users/avatar-headshot"
                f"?userIds={account.user_id}&size=352x352&format=Png&isCircular=false"
            )
        if hidden:
            self._name.setText("Hidden account")
        else:
            self._name.setText(account.display_name or account.username or account.name)
        self._handle.setText(f"@{account.username}" if account.username else account.name)
        self._presence.setText("Checking presence…")
        self._presence.setStyleSheet(f"color: {PALETTE['text_dim']}; font-size: 13px; font-weight: 600;")
        self._uid.set_value("•••" if hidden else (account.user_id or "—"))
        self._friends.set_value("—")
        self._followers.set_value("—")
        self._following.set_value("—")
        self._note.setText(account.note or "No notes yet.")
        self._added_row._value.setText(_fmt_date(account.created_at))
        self._used_row._value.setText(_fmt_date(account.last_used) if account.last_used else "Never")
        valid = roblox.is_valid_cookie(account.cookie)
        self._cookie_row._value.setText("Looks valid" if valid else "Check needed")
        self._cookie_row._value.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {PALETTE['online'] if valid else PALETTE['studio']};"
        )

        self._worker = _DetailWorker(account, self)
        self._worker.done.connect(self._on_data)
        self._worker.start()

    def _on_data(self, account_id: str, data: dict) -> None:
        if not self._account or self._account.id != account_id:
            return
        hidden = self._hide_info()
        identity = data.get("identity", {})
        if identity and not hidden:
            self._uid.set_value(identity.get("user_id", "—"))

        if "presence" in data:
            presence = data["presence"]
            kind = presence.get("kind", "offline")
            self._avatar.set_status(kind)
            label = presence.get("label", "Offline")
            color = PALETTE["online"] if kind in ("online", "ingame") else (
                PALETTE["studio"] if kind == "studio" else PALETTE["text_faint"]
            )
            self._presence.setText(f"● {label}")
            self._presence.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: 600;")

        game = data.get("game", {})
        if game.get("name"):
            self._presence.setText(f"● In game — {game['name']}")
            self._presence.setStyleSheet(f"color: {PALETTE['online']}; font-size: 13px; font-weight: 600;")
            self._join = (game.get("place_id", ""), game.get("job_id", ""))
            self._join_btn.show()

        stats = data.get("stats", {})
        if stats and not hidden:
            self._friends.set_value(str(stats.get("friends", "—")))
            self._followers.set_value(str(stats.get("followers", "—")))
            self._following.set_value(str(stats.get("following", "—")))

        if "vip" in data:
            self._vip_combo.clear()
            vip_list = data["vip"]
            if vip_list:
                from PySide6.QtGui import QIcon, QPixmap
                for v in vip_list:
                    icon = QIcon()
                    if v["icon_bytes"]:
                        pixmap = QPixmap()
                        pixmap.loadFromData(v["icon_bytes"])
                        icon = QIcon(pixmap)
                    self._vip_combo.addItem(icon, v["name"], v["link"])
                self._vip_row.show()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter
        from PySide6.QtWidgets import QStyle, QStyleOption
        p = QPainter()
        if p.begin(self):
            opt = QStyleOption()
            opt.initFrom(self)
            self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)
            p.end()
