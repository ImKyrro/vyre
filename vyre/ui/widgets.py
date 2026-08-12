from PySide6.QtCore import QRectF, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QLabel, QWidget

from ..theme import PALETTE


class Avatar(QWidget):
    def __init__(self, initials: str, color: str, diameter: int = 40, parent=None):
        super().__init__(parent)
        self._initials = initials
        self._color = color
        self._diameter = diameter
        self.setFixedSize(diameter, diameter)

    def update_data(self, initials: str, color: str) -> None:
        self._initials = initials
        self._color = color
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)

        rect = QRectF(0, 0, self._diameter, self._diameter)
        base = QColor(self._color)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(base))
        painter.drawEllipse(rect)

        ring = QColor(255, 255, 255, 28)
        pen = QPen(ring)
        pen.setWidthF(1.5)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        inset = rect.adjusted(0.75, 0.75, -0.75, -0.75)
        painter.drawEllipse(inset)

        painter.setPen(QColor("#ffffff"))
        font = QFont("Segoe UI", int(self._diameter * 0.32))
        font.setWeight(QFont.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, self._initials)
        painter.end()


class Toast(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAlignment(Qt.AlignCenter)
        self.hide()

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 160))
        self.setGraphicsEffect(shadow)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_message(self, text: str, duration: int = 2600) -> None:
        self.setText(text)
        self.adjustSize()
        self._reposition()
        self.show()
        self.raise_()
        self._timer.start(duration)

    def _reposition(self) -> None:
        parent = self.parentWidget()
        if not parent:
            return
        x = (parent.width() - self.width()) // 2
        y = parent.height() - self.height() - 28
        self.move(max(x, 12), max(y, 12))
