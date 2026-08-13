import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QDialog

from . import logs
from .config import Config
from .system import set_app_user_model_id
from .theme import stylesheet
from .ui.main_window import MainWindow
from .ui.unlock_dialog import UnlockDialog


def _icon() -> QIcon:
    assets = Path(__file__).parent / "assets"
    ico = assets / "icon.ico"
    png = assets / "icon.png"
    icon = QIcon()
    if ico.exists():
        icon.addFile(str(ico))
    if png.exists():
        icon.addFile(str(png))
    return icon


def run() -> int:
    logs.install()
    set_app_user_model_id()
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

    config = Config.load()
    window = MainWindow(unlock.vault, config, icon)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(run())
