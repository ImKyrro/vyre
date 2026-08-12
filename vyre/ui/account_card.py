from datetime import datetime, timezone

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


def _relative(iso: str) -> str:
    if not iso:
        return "Never used"
    try:
        moment = datetime.fromisoformat(iso)
    except ValueError:
        return "Never used"
    delta = datetime.now(timezone.utc) - moment
    seconds = int(delta.total_seconds())
    if seconds < 60:
        return "Just now"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    if seconds < 86400:
        return f"{seconds // 3600}h ago"
    return f"{seconds // 86400}d ago"


class AccountCard(QWidget):
    switch_requested = Signal(str)
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    copy_requested = Signal(str)

    def __init__(self, account: Account, parent=None):
        super().__init__(parent)
        self.account_id = account.id
        self._active = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(64)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 8, 10)
        layout.setSpacing(12)

        self._avatar = Avatar(account.initials(), account.color, 40)
        layout.addWidget(self._avatar)

        text = QVBoxLayout()
        text.setSpacing(2)
        text.setContentsMargins(0, 0, 0, 0)
        self._name = QLabel(account.name)
        self._name.setStyleSheet("font-size: 13px; font-weight: 600;")
        subtitle = account.username or _relative(account.last_used)
        self._sub = QLabel(subtitle)
        self._sub.setStyleSheet(f"color: {PALETTE['text_faint']}; font-size: 11px;")
        text.addWidget(self._name)
        text.addWidget(self._sub)
        layout.addLayout(text, 1)

        self._menu_button = QToolButton()
        self._menu_button.setText("⋯")
        self._menu_button.clicked.connect(self._open_menu)
        layout.addWidget(self._menu_button, 0, Qt.AlignTop)

        self._refresh_style()

    def set_active(self, active: bool) -> None:
        self._active = active
        self._refresh_style()

    def update_account(self, account: Account) -> None:
        self._avatar.update_data(account.initials(), account.color)
        self._name.setText(account.name)
        self._sub.setText(account.username or _relative(account.last_used))

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
            self.switch_requested.emit(self.account_id)
        super().mousePressEvent(event)

    def _open_menu(self) -> None:
        menu = QMenu(self)
        menu.addAction("Switch to account", lambda: self.switch_requested.emit(self.account_id))
        menu.addAction("Edit", lambda: self.edit_requested.emit(self.account_id))
        menu.addAction("Copy cookie", lambda: self.copy_requested.emit(self.account_id))
        menu.addSeparator()
        menu.addAction("Delete", lambda: self.delete_requested.emit(self.account_id))
        menu.exec(self._menu_button.mapToGlobal(self._menu_button.rect().bottomRight()))
