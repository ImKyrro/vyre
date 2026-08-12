import os
import subprocess
import sys
from pathlib import Path

APP_ID = "Vyre.RobloxAltManager"
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_RUN_NAME = "Vyre"


def set_app_user_model_id() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass


def _launch_target() -> str:
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    runtime = pythonw if pythonw.exists() else Path(sys.executable)
    script = Path(__file__).resolve().parent.parent / "Vyre.pyw"
    return f'"{runtime}" "{script}"'


def set_autostart(enabled: bool) -> bool:
    if sys.platform != "win32":
        return False
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            if enabled:
                winreg.SetValueEx(key, _RUN_NAME, 0, winreg.REG_SZ, _launch_target())
            else:
                try:
                    winreg.DeleteValue(key, _RUN_NAME)
                except FileNotFoundError:
                    pass
        return True
    except OSError:
        return False


def open_folder(path) -> None:
    target = str(path)
    if sys.platform == "win32":
        os.startfile(target)
    elif sys.platform == "darwin":
        subprocess.run(["open", target])
    else:
        subprocess.run(["xdg-open", target])
