import json
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .. import system
from ..config import Config
from ..crypto import VaultError
from ..paths import BASE_DIR, PROFILES_DIR
from ..storage import Vault
from ..theme import PALETTE


class SettingsDialog(QDialog):
    applied = Signal()
    check_cookies_requested = Signal()
    check_updates_requested = Signal()
    debug_requested = Signal()

    def __init__(self, config: Config, vault: Vault, parent=None):
        super().__init__(parent)
        self._config = config
        self._vault = vault

        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(560, 560)

        root = QVBoxLayout(self)
        root.setContentsMargins(26, 22, 26, 22)
        root.setSpacing(12)

        title = QLabel("Settings")
        title.setObjectName("DialogTitle")
        root.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(self._general_tab(), "General")
        tabs.addTab(self._security_tab(), "Security")
        tabs.addTab(self._games_tab(), "Saved games")
        tabs.addTab(self._data_tab(), "Data")
        tabs.addTab(self._mcp_tab(), "MCP")
        tabs.addTab(self._about_tab(), "About")
        root.addWidget(tabs, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        close = QPushButton("Done")
        close.setObjectName("Primary")
        close.clicked.connect(self._save_and_close)
        buttons.addWidget(close)
        root.addLayout(buttons)

    def _label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        return label

    def _general_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self._confirm_delete = QCheckBox("Ask for confirmation before deleting an account")
        self._confirm_delete.setChecked(self._config.get("confirm_delete"))
        layout.addWidget(self._confirm_delete)

        self._tray = QCheckBox("Minimize to system tray instead of closing")
        self._tray.setChecked(self._config.get("minimize_to_tray"))
        layout.addWidget(self._tray)

        self._autostart = QCheckBox("Start Vyre when Windows starts")
        self._autostart.setChecked(self._config.get("start_with_windows"))
        layout.addWidget(self._autostart)

        self._web_external = QCheckBox("Open 'View on web' in my default browser")
        self._web_external.setChecked(self._config.get("open_web_external"))
        layout.addWidget(self._web_external)

        self._hide_images = QCheckBox("Hide avatars (show initials only)")
        self._hide_images.setChecked(self._config.get("hide_images"))
        layout.addWidget(self._hide_images)

        self._hide_info = QCheckBox("Hide account info (stats, user id, username)")
        self._hide_info.setChecked(self._config.get("hide_info"))
        layout.addWidget(self._hide_info)

        self._spoof_hwid = QCheckBox("Enable Hardware ID (HWID) spoofing for Roblox")
        self._spoof_hwid.setChecked(self._config.get("spoof_hwid"))
        layout.addWidget(self._spoof_hwid)

        layout.addSpacing(6)
        layout.addWidget(self._label("Presence"))
        self._presence_auto = QCheckBox("Automatically refresh presence")
        self._presence_auto.setChecked(self._config.get("presence_auto_refresh"))
        layout.addWidget(self._presence_auto)

        interval_row = QHBoxLayout()
        interval_row.addWidget(self._label("Refresh every"))
        self._interval = QSpinBox()
        self._interval.setRange(15, 900)
        self._interval.setSuffix(" s")
        self._interval.setValue(int(self._config.get("presence_interval")))
        interval_row.addWidget(self._interval)
        interval_row.addStretch(1)
        layout.addLayout(interval_row)
        layout.addStretch(1)
        return widget

    def _security_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(self._label("Master password"))
        hint = QLabel("Change the password that encrypts your vault.")
        hint.setObjectName("Muted")
        layout.addWidget(hint)
        change = QPushButton("Change master password")
        change.clicked.connect(self._change_password)
        layout.addWidget(change, alignment=Qt.AlignLeft)

        layout.addSpacing(10)
        auto_row = QHBoxLayout()
        auto_row.addWidget(self._label("Auto-lock after"))
        self._auto_lock = QSpinBox()
        self._auto_lock.setRange(0, 120)
        self._auto_lock.setSuffix(" min (0 = off)")
        self._auto_lock.setValue(int(self._config.get("auto_lock_minutes")))
        auto_row.addWidget(self._auto_lock)
        auto_row.addStretch(1)
        layout.addLayout(auto_row)
        layout.addStretch(1)
        return widget

    def _games_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        hint = QLabel("Saved games appear in the launcher for one-click launching.")
        hint.setObjectName("Muted")
        layout.addWidget(hint)

        self._games_list = QListWidget()
        for game in self._config.get("saved_games"):
            self._add_game_item(game.get("name", ""), game.get("place_id", ""))
        layout.addWidget(self._games_list, 1)

        row = QHBoxLayout()
        self._game_name = QLineEdit()
        self._game_name.setPlaceholderText("Name")
        self._game_place = QLineEdit()
        self._game_place.setPlaceholderText("Place ID or link")
        row.addWidget(self._game_name, 1)
        row.addWidget(self._game_place, 1)
        layout.addLayout(row)

        buttons = QHBoxLayout()
        add = QPushButton("Add")
        add.clicked.connect(self._add_game)
        remove = QPushButton("Remove selected")
        remove.clicked.connect(self._remove_game)
        buttons.addWidget(add)
        buttons.addWidget(remove)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        return widget

    def _add_game_item(self, name: str, place_id: str) -> None:
        item = QListWidgetItem(f"{name}  —  {place_id}")
        item.setData(Qt.UserRole, {"name": name, "place_id": place_id})
        self._games_list.addItem(item)

    def _add_game(self) -> None:
        from .. import launcher

        name = self._game_name.text().strip()
        place_id = launcher.parse_place_id(self._game_place.text())
        if name and place_id:
            self._add_game_item(name, place_id)
            self._game_name.clear()
            self._game_place.clear()

    def _remove_game(self) -> None:
        for item in self._games_list.selectedItems():
            self._games_list.takeItem(self._games_list.row(item))

    def _data_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        export = QPushButton("Export encrypted vault…")
        export.clicked.connect(self._export)
        layout.addWidget(export, alignment=Qt.AlignLeft)

        import_btn = QPushButton("Import from export…")
        import_btn.clicked.connect(self._import)
        layout.addWidget(import_btn, alignment=Qt.AlignLeft)

        folder = QPushButton("Open data folder")
        folder.clicked.connect(lambda: system.open_folder(BASE_DIR))
        layout.addWidget(folder, alignment=Qt.AlignLeft)

        check = QPushButton("Check all cookies")
        check.clicked.connect(self.check_cookies_requested.emit)
        layout.addWidget(check, alignment=Qt.AlignLeft)

        clear = QPushButton("Clear all browser sessions")
        clear.setObjectName("Danger")
        clear.clicked.connect(self._clear_sessions)
        layout.addWidget(clear, alignment=Qt.AlignLeft)

        info = QLabel(f"Data folder:\n{BASE_DIR}")
        info.setObjectName("Faint")
        info.setWordWrap(True)
        layout.addStretch(1)
        layout.addWidget(info)
        return widget

    def _mcp_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        hint = QLabel(
            "Vyre ships an MCP server so AI clients can list accounts, check presence, "
            "browse servers, and launch games. Add this to your MCP client config."
        )
        hint.setObjectName("Muted")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        project_dir = Path(__file__).resolve().parent.parent.parent
        try:
            cwd_display = str(Path("%USERPROFILE%") / project_dir.relative_to(Path.home()))
        except ValueError:
            cwd_display = "%USERPROFILE%\\vyre"
        snippet = {
            "mcpServers": {
                "vyre": {
                    "command": "python",
                    "args": ["-m", "vyre.mcp_server"],
                    "cwd": cwd_display,
                    "env": {"VYRE_MASTER_PASSWORD": "your-master-password"},
                }
            }
        }
        self._mcp_box = QPlainTextEdit(json.dumps(snippet, indent=2))
        self._mcp_box.setReadOnly(True)
        self._mcp_box.setFixedHeight(220)
        layout.addWidget(self._mcp_box)

        copy = QPushButton("Copy config")
        copy.clicked.connect(
            lambda: QGuiApplication.clipboard().setText(self._mcp_box.toPlainText())
        )
        layout.addWidget(copy, alignment=Qt.AlignLeft)
        layout.addStretch(1)
        return widget

    def _about_tab(self) -> QWidget:
        from .. import __version__

        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        version = QLabel(f"Vyre {__version__}")
        version.setObjectName("H2")
        layout.addWidget(version)

        maker = QLabel("Made by Kyrro — Roblox alt account manager.")
        maker.setObjectName("Muted")
        layout.addWidget(maker)

        layout.addSpacing(8)
        self._check_updates = QCheckBox("Check for updates on startup")
        self._check_updates.setChecked(bool(self._config.get("check_updates")))
        layout.addWidget(self._check_updates)

        check = QPushButton("View updates")
        check.clicked.connect(self._save_then_check_updates)
        layout.addWidget(check, alignment=Qt.AlignLeft)

        debug = QPushButton("Open debug console")
        debug.clicked.connect(self.debug_requested.emit)
        layout.addWidget(debug, alignment=Qt.AlignLeft)
        layout.addStretch(1)
        return widget

    def _save_then_check_updates(self, checked: bool = False) -> None:
        self._config.set("check_updates", self._check_updates.isChecked())
        self._config.save()
        self.check_updates_requested.emit()

    def _change_password(self) -> None:
        first, ok = QInputDialog.getText(
            self, "New password", "Enter a new master password:", QLineEdit.Password
        )
        if not ok or not first:
            return
        second, ok = QInputDialog.getText(
            self, "Confirm", "Confirm the new password:", QLineEdit.Password
        )
        if not ok:
            return
        if first != second:
            QMessageBox.warning(self, "Vyre", "Passwords do not match.")
            return
        self._vault.change_password(first)
        QMessageBox.information(self, "Vyre", "Master password updated.")

    def _export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export vault", "vyre-vault.vyre", "Vyre vault (*.vyre)")
        if not path:
            return
        password, ok = QInputDialog.getText(
            self, "Export", "Password to protect the export:", QLineEdit.Password
        )
        if not ok or not password:
            return
        try:
            self._vault.export_to(path, password)
            QMessageBox.information(self, "Vyre", "Vault exported.")
        except OSError:
            QMessageBox.warning(self, "Vyre", "Could not write the export file.")

    def _import(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import vault", "", "Vyre vault (*.vyre)")
        if not path:
            return
        password, ok = QInputDialog.getText(
            self, "Import", "Password of the export file:", QLineEdit.Password
        )
        if not ok or not password:
            return
        try:
            added = self._vault.import_from(path, password)
            QMessageBox.information(self, "Vyre", f"Imported {added} account(s).")
            self.applied.emit()
        except (VaultError, OSError, ValueError):
            QMessageBox.warning(self, "Vyre", "Import failed. Check the password and file.")

    def _clear_sessions(self) -> None:
        confirm = QMessageBox.question(
            self, "Vyre", "Clear all saved browser sessions? Accounts stay, but you may need to reload them."
        )
        if confirm != QMessageBox.Yes:
            return
        import shutil

        for child in PROFILES_DIR.glob("*"):
            if child.is_dir():
                shutil.rmtree(child, ignore_errors=True)
        QMessageBox.information(self, "Vyre", "Browser sessions cleared.")

    def _save_and_close(self) -> None:
        games = []
        for index in range(self._games_list.count()):
            games.append(self._games_list.item(index).data(Qt.UserRole))
        self._config.update({
            "confirm_delete": self._confirm_delete.isChecked(),
            "minimize_to_tray": self._tray.isChecked(),
            "start_with_windows": self._autostart.isChecked(),
            "open_web_external": self._web_external.isChecked(),
            "presence_auto_refresh": self._presence_auto.isChecked(),
            "presence_interval": self._interval.value(),
            "auto_lock_minutes": self._auto_lock.value(),
            "saved_games": games,
            "check_updates": self._check_updates.isChecked(),
            "hide_images": self._hide_images.isChecked(),
            "hide_info": self._hide_info.isChecked(),
            "spoof_hwid": self._spoof_hwid.isChecked(),
        })
        self._config.save()
        system.set_autostart(self._autostart.isChecked())
        self.applied.emit()
        self.accept()
