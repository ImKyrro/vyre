from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import multi_instance, wintools
from ..config import Config
from ..theme import PALETTE


class ToolsDialog(QDialog):
    def __init__(self, config: Config, parent=None):
        super().__init__(parent)
        self._config = config

        self.setWindowTitle("Roblox tools")
        self.setModal(True)
        self.setFixedWidth(460)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        title = QLabel("Roblox tools")
        title.setObjectName("DialogTitle")
        root.addWidget(title)

        root.addWidget(self._label("Multiple instances"))
        self._multi = QCheckBox("Allow more than one Roblox client to run at once")
        self._multi.setChecked(bool(self._config.get("allow_multi_instance")))
        self._multi.toggled.connect(self._toggle_multi)
        root.addWidget(self._multi)
        self._multi_status = QLabel("")
        self._multi_status.setObjectName("Faint")
        root.addWidget(self._multi_status)

        root.addWidget(self._label("Open Roblox windows"))
        self._count = QLabel("Detecting…")
        self._count.setObjectName("Muted")
        root.addWidget(self._count)

        grid = QGridLayout()
        grid.setSpacing(9)
        buttons = [
            ("Minimize all", lambda: self._act(wintools.minimize_all, "Minimized")),
            ("Restore all", lambda: self._act(wintools.restore_all, "Restored")),
            ("Arrange in grid", lambda: self._act(wintools.tile_grid, "Arranged")),
            ("Lower GPU/CPU use", lambda: self._act(lambda: wintools.set_low_priority(True), "Optimized")),
            ("Normal priority", lambda: self._act(lambda: wintools.set_low_priority(False), "Reset priority")),
            ("Close all", lambda: self._act(wintools.close_all, "Closing")),
        ]
        for index, (text, handler) in enumerate(buttons):
            button = QPushButton(text)
            button.setCursor(Qt.PointingHandCursor)
            button.clicked.connect(handler)
            if text == "Close all":
                button.setObjectName("Danger")
            grid.addWidget(button, index // 2, index % 2)
        root.addLayout(grid)

        hint = QLabel(
            "‘Lower GPU/CPU use’ drops the priority of running Roblox clients so background "
            "alts stop hogging your machine. ‘Arrange in grid’ tiles every open client across "
            "your screen."
        )
        hint.setObjectName("Faint")
        hint.setWordWrap(True)
        root.addWidget(hint)

        self._status = QLabel("")
        self._status.setObjectName("StatusText")
        root.addWidget(self._status)

        close = QPushButton("Done")
        close.setObjectName("Primary")
        close.clicked.connect(self.accept)
        root.addWidget(close)

        self._refresh_multi_status()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh_count)
        self._timer.start(2000)
        self._refresh_count()

    def _label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        return label

    def _toggle_multi(self, enabled: bool) -> None:
        if enabled:
            multi_instance.enable()
        else:
            multi_instance.disable()
        self._config.set("allow_multi_instance", enabled)
        self._config.save()
        self._refresh_multi_status()

    def _refresh_multi_status(self) -> None:
        if not multi_instance.is_supported():
            self._multi_status.setText("Only available on Windows.")
            self._multi.setEnabled(False)
            return
        if multi_instance.is_enabled():
            self._multi_status.setText("Active — launch your accounts and they will run side by side.")
        else:
            self._multi_status.setText("Off — Roblox will only allow one client at a time.")

    def _refresh_count(self) -> None:
        if not wintools.is_supported():
            self._count.setText("Window controls are only available on Windows.")
            return
        self._count.setText(f"{wintools.count()} Roblox window(s) open")

    def _act(self, func, verb: str) -> None:
        affected = func()
        self._status.setStyleSheet(f"color: {PALETTE['text_dim']}; font-size: 12px;")
        self._status.setText(f"{verb} {affected} window(s).")
        self._refresh_count()
