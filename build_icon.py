import sys
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QGuiApplication,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)

ASSETS = Path(__file__).parent / "vyre" / "assets"


def render(size: int) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.TextAntialiasing)

    radius = size * 0.24
    body = QRectF(0, 0, size, size)

    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0.0, QColor("#8f74ff"))
    gradient.setColorAt(0.55, QColor("#6a4bf0"))
    gradient.setColorAt(1.0, QColor("#4b6bff"))

    plate = QPainterPath()
    plate.addRoundedRect(body, radius, radius)
    painter.fillPath(plate, QBrush(gradient))

    sheen = QLinearGradient(0, 0, 0, size)
    sheen.setColorAt(0.0, QColor(255, 255, 255, 46))
    sheen.setColorAt(0.5, QColor(255, 255, 255, 0))
    painter.fillPath(plate, QBrush(sheen))

    pen = QPen(QColor(255, 255, 255, 235))
    pen.setWidthF(size * 0.11)
    pen.setCapStyle(Qt.RoundCap)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)

    left = QPointF(size * 0.28, size * 0.30)
    tip = QPointF(size * 0.50, size * 0.72)
    right = QPointF(size * 0.72, size * 0.30)
    path = QPainterPath(left)
    path.lineTo(tip)
    path.lineTo(right)
    painter.drawPath(path)

    painter.end()
    return pixmap


def main() -> None:
    QGuiApplication(sys.argv)
    ASSETS.mkdir(parents=True, exist_ok=True)

    render(512).save(str(ASSETS / "icon.png"), "PNG")

    sizes = [16, 24, 32, 48, 64, 128, 256]
    frames = [render(size) for size in sizes]
    icon_path = ASSETS / "icon.ico"
    frames[-1].save(str(icon_path), "ICO")

    print(f"Wrote {ASSETS / 'icon.png'} and {icon_path}")


if __name__ == "__main__":
    main()
