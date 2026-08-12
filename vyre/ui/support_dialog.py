from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..theme import PALETTE
from .widgets import Avatar

LTC_ADDRESS = "LSmU3RodML3p2HvwN2wU4HUJZSJddMxUJW"
DISCORD = "kyrro_real"


class SupportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Support Vyre")
        self.setModal(True)
        self.setFixedWidth(440)

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 26, 30, 26)
        root.setSpacing(8)

        badge = Avatar("K", PALETTE["accent"], 56)
        holder = QWidget()
        holder_layout = QVBoxLayout(holder)
        holder_layout.setContentsMargins(0, 0, 0, 0)
        holder_layout.addWidget(badge, alignment=Qt.AlignCenter)
        root.addWidget(holder)

        title = QLabel("Support Kyrro")
        title.setObjectName("DialogTitle")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        blurb = QLabel(
            "Vyre is made by Kyrro. If it helps you, a tip keeps it going. "
            "Game pass support is coming soon."
        )
        blurb.setObjectName("Muted")
        blurb.setAlignment(Qt.AlignCenter)
        blurb.setWordWrap(True)
        root.addWidget(blurb)
        root.addSpacing(10)

        root.addWidget(self._field_label("Litecoin (LTC)"))
        root.addLayout(self._copy_row(LTC_ADDRESS))

        root.addSpacing(6)
        root.addWidget(self._field_label("Discord"))
        root.addLayout(self._copy_row(DISCORD))

        root.addSpacing(14)
        close = QPushButton("Close")
        close.setObjectName("Primary")
        close.clicked.connect(self.accept)
        root.addWidget(close)

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        return label

    def _copy_row(self, value: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(8)
        field = QLineEdit(value)
        field.setReadOnly(True)
        field.setCursorPosition(0)
        row.addWidget(field, 1)
        copy = QPushButton("Copy")
        copy.setCursor(Qt.PointingHandCursor)
        copy.clicked.connect(lambda: QGuiApplication.clipboard().setText(value))
        row.addWidget(copy)
        return row
