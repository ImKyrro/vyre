from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from .. import logs, system
from ..theme import PALETTE
from . import icons


class DebugDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Debug console")
        self.setModal(False)
        self.resize(680, 460)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(10)

        header = QHBoxLayout()
        title = QLabel("Debug console")
        title.setObjectName("DialogTitle")
        header.addWidget(title)
        header.addStretch(1)
        self._auto = QLabel("live")
        self._auto.setObjectName("Faint")
        header.addWidget(self._auto)
        root.addLayout(header)

        self._view = QPlainTextEdit()
        self._view.setReadOnly(True)
        self._view.setStyleSheet(
            f"font-family: Consolas, monospace; font-size: 12px; background: {PALETTE['bg']};"
        )
        root.addWidget(self._view, 1)

        buttons = QHBoxLayout()
        copy = QPushButton("  Copy")
        copy.setIcon(icons.icon("copy", PALETTE["text_dim"], 15))
        copy.clicked.connect(lambda: QGuiApplication.clipboard().setText(self._view.toPlainText()))
        clear = QPushButton("  Clear")
        clear.setIcon(icons.icon("trash", PALETTE["text_dim"], 15))
        clear.clicked.connect(self._clear)
        open_log = QPushButton("  Open log file")
        open_log.setIcon(icons.icon("folder", PALETTE["text_dim"], 15))
        open_log.clicked.connect(lambda: system.open_folder(logs.log_file()))
        for button in (copy, clear, open_log):
            button.setCursor(Qt.PointingHandCursor)
        buttons.addWidget(copy)
        buttons.addWidget(clear)
        buttons.addWidget(open_log)
        buttons.addStretch(1)
        close = QPushButton("Close")
        close.setObjectName("Primary")
        close.clicked.connect(self.accept)
        buttons.addWidget(close)
        root.addLayout(buttons)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(1000)
        self._refresh()

    def _clear(self) -> None:
        logs.clear()
        self._refresh()

    def _refresh(self) -> None:
        lines = logs.get_lines()
        text = "\n".join(lines) if lines else "No log output yet."
        if text != self._view.toPlainText():
            self._view.setPlainText(text)
            self._view.verticalScrollBar().setValue(self._view.verticalScrollBar().maximum())
