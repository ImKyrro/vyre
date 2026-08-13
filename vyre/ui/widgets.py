import json

from PySide6.QtCore import QByteArray, QRectF, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..theme import PALETTE, status_color

_cache: dict[str, QPixmap] = {}
HIDE_IMAGES = False
HIDE_INFO = False


def set_hide_images(value: bool) -> None:
    global HIDE_IMAGES
    HIDE_IMAGES = value


def set_hide_info(value: bool) -> None:
    global HIDE_INFO
    HIDE_INFO = value


class _Loader:
    def __init__(self):
        self._manager = QNetworkAccessManager()
        self._pending: dict[str, list] = {}

    def load(self, url: str, callback) -> None:
        if not url:
            return
        if url in _cache:
            callback(_cache[url])
            return
        if url in self._pending:
            self._pending[url].append(callback)
            return
        self._pending[url] = [callback]
        reply = self._manager.get(QNetworkRequest(QUrl(url)))
        reply.finished.connect(lambda: self._done(url, reply))

    def _done(self, url: str, reply) -> None:
        raw = bytes(reply.readAll())
        reply.deleteLater()
        callbacks = self._pending.pop(url, [])

        if "thumbnails.roblox.com" in url:
            image_url = self._extract_image_url(raw)
            if image_url:
                self._chain(url, image_url, callbacks)
            return

        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(raw))
        if pixmap.isNull():
            return
        _cache[url] = pixmap
        for callback in callbacks:
            callback(pixmap)

    def _extract_image_url(self, raw: bytes) -> str:
        try:
            payload = json.loads(raw.decode("utf-8"))
            items = payload.get("data", [])
            if items and items[0].get("state") == "Completed":
                return items[0].get("imageUrl", "")
        except (ValueError, KeyError, IndexError):
            return ""
        return ""

    def _chain(self, api_url: str, image_url: str, callbacks) -> None:
        def relay(pixmap):
            _cache[api_url] = pixmap
            for callback in callbacks:
                callback(pixmap)

        self.load(image_url, relay)


_loader = _Loader()


class Avatar(QWidget):
    def __init__(self, initials: str, color: str, diameter: int = 40, parent=None):
        super().__init__(parent)
        self._initials = initials
        self._color = color
        self._diameter = diameter
        self._pixmap: QPixmap | None = None
        self._status: str | None = None
        self.setFixedSize(diameter, diameter)

    def update_data(self, initials: str, color: str) -> None:
        self._initials = initials
        self._color = color
        self.update()

    def set_image_url(self, url: str) -> None:
        if not url or HIDE_IMAGES:
            return
        _loader.load(url, self._set_pixmap)

    def _set_pixmap(self, pixmap: QPixmap) -> None:
        self._pixmap = pixmap
        self.update()

    def set_status(self, kind: str | None) -> None:
        self._status = kind
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter()
        if not painter.begin(self):
            return
        painter.setRenderHint(QPainter.Antialiasing)
        d = self._diameter
        rect = QRectF(0, 0, d, d)

        clip = QPainterPath()
        clip.addEllipse(rect)
        painter.setClipPath(clip)

        if self._pixmap and not self._pixmap.isNull() and not HIDE_IMAGES:
            scaled = self._pixmap.scaled(
                d, d, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
            )
            painter.drawPixmap(0, 0, scaled)
        else:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(self._color)))
            painter.drawEllipse(rect)
            painter.setPen(QColor("#ffffff"))
            font = QFont("Segoe UI", max(6, int(d * 0.32)))
            font.setWeight(QFont.Bold)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignCenter, self._initials)

        painter.setClipping(False)
        if self._status:
            size = max(d * 0.28, 9)
            sx, sy = d - size, d - size
            painter.setPen(QPen(QColor(PALETTE["surface"]), 2))
            painter.setBrush(QBrush(QColor(status_color(self._status))))
            painter.drawEllipse(QRectF(sx, sy, size, size))
        painter.end()


class StatusDot(QWidget):
    def __init__(self, kind: str = "offline", parent=None):
        super().__init__(parent)
        self._kind = kind
        self.setFixedSize(10, 10)

    def set_kind(self, kind: str) -> None:
        self._kind = kind
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter()
        if not painter.begin(self):
            return
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(status_color(self._kind))))
        painter.drawEllipse(1, 1, 8, 8)
        painter.end()


class StatChip(QWidget):
    def __init__(self, value: str, label: str, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(1)
        self._value = QLabel(value)
        self._value.setObjectName("StatValue")
        self._label = QLabel(label.upper())
        self._label.setObjectName("StatLabel")
        layout.addWidget(self._value)
        layout.addWidget(self._label)

    def set_value(self, value: str) -> None:
        self._value.setText(value)


class ProcessingButton(QPushButton):
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._label = text
        self._frame = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def start_busy(self, text: str = "Working") -> None:
        self._busy_text = text
        self._frame = 0
        self.setEnabled(False)
        self._timer.start(300)
        self._tick()

    def stop_busy(self) -> None:
        self._timer.stop()
        self.setEnabled(True)
        self.setText(self._label)

    def set_label(self, text: str) -> None:
        self._label = text
        if not self._timer.isActive():
            self.setText(text)

    def _tick(self) -> None:
        dots = "." * (1 + self._frame % 3)
        self.setText(f"{self._busy_text}{dots}")
        self._frame += 1


class Toast(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAlignment(Qt.AlignCenter)
        self.hide()
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 180))
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
        y = parent.height() - self.height() - 30
        self.move(max(x, 12), max(y, 12))
