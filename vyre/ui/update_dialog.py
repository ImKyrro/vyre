from PySide6.QtCore import Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from .. import __version__, changelog, updater
from ..theme import PALETTE
from . import icons


class _CheckWorker(QThread):
    done = Signal(dict)

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self._url = url

    def run(self) -> None:
        self.done.emit(updater.check(self._url))


class UpdateDialog(QDialog):
    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self._url = url
        self._worker = None
        self._download = ""

        self.setWindowTitle("Updates")
        self.setModal(True)
        self.setFixedWidth(460)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(10)

        title = QLabel("Updates")
        title.setObjectName("DialogTitle")
        root.addWidget(title)

        self._current = QLabel(f"Installed version: {__version__}")
        self._current.setObjectName("Muted")
        root.addWidget(self._current)

        self._status = QLabel("Checking for updates…")
        self._status.setStyleSheet("font-size: 14px; font-weight: 700;")
        root.addWidget(self._status)

        self._notes = QPlainTextEdit()
        self._notes.setReadOnly(True)
        self._notes.setFixedHeight(180)
        self._notes.hide()
        root.addWidget(self._notes)

        buttons = QHBoxLayout()
        self._recheck = QPushButton("  Check again")
        self._recheck.setIcon(icons.icon("refresh", PALETTE["text_dim"], 15))
        self._recheck.setCursor(Qt.PointingHandCursor)
        self._recheck.clicked.connect(self._check)
        buttons.addWidget(self._recheck)
        whats_new = QPushButton("  What's new")
        whats_new.setIcon(icons.icon("clock", PALETTE["text_dim"], 15))
        whats_new.setCursor(Qt.PointingHandCursor)
        whats_new.clicked.connect(self._show_changelog)
        buttons.addWidget(whats_new)
        buttons.addStretch(1)
        self._get = QPushButton("  Download update")
        self._get.setObjectName("Primary")
        self._get.setIcon(icons.icon("download", "#ffffff", 15))
        self._get.setCursor(Qt.PointingHandCursor)
        self._get.clicked.connect(self._open_download)
        self._get.hide()
        buttons.addWidget(self._get)
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        buttons.addWidget(close)
        root.addLayout(buttons)

        self._check()

    def _check(self, checked: bool = False) -> None:
        if not self._url:
            self._status.setText("No update source set")
            self._status.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {PALETTE['text_dim']};")
            self._current.setText("Add an update URL in Settings → About to enable updates.")
            self._recheck.setEnabled(False)
            return
        self._status.setText("Checking for updates…")
        self._status.setStyleSheet("font-size: 14px; font-weight: 700;")
        self._recheck.setEnabled(False)
        self._worker = _CheckWorker(self._url, self)
        self._worker.done.connect(self._on_result)
        self._worker.start()

    def _on_result(self, info: dict | None) -> None:
        self._recheck.setEnabled(True)
        if info is None:
            self._status.setText("Failed to check for updates")
            self._status.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {PALETTE['danger']};")
            self._notes.hide()
            self._get.hide()
            return
        if not info:
            self._status.setText("You're up to date")
            self._status.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {PALETTE['online']};")
            self._notes.hide()
            self._get.hide()
            return
        self._status.setText(f"Update available — v{info['version']}")
        self._status.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {PALETTE['accent']};")
        notes = info.get("notes") or "A new version is available."
        self._notes.setPlainText(notes)
        self._notes.show()
        self._download = info.get("url", "")
        self._get.setVisible(bool(self._download))

    def _show_changelog(self, checked: bool = False) -> None:
        self._notes.setPlainText(changelog.TEXT)
        self._notes.show()

    def _open_download(self, checked: bool = False) -> None:
        if self._download:
            QDesktopServices.openUrl(QUrl(self._download))
