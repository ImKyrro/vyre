import sys
import traceback
from collections import deque
from datetime import datetime

from .paths import BASE_DIR

_LOG_FILE = BASE_DIR / "vyre.log"
_buffer: deque = deque(maxlen=500)
_installed = False


def log(message: str, level: str = "INFO") -> None:
    stamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{stamp}] {level}: {message}"
    _buffer.append(line)
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError:
        pass


def get_lines() -> list:
    return list(_buffer)


def clear() -> None:
    _buffer.clear()


def log_file() -> str:
    return str(_LOG_FILE)


def _excepthook(exc_type, exc_value, exc_tb) -> None:
    text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    log(text.strip(), "ERROR")
    sys.__excepthook__(exc_type, exc_value, exc_tb)


def _qt_handler(mode, context, message) -> None:
    log(str(message), "QT")


def install() -> None:
    global _installed
    if _installed:
        return
    _installed = True
    sys.excepthook = _excepthook
    try:
        from PySide6.QtCore import qInstallMessageHandler

        qInstallMessageHandler(_qt_handler)
    except Exception:
        pass
    log("Vyre started", "INFO")
