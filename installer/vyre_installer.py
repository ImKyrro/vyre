import os
import subprocess
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from vyre.theme import PALETTE, stylesheet
from vyre.ui.widgets import Avatar

DOWNLOAD_URL = "https://github.com/ImKyrro/vyre/releases/latest/download/Vyre.exe"
INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))) / "Programs" / "Vyre"
INSTALL_PATH = INSTALL_DIR / "Vyre.exe"


class _Worker(QThread):
    progress = Signal(int, str)
    finished_ok = Signal(bool, str)

    def run(self) -> None:
        try:
            self.progress.emit(1, "Preparing environment...")
            try:
                subprocess.run(
                    ["powershell", "-NoProfile", "-Command", "Stop-Process -Name Vyre -Force -ErrorAction SilentlyContinue"],
                    capture_output=True,
                    check=False
                )
            except Exception:
                pass
            INSTALL_DIR.mkdir(parents=True, exist_ok=True)
            for p in INSTALL_DIR.glob("*.download"):
                try:
                    p.unlink()
                except OSError:
                    pass
            self.progress.emit(2, "Connecting to GitHub...")
            temp = INSTALL_DIR / "Vyre.download"
            request = urllib.request.Request(DOWNLOAD_URL, headers={"User-Agent": "VyreSetup"})
            import time
            with urllib.request.urlopen(request, timeout=30) as response:
                total = int(response.headers.get("Content-Length", 0))
                done = 0
                start_time = time.time()
                last_time = start_time
                last_done = 0
                speed = 0.0
                with open(temp, "wb") as handle:
                    while True:
                        chunk = response.read(262144)
                        if not chunk:
                            break
                        handle.write(chunk)
                        done += len(chunk)
                        now = time.time()
                        elapsed = now - last_time
                        if elapsed >= 0.5:
                            speed = (done - last_done) / elapsed / (1024 * 1024)
                            last_time = now
                            last_done = done
                        pct = int(done * 90 / total) if total else 45
                        mb = done / (1024 * 1024)
                        total_mb = total / (1024 * 1024) if total else 0.0
                        speed_str = f" ({speed:.2f} MB/s)" if speed > 0 else ""
                        self.progress.emit(min(90, pct), f"Downloading... {mb:.1f}/{total_mb:.1f} MB{speed_str}")
            self.progress.emit(92, "Installing...")
            if INSTALL_PATH.exists():
                try:
                    INSTALL_PATH.unlink()
                except OSError:
                    pass
            os.replace(temp, INSTALL_PATH)
            self.progress.emit(96, "Creating shortcuts...")
            _create_shortcuts()
            self.progress.emit(100, "Done")
            self.finished_ok.emit(True, "Vyre is installed.")
        except Exception as error:
            self.finished_ok.emit(False, f"Install failed: {error}")


def _create_shortcuts() -> None:
    desktop = Path(os.environ["USERPROFILE"]) / "Desktop"
    start_menu = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    for folder in (desktop, start_menu):
        try:
            folder.mkdir(parents=True, exist_ok=True)
            shortcut = folder / "Vyre.lnk"
            ps = (
                "$ws = New-Object -ComObject WScript.Shell; "
                f"$s = $ws.CreateShortcut('{shortcut}'); "
                f"$s.TargetPath = '{INSTALL_PATH}'; "
                f"$s.WorkingDirectory = '{INSTALL_DIR}'; "
                f"$s.IconLocation = '{INSTALL_PATH}'; "
                "$s.Description = 'Vyre - Roblox Alt Account Manager'; "
                "$s.Save()"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=False)
        except OSError:
            pass


def _check_requirements() -> list[dict]:
    missing = []
    system32 = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32"
    if not (system32 / "msvcp140.dll").exists():
        missing.append({
            "name": "Microsoft Visual C++ 2015-2022 Redistributable",
            "url": "https://aka.ms/vs/17/release/vc_redist.x64.exe",
        })
    return missing


