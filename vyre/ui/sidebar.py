from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..models import Account
from .account_card import AccountCard


class Sidebar(QWidget):
    add_requested = Signal()
    bulk_requested = Signal()
    settings_requested = Signal()
    refresh_requested = Signal()
    select_requested = Signal(str)
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    copy_requested = Signal(str)
    favorite_requested = Signal(str)
    duplicate_requested = Signal(str)
    web_requested = Signal(str)
    launch_requested = Signal(str)
    move_requested = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(304)
        self._cards: dict[str, AccountCard] = {}
        self._active_id: str | None = None
        self._filter = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QHBoxLayout()
        header.setContentsMargins(20, 20, 14, 8)
        brand = QVBoxLayout()
        brand.setSpacing(1)
        mark = QLabel("VYRE")
        mark.setObjectName("Wordmark")
        tag = QLabel("ALT ACCOUNT MANAGER")
        tag.setObjectName("Tagline")
        brand.addWidget(mark)
        brand.addWidget(tag)
        header.addLayout(brand)
        header.addStretch(1)
        self._settings = QToolButton()
        self._settings.setText("⚙")
        self._settings.setToolTip("Settings")
        self._settings.setCursor(Qt.PointingHandCursor)
        self._settings.clicked.connect(self.settings_requested.emit)
        header.addWidget(self._settings, 0, Qt.AlignTop)
        root.addLayout(header)

        controls = QVBoxLayout()
        controls.setContentsMargins(16, 8, 16, 10)
        controls.setSpacing(9)
        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        add = QPushButton("+  Add account")
        add.setObjectName("Primary")
        add.setCursor(Qt.PointingHandCursor)
        add.clicked.connect(self.add_requested.emit)
        action_row.addWidget(add, 1)
        bulk = QPushButton("Bulk")
        bulk.setCursor(Qt.PointingHandCursor)
        bulk.setToolTip("Import many accounts at once")
        bulk.clicked.connect(self.bulk_requested.emit)
        action_row.addWidget(bulk)
        controls.addLayout(action_row)

        self._search = QLineEdit()
        self._search.setObjectName("Search")
        self._search.setPlaceholderText("Search accounts")
        self._search.textChanged.connect(self._on_search)
        controls.addWidget(self._search)
        root.addLayout(controls)

        label_row = QHBoxLayout()
        label_row.setContentsMargins(20, 4, 16, 4)
        self._section = QLabel("ACCOUNTS")
        self._section.setObjectName("SectionLabel")
        label_row.addWidget(self._section)
        self._count = QLabel("0")
        self._count.setObjectName("SectionLabel")
        label_row.addWidget(self._count)
        label_row.addStretch(1)
        self._refresh = QToolButton()
        self._refresh.setText("⟳")
        self._refresh.setToolTip("Refresh presence")
        self._refresh.setCursor(Qt.PointingHandCursor)
        self._refresh.clicked.connect(self.refresh_requested.emit)
        label_row.addWidget(self._refresh)
        root.addLayout(label_row)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        container = QWidget()
        self._list = QVBoxLayout(container)
        self._list.setContentsMargins(10, 4, 10, 16)
        self._list.setSpacing(3)
        self._list.addStretch(1)
        self._scroll.setWidget(container)
        root.addWidget(self._scroll, 1)

        self._empty = QLabel("No accounts yet.\nAdd one to get started.")
        self._empty.setObjectName("Faint")
        self._empty.setAlignment(Qt.AlignCenter)
        self._list.insertWidget(0, self._empty)

    def _on_search(self, text: str) -> None:
        self._filter = text.strip().lower()
        self._apply_filter()

    def _apply_filter(self) -> None:
        visible = 0
        for card in self._cards.values():
            matches = self._filter in card.name_text().lower()
            card.setVisible(matches)
            if matches:
                visible += 1
        self._empty.setVisible(visible == 0 and bool(self._cards) or not self._cards)

    def set_accounts(self, accounts: list[Account]) -> None:
        for card in self._cards.values():
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()

        for account in accounts:
            card = AccountCard(account)
            card.select_requested.connect(self.select_requested.emit)
            card.edit_requested.connect(self.edit_requested.emit)
            card.delete_requested.connect(self.delete_requested.emit)
            card.copy_requested.connect(self.copy_requested.emit)
            card.favorite_requested.connect(self.favorite_requested.emit)
            card.duplicate_requested.connect(self.duplicate_requested.emit)
            card.web_requested.connect(self.web_requested.emit)
            card.launch_requested.connect(self.launch_requested.emit)
            card.move_requested.connect(self.move_requested.emit)
            self._list.insertWidget(self._list.count() - 1, card)
            self._cards[account.id] = card

        self._count.setText(str(len(accounts)))
        self._empty.setVisible(len(accounts) == 0)
        if self._active_id:
            self.set_active(self._active_id)
        self._apply_filter()

    def set_active(self, account_id: str | None) -> None:
        self._active_id = account_id
        for card_id, card in self._cards.items():
            card.set_active(card_id == account_id)

    def update_presence(self, presence: dict, accounts: list[Account]) -> None:
        by_user = {a.user_id: a.id for a in accounts if a.user_id}
        for user_id, info in presence.items():
            card_id = by_user.get(user_id)
            if card_id and card_id in self._cards:
                self._cards[card_id].update_presence(
                    info["kind"], info["label"], info["location"]
                )
