import sys
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QGuiApplication,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)

ASSETS = Path(__file__).parent / "vyre" / "assets"


def _v_path(size: float) -> QPainterPath:
    points = [
        (0.19, 0.25), (0.35, 0.25), (0.50, 0.585),
        (0.65, 0.25), (0.81, 0.25), (0.50, 0.80),
    ]
    path = QPainterPath(QPointF(points[0][0] * size, points[0][1] * size))
    for x, y in points[1:]:
        path.lineTo(x * size, y * size)
    path.closeSubpath()
    return path


def render(size: int) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    radius = size * 0.235
    body = QRectF(0, 0, size, size)

    plate = QPainterPath()
    plate.addRoundedRect(body, radius, radius)

    base = QLinearGradient(0, 0, 0, size)
    base.setColorAt(0.0, QColor("#1a1a1e"))
    base.setColorAt(1.0, QColor("#0a0a0b"))
    painter.fillPath(plate, QBrush(base))

    glow = QRadialGradient(size * 0.5, size * 0.66, size * 0.55)
    glow.setColorAt(0.0, QColor(229, 72, 77, 130))
    glow.setColorAt(0.6, QColor(229, 72, 77, 24))
    glow.setColorAt(1.0, QColor(229, 72, 77, 0))
    painter.fillPath(plate, QBrush(glow))

    painter.save()
    painter.setClipPath(plate)
    edge = QLinearGradient(0, 0, 0, size)
    edge.setColorAt(0.0, QColor(255, 255, 255, 40))
    edge.setColorAt(0.12, QColor(255, 255, 255, 0))
    pen = QPen(QColor(255, 255, 255, 22))
    pen.setWidthF(max(size * 0.012, 1.0))
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    painter.drawRoundedRect(body.adjusted(1, 1, -1, -1), radius, radius)
    painter.restore()

    v = _v_path(size)

    shadow = QPainterPath(v)
    painter.save()
    painter.translate(0, size * 0.02)
    painter.fillPath(shadow, QColor(0, 0, 0, 120))
    painter.restore()

    v_grad = QLinearGradient(0, size * 0.22, 0, size * 0.82)
    v_grad.setColorAt(0.0, QColor("#ff6b70"))
    v_grad.setColorAt(0.5, QColor("#e5484d"))
    v_grad.setColorAt(1.0, QColor("#b5323a"))
    painter.fillPath(v, QBrush(v_grad))

    highlight = QPainterPath()
    highlight.moveTo(0.19 * size, 0.25 * size)
    highlight.lineTo(0.35 * size, 0.25 * size)
    highlight.lineTo(0.50 * size, 0.585 * size)
    highlight.lineTo(0.435 * size, 0.585 * size)
    highlight.closeSubpath()
    sheen = QLinearGradient(0, 0, size, 0)
    sheen.setColorAt(0.0, QColor(255, 255, 255, 70))
    sheen.setColorAt(1.0, QColor(255, 255, 255, 0))
    painter.fillPath(highlight, QBrush(sheen))

    painter.end()
    return pixmap


def main() -> None:
    QGuiApplication(sys.argv)
    ASSETS.mkdir(parents=True, exist_ok=True)
    render(512).save(str(ASSETS / "icon.png"), "PNG")
    render(256).save(str(ASSETS / "icon.ico"), "ICO")
    print(f"Wrote {ASSETS / 'icon.png'} and {ASSETS / 'icon.ico'}")


if __name__ == "__main__":
    main()
