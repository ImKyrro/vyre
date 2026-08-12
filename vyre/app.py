import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QDialog

from pathlib import Path

from .theme import stylesheet
from .ui.main_window import MainWindow
from .ui.unlock_dialog import UnlockDialog


def _icon() -> QIcon:
    path = Path(__file__).parent / "assets" / "icon.png"
    return QIcon(str(path)) if path.exists() else QIcon()


def run() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Vyre")
    app.setApplicationDisplayName("Vyre")
    app.setStyleSheet(stylesheet())

    icon = _icon()
    app.setWindowIcon(icon)

    unlock = UnlockDialog()
    unlock.setWindowIcon(icon)
    if unlock.exec() != QDialog.Accepted or unlock.vault is None:
        return 0

    window = MainWindow(unlock.vault, icon)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