class Installer(QWidget):
    def __init__(self):
        super().__init__()
        self._worker = None
        self.setObjectName("Root")
        self.setWindowTitle("Install Vyre")
        
        self._missing_reqs = _check_requirements()
        h = 440 if self._missing_reqs else 360
        self.setFixedSize(520, h)

        root = QVBoxLayout(self)
        root.setContentsMargins(40, 28, 40, 28)
        root.setSpacing(10)
        root.setAlignment(Qt.AlignTop)

        root.addWidget(Avatar("V", PALETTE["accent"], 60), alignment=Qt.AlignCenter)
        title = QLabel("Vyre")
        title.setObjectName("H1")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)
        sub = QLabel("Roblox Alt Account Manager")
        sub.setObjectName("Muted")
        sub.setAlignment(Qt.AlignCenter)
        root.addWidget(sub)
        root.addSpacing(10)

        if self._missing_reqs:
            req_widget = QWidget()
            req_layout = QVBoxLayout(req_widget)
            req_layout.setContentsMargins(12, 10, 12, 10)
            req_layout.setSpacing(5)
            req_widget.setStyleSheet(f"background-color: {PALETTE['surface_alt']}; border: 1px solid {PALETTE['border']}; border-radius: 8px;")
            warn_lbl = QLabel("⚠️ Missing required system component:")
            warn_lbl.setStyleSheet(f"color: {PALETTE['danger']}; font-weight: bold; font-size: 11px;")
            req_layout.addWidget(warn_lbl)
            for req in self._missing_reqs:
                item_lbl = QLabel(f"Vyre needs {req['name']} to run.")
                item_lbl.setStyleSheet("font-size: 11px; color: #9a9aa2;")
                req_layout.addWidget(item_lbl)
                dl_btn = QPushButton("Download and Install")
                dl_btn.setCursor(Qt.PointingHandCursor)
                dl_btn.setStyleSheet("font-size: 11px; padding: 4px 8px; background-color: #1c1c20;")
                dl_btn.clicked.connect(lambda _=False, url=req['url']: QDesktopServices.openUrl(QUrl(url)))
                req_layout.addWidget(dl_btn, alignment=Qt.AlignLeft)
            root.addWidget(req_widget)
            root.addSpacing(6)

        self._status = QLabel("Ready to install to your account (no admin needed).")
        self._status.setObjectName("Muted")
        self._status.setAlignment(Qt.AlignCenter)
        self._status.setWordWrap(True)
        root.addWidget(self._status)

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(8)
        root.addWidget(self._bar)
        root.addSpacing(6)

        self._button = QPushButton("Install Vyre")
        self._button.setObjectName("Primary")
        self._button.setCursor(Qt.PointingHandCursor)
        self._button.clicked.connect(self._install)
        root.addWidget(self._button)

        self._path = QLabel(str(INSTALL_PATH))
        self._path.setObjectName("Faint")
        self._path.setAlignment(Qt.AlignCenter)
        root.addWidget(self._path)

    def _install(self) -> None:
        self._button.setEnabled(False)
        self._button.setText("Installing…")
        self._worker = _Worker(self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_done)
        self._worker.start()

    def _on_progress(self, pct: int, text: str) -> None:
        self._bar.setValue(pct)
        self._status.setText(text)

    def _on_done(self, ok: bool, message: str) -> None:
        self._status.setText(message)
        if ok:
            self._button.setText("Launch Vyre")
            self._button.setEnabled(True)
            self._button.clicked.disconnect()
            self._button.clicked.connect(self._launch)
        else:
            self._button.setText("Retry")
            self._button.setEnabled(True)

    def _launch(self) -> None:
        try:
            os.startfile(str(INSTALL_PATH))
        except OSError:
            pass
        QApplication.instance().quit()


def _icon() -> QIcon:
    path = Path(__file__).resolve().parent.parent / "vyre" / "assets" / "icon.ico"
    return QIcon(str(path)) if path.exists() else QIcon()


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(stylesheet())
    icon = _icon()
    app.setWindowIcon(icon)
    window = Installer()
    window.setWindowIcon(icon)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
