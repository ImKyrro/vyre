import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QDialog

from .config import Config
from .system import set_app_user_model_id
from .theme import stylesheet
from .ui.main_window import MainWindow
from .ui.unlock_dialog import UnlockDialog


def _icon() -> QIcon:
    path = Path(__file__).parent / "assets" / "icon.png"
    return QIcon(str(path)) if path.exists() else QIcon()


def run() -> int:
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
