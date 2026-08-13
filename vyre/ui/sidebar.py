from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ..models import Account
from ..theme import PALETTE
from . import icons
from .account_card import AccountCard


class Sidebar(QWidget):
    add_requested = Signal()
    bulk_requested = Signal()
    settings_requested = Signal()
    refresh_requested = Signal()
    update_triggered = Signal()
    support_requested = Signal()
    tools_requested = Signal()
    mass_launch_requested = Signal()
    reorder_requested = Signal(list)
    select_requested = Signal(str)
    edit_requested = Signal(str)
    delete_requested = Signal(str)
    copy_requested = Signal(str)
    favorite_requested = Signal(str)
    duplicate_requested = Signal(str)
    web_requested = Signal(str)
    launch_requested = Signal(str)
    health_requested = Signal(str)
    move_requested = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(310)
        self._cards: dict[str, AccountCard] = {}
        self._items: dict[str, QListWidgetItem] = {}
        self._active_id: str | None = None
        self._checked: set[str] = set()
        self._filter = ""
        self._suspend_reorder = False

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
        self._update_btn = QToolButton()
        self._update_btn.setIcon(icons.icon("download", PALETTE["accent"], 18))
        self._update_btn.setToolTip("Update available!")
        self._update_btn.setCursor(Qt.PointingHandCursor)
        self._update_btn.clicked.connect(self.update_triggered.emit)
        self._update_btn.hide()
        header.addWidget(self._update_btn, 0, Qt.AlignTop)
        self._settings = QToolButton()
        self._settings.setIcon(icons.icon("settings", PALETTE["text_dim"], 19))
        self._settings.setToolTip("Settings")
        self._settings.clicked.connect(self.settings_requested.emit)
        self._settings.setCursor(Qt.PointingHandCursor)
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
        self._select_all = QToolButton()
        self._select_all.setIcon(icons.icon("check", PALETTE["text_dim"], 16))
        self._select_all.setToolTip("Select all / none")
        self._select_all.setCursor(Qt.PointingHandCursor)
        self._select_all.clicked.connect(self._toggle_all)
        label_row.addWidget(self._select_all)
        self._refresh = QToolButton()
        self._refresh.setIcon(icons.icon("refresh", PALETTE["text_dim"], 16))
        self._refresh.setToolTip("Refresh presence")
        self._refresh.setCursor(Qt.PointingHandCursor)
        self._refresh.clicked.connect(self.refresh_requested.emit)
        label_row.addWidget(self._refresh)
        root.addLayout(label_row)

        self._list = QListWidget()
        self._list.setObjectName("AccountList")
        self._list.setSelectionMode(QAbstractItemView.SingleSelection)
        self._list.setDragDropMode(QAbstractItemView.InternalMove)
        self._list.setDefaultDropAction(Qt.MoveAction)
        self._list.setDropIndicatorShown(True)
        self._list.setFocusPolicy(Qt.NoFocus)
        self._list.setSpacing(2)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._list.setStyleSheet(
            "QListWidget#AccountList { background: transparent; border: none; }"
            "QListWidget#AccountList::item { border: none; }"
            "QListWidget#AccountList::item:selected { background: transparent; }"
        )
        self._list.itemClicked.connect(self._on_item_clicked)
        self._list.model().rowsMoved.connect(self._on_rows_moved)
        root.addWidget(self._list, 1)

        self._empty = QLabel("No accounts yet.\nAdd one to get started.")
        self._empty.setObjectName("Faint")
        self._empty.setAlignment(Qt.AlignCenter)
        root.addWidget(self._empty)

        self._action_bar = self._build_action_bar()
        root.addWidget(self._action_bar)

        footer = QHBoxLayout()
        footer.setContentsMargins(16, 8, 16, 14)
        footer.setSpacing(8)
        support = QPushButton("  Support")
        support.setIcon(icons.icon("heart", PALETTE["accent"], 16))
        support.setCursor(Qt.PointingHandCursor)
        support.clicked.connect(self.support_requested.emit)
        tools = QPushButton("  Roblox tools")
        tools.setIcon(icons.icon("tool", PALETTE["text_dim"], 16))
        tools.setCursor(Qt.PointingHandCursor)
        tools.clicked.connect(self.tools_requested.emit)
        footer.addWidget(support, 1)
        footer.addWidget(tools, 1)
        root.addLayout(footer)

    def _build_action_bar(self) -> QWidget:
        bar = QWidget()
        bar.setStyleSheet(
            f"background-color: {PALETTE['surface_alt']};"
            f" border-top: 1px solid {PALETTE['border']};"
        )
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(8)
        self._sel_label = QLabel("0 selected")
        self._sel_label.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {PALETTE['text']};")
        layout.addWidget(self._sel_label)
        layout.addStretch(1)
        clear = QPushButton("Clear")
        clear.setObjectName("Ghost")
        clear.setCursor(Qt.PointingHandCursor)
        clear.clicked.connect(self._clear_checks)
        layout.addWidget(clear)
        launch = QPushButton("  Launch")
        launch.setObjectName("Primary")
        launch.setIcon(icons.icon("rocket", "#ffffff", 16))
        launch.setCursor(Qt.PointingHandCursor)
        launch.clicked.connect(self.mass_launch_requested.emit)
        layout.addWidget(launch)
        bar.hide()
        return bar

    def _on_search(self, text: str) -> None:
        self._filter = text.strip().lower()
        self._apply_filter()

    def _apply_filter(self) -> None:
        for account_id, item in self._items.items():
            card = self._cards.get(account_id)
            matches = bool(card) and self._filter in card.name_text().lower()
            item.setHidden(not matches)

    def _connect_card(self, card: AccountCard) -> None:
        card.select_requested.connect(self.select_requested.emit)
        card.edit_requested.connect(self.edit_requested.emit)
        card.delete_requested.connect(self.delete_requested.emit)
        card.copy_requested.connect(self.copy_requested.emit)
        card.favorite_requested.connect(self.favorite_requested.emit)
        card.duplicate_requested.connect(self.duplicate_requested.emit)
        card.web_requested.connect(self.web_requested.emit)
        card.launch_requested.connect(self.launch_requested.emit)
        card.health_requested.connect(self.health_requested.emit)
        card.move_requested.connect(self.move_requested.emit)
        card.check_changed.connect(self._on_check)

    def set_accounts(self, accounts: list[Account]) -> None:
        self._suspend_reorder = True
        self._list.clear()
        self._cards.clear()
        self._items.clear()
        self._checked.clear()
        self._update_action_bar()

        for account in accounts:
            card = AccountCard(account)
            self._connect_card(card)
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 64))
            item.setData(Qt.UserRole, account.id)
            self._list.addItem(item)
            self._list.setItemWidget(item, card)
            self._cards[account.id] = card
            self._items[account.id] = item

        self._count.setText(str(len(accounts)))
        self._empty.setVisible(len(accounts) == 0)
        self._list.setVisible(len(accounts) > 0)
        if self._active_id:
            self.set_active(self._active_id)
        self._apply_filter()
        self._suspend_reorder = False

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        account_id = item.data(Qt.UserRole)
        if account_id:
            self.select_requested.emit(account_id)

    def _on_rows_moved(self, *args) -> None:
        if self._suspend_reorder:
            return
        order = []
        for row in range(self._list.count()):
            order.append(self._list.item(row).data(Qt.UserRole))
        QTimer.singleShot(0, lambda: self.reorder_requested.emit(order))

    def set_active(self, account_id: str | None) -> None:
        self._active_id = account_id
        for card_id, card in self._cards.items():
            card.set_active(card_id == account_id)

    def set_health(self, account_id: str, valid: bool) -> None:
        card = self._cards.get(account_id)
        if card:
            card.set_health(valid)

    def _on_check(self, account_id: str, checked: bool) -> None:
        if checked:
            self._checked.add(account_id)
        else:
            self._checked.discard(account_id)
        self._update_action_bar()

    def _update_action_bar(self) -> None:
        count = len(self._checked)
        self._sel_label.setText(f"{count} selected")
        self._action_bar.setVisible(count > 0)

    def _clear_checks(self) -> None:
        for card in self._cards.values():
            card.set_checked(False)
        self._checked.clear()
        self._update_action_bar()

    def _toggle_all(self) -> None:
        target = len(self._checked) < len(self._cards)
        for card in self._cards.values():
            card.set_checked(target)

    def checked_ids(self) -> list[str]:
        return [cid for cid in self._cards if cid in self._checked]

    def update_presence(self, presence: dict, accounts: list[Account]) -> None:
        by_user = {a.user_id: a.id for a in accounts if a.user_id}
        for user_id, info in presence.items():
            card_id = by_user.get(user_id)
            if card_id and card_id in self._cards:
                self._cards[card_id].update_presence(
                    info["kind"], info["label"], info["location"]
                )

    def show_update(self, visible: bool) -> None:
        self._update_btn.setVisible(visible)
