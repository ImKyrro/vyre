import time

from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .. import launcher, multi_instance, roblox
from ..models import Account
from ..theme import PALETTE
from .widgets import ProcessingButton


class _MassWorker(QThread):
    progress = Signal(int, int, str)
    finished_all = Signal(int)

    def __init__(self, accounts, mode, place_id, job_id, user_id, delay, parent=None):
        super().__init__(parent)
        self._accounts = accounts
        self._mode = mode
        self._place_id = place_id
        self._job_id = job_id
        self._user_id = user_id
        self._delay = delay

    def run(self) -> None:
        launched = 0
        total = len(self._accounts)
        for index, account in enumerate(self._accounts, start=1):
            self.progress.emit(index, total, account.name)
            if self._mode == "user":
                ok, _ = launcher.follow_user(account.cookie, self._user_id)
            else:
                ok, _ = launcher.launch_as_account(
                    account.cookie, self._place_id, self._job_id
                )
            if ok:
                launched += 1
            if index < total:
                time.sleep(max(1, self._delay))
        self.finished_all.emit(launched)


class MassLaunchDialog(QDialog):
    def __init__(self, accounts: list[Account], saved_games: list, config=None, parent=None):
        super().__init__(parent)
        self._accounts = accounts
        self._saved = saved_games or []
        self._config = config
        self._worker: _MassWorker | None = None

        self.setWindowTitle("Launch selected accounts")
        self.setModal(True)
        self.setFixedWidth(460)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(11)

        title = QLabel(f"Launch {len(accounts)} account(s)")
        title.setObjectName("DialogTitle")
        root.addWidget(title)

        self._mode_game = QRadioButton("Into a game")
        self._mode_game.setChecked(True)
        self._mode_user = QRadioButton("Join a user or friend")
        self._mode_game.toggled.connect(self._update_mode)
        root.addWidget(self._mode_game)

        self._game_box = QWidget()
        game_layout = QVBoxLayout(self._game_box)
        game_layout.setContentsMargins(16, 0, 0, 0)
        game_layout.setSpacing(8)
        if self._saved:
            self._saved_box = QComboBox()
            self._saved_box.addItem("Saved game…", "")
            for game in self._saved:
                self._saved_box.addItem(game.get("name", "Game"), game.get("place_id", ""))
            self._saved_box.currentIndexChanged.connect(
                lambda _: self._place.setText(self._saved_box.currentData() or self._place.text())
            )
            game_layout.addWidget(self._saved_box)
        self._place = QLineEdit()
        self._place.setPlaceholderText("Place ID or game link")
        game_layout.addWidget(self._place)
        self._job = QLineEdit()
        self._job.setPlaceholderText("Job ID (same server for everyone, optional)")
        game_layout.addWidget(self._job)
        root.addWidget(self._game_box)

        root.addWidget(self._mode_user)
        self._user_box = QWidget()
        user_layout = QVBoxLayout(self._user_box)
        user_layout.setContentsMargins(16, 0, 0, 0)
        self._user = QLineEdit()
        self._user.setPlaceholderText("Username or user ID to follow into their game")
        user_layout.addWidget(self._user)
        root.addWidget(self._user_box)

        delay_row = QHBoxLayout()
        delay_row.addWidget(self._label("Stagger each launch by"))
        self._delay = QSpinBox()
        self._delay.setRange(1, 60)
        self._delay.setValue(6)
        self._delay.setSuffix(" s")
        delay_row.addWidget(self._delay)
        delay_row.addStretch(1)
        root.addLayout(delay_row)

        self._multi = QCheckBox("Allow multiple instances (needed to run more than one)")
        self._multi.setChecked(True)
        self._multi.setEnabled(multi_instance.is_supported())
        root.addWidget(self._multi)

        warn = QLabel("Close any Roblox windows already open before launching, or the first one may get replaced.")
        warn.setObjectName("Faint")
        warn.setWordWrap(True)
        root.addWidget(warn)

        self._status = QLabel("")
        self._status.setObjectName("StatusText")
        self._status.setWordWrap(True)
        root.addWidget(self._status)

        self._launch = ProcessingButton("Launch all")
        self._launch.setObjectName("Primary")
        self._launch.setCursor(Qt.PointingHandCursor)
        self._launch.clicked.connect(self._start)
        root.addWidget(self._launch)

        self._update_mode()

    def _label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        return label

    def _update_mode(self) -> None:
        game = self._mode_game.isChecked()
        self._game_box.setVisible(game)
        self._user_box.setVisible(not game)

    def _set_status(self, text: str, color: str) -> None:
        self._status.setStyleSheet(f"color: {color}; font-size: 12px;")
        self._status.setText(text)

    def _start(self) -> None:
        if self._multi.isChecked():
            multi_instance.enable()
            if self._config is not None:
                self._config.set("allow_multi_instance", True)
                self._config.save()
        if self._mode_user.isChecked():
            user_id = roblox.resolve_username(self._user.text())
            if not user_id:
                self._set_status("Could not find that user.", PALETTE["danger"])
                return
            args = ("user", "", "", user_id)
        else:
            place_id = launcher.parse_place_id(self._place.text())
            if not place_id:
                self._set_status("Enter a Place ID or game link.", PALETTE["danger"])
                return
            args = ("game", place_id, self._job.text().strip(), "")

        self._launch.start_busy("Launching")
        self._worker = _MassWorker(
            self._accounts, args[0], args[1], args[2], args[3], self._delay.value(), self
        )
        self._worker.progress.connect(
            lambda i, total, name: self._set_status(f"Launching {i}/{total}: {name}", PALETTE["text_dim"])
        )
        self._worker.finished_all.connect(self._done)
        self._worker.start()

    def _done(self, launched: int) -> None:
        self._launch.stop_busy()
        self._set_status(f"Launched {launched} of {len(self._accounts)} account(s).", PALETTE["online"])
        if launched:
            QTimer.singleShot(1400, self.accept)
