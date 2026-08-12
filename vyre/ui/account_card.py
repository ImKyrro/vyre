from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMenu,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..models import Account
from ..theme import PALETTE
from .widgets import Avatar


class AccountCard(QWidget):
    select_requested = Signal(str)
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    copy_requested = Signal(str)
    favorite_requested = Signal(str)
    duplicate_requested = Signal(str)
    web_requested = Signal(str)
    launch_requested = Signal(str)
    move_requested = Signal(str, int)

    def __init__(self, account: Account, parent=None):
        super().__init__(parent)
        self.account_id = account.id
        self._favorite = account.favorite
        self._username = account.username
        self._active = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(62)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 6, 8)
        layout.setSpacing(11)

        self._avatar = Avatar(account.initials(), account.color, 40)
        self._avatar.set_status("offline")
        if account.user_id:
            self._avatar.set_image_url(
                f"https://thumbnails.roblox.com/v1/users/avatar-headshot"
                f"?userIds={account.user_id}&size=150x150&format=Png&isCircular=false"
            )
        layout.addWidget(self._avatar)

        text = QVBoxLayout()
        text.setSpacing(2)
        text.setContentsMargins(0, 0, 0, 0)
        self._name = QLabel(account.name)
        self._name.setStyleSheet("font-size: 13px; font-weight: 700;")
        self._sub = QLabel(account.username or "Not verified")
        self._sub.setStyleSheet(f"color: {PALETTE['text_faint']}; font-size: 11px;")
        text.addWidget(self._name)
        text.addWidget(self._sub)
        layout.addLayout(text, 1)

        self._star = QToolButton()
        self._star.setObjectName("Star")
        self._star.setCursor(Qt.PointingHandCursor)
        self._star.clicked.connect(lambda: self.favorite_requested.emit(self.account_id))
        layout.addWidget(self._star, 0, Qt.AlignVCenter)
        self._render_star()

        self._menu_button = QToolButton()
        self._menu_button.setText("⋯")
        self._menu_button.clicked.connect(self._open_menu)
        layout.addWidget(self._menu_button, 0, Qt.AlignVCenter)

        self._refresh_style()

    def set_active(self, active: bool) -> None:
        self._active = active
        self._refresh_style()

    def update_account(self, account: Account) -> None:
        self._favorite = account.favorite
        self._username = account.username
        self._avatar.update_data(account.initials(), account.color)
        if account.user_id:
            self._avatar.set_image_url(
                f"https://thumbnails.roblox.com/v1/users/avatar-headshot"
                f"?userIds={account.user_id}&size=150x150&format=Png&isCircular=false"
            )
        self._name.setText(account.name)
        self._render_star()

    def update_presence(self, kind: str, label: str, location: str) -> None:
        self._avatar.set_status(kind)
        if kind in ("ingame", "online", "studio"):
            detail = location if (kind == "ingame" and location) else label
            self._sub.setText(detail)
            color = PALETTE["online"] if kind == "ingame" else PALETTE["text_dim"]
            self._sub.setStyleSheet(f"color: {color}; font-size: 11px;")
        else:
            self._sub.setText(self._username or "Offline")
            self._sub.setStyleSheet(f"color: {PALETTE['text_faint']}; font-size: 11px;")

    def _render_star(self) -> None:
        self._star.setText("★" if self._favorite else "☆")
        color = PALETTE["studio"] if self._favorite else PALETTE["text_faint"]
        self._star.setStyleSheet(f"QToolButton#Star {{ color: {color}; }}")

    def _refresh_style(self) -> None:
        if self._active:
            self.setStyleSheet(
                f"AccountCard {{ background-color: {PALETTE['surface_hover']};"
                f" border-radius: 10px; border-left: 3px solid {PALETTE['accent']}; }}"
            )
        else:
            self.setStyleSheet(
                "AccountCard { background-color: transparent; border-radius: 10px;"
                " border-left: 3px solid transparent; }"
                f"AccountCard:hover {{ background-color: {PALETTE['surface_alt']}; }}"
            )

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.select_requested.emit(self.account_id)
        super().mousePressEvent(event)

    def name_text(self) -> str:
        return self._name.text()

    def _open_menu(self) -> None:
        menu = QMenu(self)
        menu.addAction("Open", lambda: self.select_requested.emit(self.account_id))
        menu.addAction("Launch a game", lambda: self.launch_requested.emit(self.account_id))
        menu.addAction("View profile on web", lambda: self.web_requested.emit(self.account_id))
        menu.addSeparator()
        menu.addAction("Edit", lambda: self.edit_requested.emit(self.account_id))
        menu.addAction("Duplicate", lambda: self.duplicate_requested.emit(self.account_id))
        menu.addAction("Copy cookie", lambda: self.copy_requested.emit(self.account_id))
        menu.addSeparator()
        menu.addAction("Move up", lambda: self.move_requested.emit(self.account_id, -1))
        menu.addAction("Move down", lambda: self.move_requested.emit(self.account_id, 1))
        menu.addSeparator()
        menu.addAction("Delete", lambda: self.delete_requested.emit(self.account_id))
        menu.exec(self._menu_button.mapToGlobal(self._menu_button.rect().bottomRight()))
