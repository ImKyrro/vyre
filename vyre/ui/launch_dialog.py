from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .. import launcher, roblox
from ..models import Account
from ..theme import PALETTE
from .widgets import ProcessingButton


class _ServerWorker(QThread):
    done = Signal(list)

    def __init__(self, place_id: str, parent=None):
        super().__init__(parent)
        self._place_id = place_id

    def run(self) -> None:
        result = roblox.list_servers(self._place_id)
        self.done.emit(result.get("servers", []))


class _LaunchWorker(QThread):
    done = Signal(bool, str)

    def __init__(self, cookie, place_id, job_id, access_code, link_code, parent=None):
        super().__init__(parent)
        self._args = (cookie, place_id, job_id, access_code, link_code)

    def run(self) -> None:
        ok, message = launcher.launch_as_account(*self._args)
        self.done.emit(ok, message)


class LaunchDialog(QDialog):
    def __init__(self, account: Account, saved_games: list, parent=None):
        super().__init__(parent)
        self._account = account
        self._saved = saved_games or []
        self._server_worker: _ServerWorker | None = None
        self._launch_worker: _LaunchWorker | None = None

        self.setWindowTitle("Launch a game")
        self.setModal(True)
        self.resize(560, 560)

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(12)

        title = QLabel(f"Launch as {account.username or account.name}")
        title.setObjectName("DialogTitle")
        root.addWidget(title)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_quick_tab(), "Quick launch")
        self._tabs.addTab(self._build_servers_tab(), "Server browser")
        root.addWidget(self._tabs, 1)

        self._status = QLabel("")
        self._status.setObjectName("StatusText")
        self._status.setWordWrap(True)
        root.addWidget(self._status)

    def _build_quick_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(9)

        if self._saved:
            layout.addWidget(self._label("Saved games"))
            self._saved_box = QComboBox()
            self._saved_box.addItem("Select a saved game…", "")
            for game in self._saved:
                self._saved_box.addItem(game.get("name", "Game"), game.get("place_id", ""))
            self._saved_box.currentIndexChanged.connect(self._on_saved)
            layout.addWidget(self._saved_box)

        layout.addWidget(self._label("Place ID or game link"))
        self._place = QLineEdit()
        self._place.setPlaceholderText("e.g. 2753915549 or roblox.com/games/…")
        layout.addWidget(self._place)

        layout.addWidget(self._label("Job ID (specific server, optional)"))
        self._job = QLineEdit()
        self._job.setPlaceholderText("Paste a server / job id to join that instance")
        layout.addWidget(self._job)

        layout.addWidget(self._label("Private server link or code (optional)"))
        self._private = QLineEdit()
        self._private.setPlaceholderText("Private server link or access code")
        layout.addWidget(self._private)

        self._launch_btn = ProcessingButton("Launch game")
        self._launch_btn.setObjectName("Primary")
        self._launch_btn.setCursor(Qt.PointingHandCursor)
        self._launch_btn.clicked.connect(self._launch_quick)
        layout.addWidget(self._launch_btn, alignment=Qt.AlignLeft)
        layout.addStretch(1)
        return widget

    def _build_servers_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(9)

        row = QHBoxLayout()
        self._server_place = QLineEdit()
        self._server_place.setPlaceholderText("Place ID or game link")
        row.addWidget(self._server_place, 1)
        self._load_btn = ProcessingButton("Load servers")
        self._load_btn.setCursor(Qt.PointingHandCursor)
        self._load_btn.clicked.connect(self._load_servers)
        row.addWidget(self._load_btn)
        layout.addLayout(row)

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Players", "Max", "Server ID"])
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        self._table.itemDoubleClicked.connect(lambda _: self._join_selected())
        layout.addWidget(self._table, 1)

        self._join_btn = ProcessingButton("Join selected server")
        self._join_btn.setObjectName("Primary")
        self._join_btn.setCursor(Qt.PointingHandCursor)
        self._join_btn.clicked.connect(self._join_selected)
        layout.addWidget(self._join_btn, alignment=Qt.AlignLeft)
        return widget

    def _label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        return label

    def _on_saved(self, index: int) -> None:
        place_id = self._saved_box.currentData()
        if place_id:
            self._place.setText(place_id)

    def _set_status(self, text: str, color: str) -> None:
        self._status.setStyleSheet(f"color: {color}; font-size: 12px;")
        self._status.setText(text)

    def _launch(self, place_id: str, job_id: str, access_code: str, link_code: str, button) -> None:
        if not place_id:
            self._set_status("Enter a Place ID or game link.", PALETTE["danger"])
            return
        button.start_busy("Launching")
        self._launch_worker = _LaunchWorker(
            self._account.cookie, place_id, job_id, access_code, link_code, self
        )
        self._launch_worker.done.connect(lambda ok, msg: self._on_launched(ok, msg, button))
        self._launch_worker.start()

    def _on_launched(self, ok: bool, message: str, button) -> None:
        button.stop_busy()
        self._set_status(message, PALETTE["online"] if ok else PALETTE["danger"])

    def _launch_quick(self) -> None:
        place_id = launcher.parse_place_id(self._place.text())
        job_id = self._job.text().strip()
        private = self._private.text().strip()
        access_code = launcher.parse_access_code(private) if private else ""
        self._launch(place_id, job_id, access_code, "", self._launch_btn)

    def _load_servers(self) -> None:
        place_id = launcher.parse_place_id(self._server_place.text())
        if not place_id:
            self._set_status("Enter a Place ID or game link.", PALETTE["danger"])
            return
        self._table.setRowCount(0)
        self._load_btn.start_busy("Loading")
        self._server_worker = _ServerWorker(place_id, self)
        self._server_worker.done.connect(self._on_servers)
        self._server_worker.start()

    def _on_servers(self, servers: list) -> None:
        self._load_btn.stop_busy()
        if not servers:
            self._set_status("No servers found (or the game is unlisted).", PALETTE["text_dim"])
            return
        self._table.setRowCount(len(servers))
        for row, server in enumerate(servers):
            playing = QTableWidgetItem(str(server.get("playing", 0)))
            maximum = QTableWidgetItem(str(server.get("maxPlayers", 0)))
            sid = QTableWidgetItem(str(server.get("id", "")))
            self._table.setItem(row, 0, playing)
            self._table.setItem(row, 1, maximum)
            self._table.setItem(row, 2, sid)
        self._set_status(f"Loaded {len(servers)} servers. Double-click one to join.", PALETTE["text_dim"])

    def _join_selected(self) -> None:
        row = self._table.currentRow()
        if row < 0:
            self._set_status("Select a server first.", PALETTE["danger"])
            return
        place_id = launcher.parse_place_id(self._server_place.text())
        job_id = self._table.item(row, 2).text()
        self._launch(place_id, job_id, "", "", self._join_btn)
