from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..models import Account
from .account_card import AccountCard


class Sidebar(QWidget):
    add_requested = Signal()
    bulk_requested = Signal()
    switch_requested = Signal(str)
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    copy_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(300)
        self._cards: dict[str, AccountCard] = {}
        self._active_id: str | None = None
        self._filter = ""

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QVBoxLayout()
        header.setContentsMargins(20, 22, 20, 12)
        header.setSpacing(2)

        brand = QHBoxLayout()
        brand.setSpacing(0)
        mark = QLabel("Vy")
        mark.setObjectName("Wordmark")
        accent = QLabel("re")
        accent.setObjectName("Wordmark")
        accent.setProperty("class", "accent")
        accent.setObjectName("WordmarkAccent")
        accent.setStyleSheet("font-size: 22px; font-weight: 800; letter-spacing: 1px;")
        brand.addWidget(mark)
        brand.addWidget(accent)
        brand.addStretch(1)
        header.addLayout(brand)

        tag = QLabel("ACCOUNT MANAGER")
        tag.setObjectName("Tagline")
        header.addWidget(tag)
        root.addLayout(header)

        controls = QVBoxLayout()
        controls.setContentsMargins(16, 4, 16, 10)
        controls.setSpacing(10)

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
        label_row.setContentsMargins(20, 4, 20, 4)
        self._section = QLabel("ACCOUNTS")
        self._section.setObjectName("SectionLabel")
        label_row.addWidget(self._section)
        label_row.addStretch(1)
        self._count = QLabel("0")
        self._count.setObjectName("SectionLabel")
        label_row.addWidget(self._count)
        root.addLayout(label_row)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        container = QWidget()
        self._list = QVBoxLayout(container)
        self._list.setContentsMargins(10, 4, 10, 16)
        self._list.setSpacing(4)
        self._list.addStretch(1)
        self._scroll.setWidget(container)
        root.addWidget(self._scroll, 1)

        self._empty = QLabel("No accounts yet.\nAdd one to get started.")
        self._empty.setObjectName("EmptyBody")
        self._empty.setAlignment(Qt.AlignCenter)
        self._list.insertWidget(0, self._empty)

    def _on_search(self, text: str) -> None:
        self._filter = text.strip().lower()
        self._apply_filter()

    def _apply_filter(self) -> None:
        visible = 0
        for card in self._cards.values():
            account = card
            matches = self._filter in card._name.text().lower()
            card.setVisible(matches)
            if matches:
                visible += 1
        self._empty.setVisible(visible == 0)

    def set_accounts(self, accounts: list[Account]) -> None:
        for card in self._cards.values():
            card.setParent(None)
            card.deleteLater()
        self._cards.clear()

        for account in accounts:
            card = AccountCard(account)
            card.switch_requested.connect(self.switch_requested.emit)
            card.edit_requested.connect(self.edit_requested.emit)
            card.delete_requested.connect(self.delete_requested.emit)
            card.copy_requested.connect(self.copy_requested.emit)
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
