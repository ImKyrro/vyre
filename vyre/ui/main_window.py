from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtHttpServer import QHttpServer, QHttpServerRequest, QHttpServerResponse
from PySide6.QtNetwork import QTcpServer

from .. import multi_instance, roblox, updater
from ..config import Config
from ..models import Account
from ..storage import Vault
from .account_dialog import AccountDialog
from .browser import BrowserPanel
from .bulk_dialog import BulkImportDialog
from .detail_panel import DetailPanel
from .email_dialog import EmailDialog
from .launch_dialog import LaunchDialog
from .mass_launch_dialog import MassLaunchDialog
from .settings_dialog import SettingsDialog
from .sidebar import Sidebar
from .support_dialog import SupportDialog
from .tools_dialog import ToolsDialog
from .widgets import Toast, set_hide_images, set_hide_info


class _PresenceWorker(QThread):
    done = Signal(dict)

    def __init__(self, cookie: str, user_ids: list, parent=None):
        super().__init__(parent)
        self._cookie = cookie
        self._user_ids = user_ids

    def run(self) -> None:
        self.done.emit(roblox.fetch_presence(self._cookie, self._user_ids))


class _BackfillWorker(QThread):
    done = Signal(dict)

    def __init__(self, accounts, parent=None):
        super().__init__(parent)
        self._items = [(a.id, a.cookie, a.proxy) for a in accounts]

    def run(self) -> None:
        result = {}
        for account_id, cookie, proxy in self._items:
            identity = roblox.fetch_identity(cookie, proxy=proxy)
            if identity.get("user_id"):
                result[account_id] = identity
        self.done.emit(result)


class _HealthWorker(QThread):
    done = Signal(dict)

    def __init__(self, accounts, parent=None):
        super().__init__(parent)
        self._items = [(a.id, a.cookie, a.proxy) for a in accounts]

    def run(self) -> None:
        result = {}
        for account_id, cookie, proxy in self._items:
            result[account_id] = roblox.check_cookie(cookie, proxy=proxy)
        self.done.emit(result)


class _UpdateWorker(QThread):
    done = Signal(dict)

    def __init__(self, url: str, parent=None):
        super().__init__(parent)
        self._url = url

    def run(self) -> None:
        self.done.emit(updater.check(self._url))


class _AppUpdateWorker(QThread):
    progress = Signal(int)
    done = Signal(bool, str)

    def __init__(self, url: str, dest_path: str, parent=None):
        super().__init__(parent)
        self._url = url
        self._dest_path = dest_path

    def run(self):
        try:
            import urllib.request
            request = urllib.request.Request(self._url, headers={"User-Agent": "VyreUpdate"})
            with urllib.request.urlopen(request, timeout=30) as response:
                total = int(response.headers.get("Content-Length", 0))
                done = 0
                with open(self._dest_path, "wb") as handle:
                    while True:
                        chunk = response.read(262144)
                        if not chunk:
                            break
                        handle.write(chunk)
                        done += len(chunk)
                        pct = int(done * 100 / total) if total else 50
                        self.progress.emit(pct)
            self.done.emit(True, "")
        except Exception as err:
            self.done.emit(False, str(err))


class TitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(36)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 8, 0)
        layout.setSpacing(6)
        import os
        from PySide6.QtGui import QPixmap
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(base_dir, "assets", "icon.png")
        self._logo = QLabel()
        self._logo.setPixmap(QPixmap(logo_path).scaled(14, 14, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(self._logo)
        self._title = QLabel("VYRE")
        self._title.setStyleSheet("font-weight: 800; font-size: 11px; letter-spacing: 2px; color: #f2f2f3;")
        layout.addWidget(self._title)
        layout.addStretch(1)

        self._update_btn = QPushButton("Download Update")
        self._update_btn.setStyleSheet("background-color: #e5484d; color: #ffffff; border: none; border-radius: 4px; padding: 2px 10px; font-size: 11px; font-weight: bold; margin-right: 6px;")
        self._update_btn.setCursor(Qt.PointingHandCursor)
        self._update_btn.hide()
        self._update_btn.clicked.connect(self._on_update_clicked)
        layout.addWidget(self._update_btn)

        self._min_btn = QPushButton("—")
        self._min_btn.setObjectName("TitleMin")
        self._min_btn.setFixedSize(28, 28)
        self._min_btn.setCursor(Qt.PointingHandCursor)
        self._min_btn.clicked.connect(self._minimize)
        layout.addWidget(self._min_btn)
        self._max_btn = QPushButton("❑")
        self._max_btn.setObjectName("TitleMax")
        self._max_btn.setFixedSize(28, 28)
        self._max_btn.setCursor(Qt.PointingHandCursor)
        self._max_btn.clicked.connect(self._maximize)
        layout.addWidget(self._max_btn)
        self._close_btn = QPushButton("✕")
        self._close_btn.setObjectName("TitleClose")
        self._close_btn.setFixedSize(28, 28)
        self._close_btn.setCursor(Qt.PointingHandCursor)
        self._close_btn.clicked.connect(self._close)
        layout.addWidget(self._close_btn)
        self._drag_position = None

    def show_update(self, download_url: str, version: str) -> None:
        self._download_url = download_url
        self._new_version = version
        self._update_btn.setText(f"Update to v{version}")
        self._update_btn.show()

    def _on_update_clicked(self, checked: bool = False) -> None:
        self._update_btn.setEnabled(False)
        self._update_btn.setText("Downloading (0%)...")
        import sys
        from pathlib import Path
        dest = Path(sys.executable).parent / "Vyre.new"
        self._worker = _AppUpdateWorker(self._download_url, str(dest), self)
        self._worker.progress.connect(self._on_download_progress)
        self._worker.done.connect(self._on_download_done)
        self._worker.start()

    def _on_download_progress(self, percent: int) -> None:
        self._update_btn.setText(f"Downloading ({percent}%)...")

    def _on_download_done(self, success: bool, error: str) -> None:
        if success:
            self._update_btn.setEnabled(True)
            self._update_btn.setText("Restart Vyre")
            self._update_btn.setStyleSheet("background-color: #30a46c; color: #ffffff; border: none; border-radius: 4px; padding: 2px 10px; font-size: 11px; font-weight: bold; margin-right: 6px;")
            self._update_btn.clicked.disconnect()
            self._update_btn.clicked.connect(self._restart_app)
        else:
            self._update_btn.setEnabled(True)
            self._update_btn.setText(f"Failed: {error[:15]}")

    def _restart_app(self, checked: bool = False) -> None:
        import sys
        import os
        import subprocess
        from pathlib import Path
        from PySide6.QtWidgets import QApplication
        exe_path = Path(sys.executable)
        if exe_path.name.lower() == "vyre.exe":
            new_exe_path = exe_path.with_name("Vyre.new")
            pid = os.getpid()
            ps_cmd = (
                f"Start-Sleep -Seconds 1; "
                f"while (Get-Process -Id {pid} -ErrorAction SilentlyContinue) {{ Start-Sleep -Milliseconds 100 }}; "
                f"Move-Item -Path '{new_exe_path}' -Destination '{exe_path}' -Force; "
                f"Start-Process -FilePath '{exe_path}'"
            )
            try:
                subprocess.Popen(["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_cmd])
            except Exception:
                pass
        else:
            script = Path(__file__).resolve().parent.parent / "Vyre.pyw"
            try:
                subprocess.Popen([sys.executable, str(script)])
            except Exception:
                pass
        QApplication.quit()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_position is not None:
            self.window().move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_position = None

    def _minimize(self, checked: bool = False):
        self.window().showMinimized()

    def _maximize(self, checked: bool = False):
        w = self.window()
        if w.isMaximized():
            w.showNormal()
        else:
            w.showMaximized()

    def _close(self, checked: bool = False):
        self.window().close()

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter
        from PySide6.QtWidgets import QStyle, QStyleOption
        p = QPainter()
        if p.begin(self):
            opt = QStyleOption()
            opt.initFrom(self)
            self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)
            p.end()


class MainWindow(QWidget):
    def __init__(self, vault: Vault, config: Config, icon: QIcon, parent=None):
        super().__init__(parent)
        self._vault = vault
        self._config = config
        self._icon = icon
        self._selected: str | None = None
        self._presence_worker: _PresenceWorker | None = None
        self._backfill_worker: _BackfillWorker | None = None
        self._health_worker: _HealthWorker | None = None
        self._tray: QSystemTrayIcon | None = None

        self.setObjectName("Root")
        self.setWindowTitle("Vyre — Roblox Alt Account Manager")
        self.setWindowIcon(icon)
        self.setMinimumSize(820, 560)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._titlebar = TitleBar(self)
        root_layout.addWidget(self._titlebar)

        content = QWidget()
        layout = QHBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        root_layout.addWidget(content, 1)

        self._sidebar = Sidebar()
        self._wire_sidebar()
        layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        self._placeholder = self._build_placeholder()
        self._detail = DetailPanel(self._config)
        self._wire_detail()
        self._browser = BrowserPanel()
        self._browser.back_to_app.connect(self._back_to_app)
        self._stack.addWidget(self._placeholder)
        self._stack.addWidget(self._detail)
        self._stack.addWidget(self._browser)
        layout.addWidget(self._stack, 1)

        self._toast = Toast(self)
        self._presence_timer = QTimer(self)
        self._presence_timer.timeout.connect(self._refresh_presence)

        if self._config.get("allow_multi_instance"):
            multi_instance.enable()

        set_hide_images(bool(self._config.get("hide_images")))
        set_hide_info(bool(self._config.get("hide_info")))
        self._refresh()
        self._resize_compact()
        self._apply_config()
        QTimer.singleShot(400, self._backfill_identities)
        QTimer.singleShot(1200, self._refresh_presence)
        if self._config.get("check_updates"):
            QTimer.singleShot(2500, self._auto_check_updates)

        self._server = QHttpServer(self)
        self._tcp_server = QTcpServer(self)
        if self._tcp_server.listen(port=59124):
            self._server.bind(self._tcp_server)
            self._server.route("/", self._api_index)
            self._server.route("/add_account", self._api_add_account)
            self._server.route("/list_accounts", self._api_list_accounts)
            self._server.route("/launch_game", self._api_launch_game)

    def _wire_sidebar(self) -> None:
        s = self._sidebar
        s.add_requested.connect(self._add_account)
        s.bulk_requested.connect(self._bulk_import)
        s.settings_requested.connect(self._open_settings)
        s.update_triggered.connect(self._open_updates)
        s.refresh_requested.connect(self._refresh_presence)
        s.support_requested.connect(self._open_support)
        s.tools_requested.connect(self._open_tools)
        s.mass_launch_requested.connect(self._mass_launch)
        s.reorder_requested.connect(self._reorder)
        s.health_requested.connect(self._check_health)
        s.select_requested.connect(self._select_account)
        s.edit_requested.connect(self._edit_account)
        s.delete_requested.connect(self._delete_account)
        s.copy_requested.connect(self._copy_cookie)
        s.favorite_requested.connect(self._toggle_favorite)
        s.duplicate_requested.connect(self._duplicate_account)
        s.web_requested.connect(self._view_web)
        s.launch_requested.connect(self._launch_game)
        s.move_requested.connect(self._move_account)

    def _wire_detail(self) -> None:
        d = self._detail
        d.browse_requested.connect(self._browse_account)
        d.launch_requested.connect(self._launch_game)
        d.web_requested.connect(self._view_web)
        d.copy_cookie_requested.connect(self._copy_cookie)
        d.copy_profile_requested.connect(self._copy_profile)
        d.edit_requested.connect(self._edit_account)
        d.settings_web_requested.connect(self._open_email_dialog)
        d.health_requested.connect(self._check_health)
        d.join_requested.connect(self._join_game)
        d.vip_launch_requested.connect(self._launch_vip)

    def _build_placeholder(self) -> QWidget:
        widget = QWidget()
        widget.setObjectName("DetailPane")
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)
        title = QLabel("Select an account")
        title.setObjectName("EmptyTitle")
        title.setAlignment(Qt.AlignCenter)
        body = QLabel("Pick an account on the left to see its profile, presence, and actions.")
        body.setObjectName("Faint")
        body.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        layout.addWidget(body)
        return widget

    def _resize_compact(self) -> None:
        screen = QGuiApplication.primaryScreen().availableGeometry()
        width = min(max(int(screen.width() * 0.52), 900), screen.width() - 80)
        height = min(max(int(screen.height() * 0.64), 600), screen.height() - 80)
        self.resize(width, height)
        self.move(
            screen.x() + (screen.width() - width) // 2,
            screen.y() + (screen.height() - height) // 2,
        )

    def _refresh(self) -> None:
        self._sidebar.set_accounts(self._vault.sorted_accounts())
        if not self._vault.accounts:
            self._stack.setCurrentWidget(self._placeholder)
            self._selected = None

    def _apply_config(self) -> None:
        set_hide_images(bool(self._config.get("hide_images")))
        set_hide_info(bool(self._config.get("hide_info")))
        self._presence_timer.stop()
        if self._config.get("presence_auto_refresh"):
            interval = max(15, int(self._config.get("presence_interval"))) * 1000
            self._presence_timer.start(interval)
        if self._config.get("minimize_to_tray"):
            self._ensure_tray()
        elif self._tray:
            self._tray.hide()
            self._tray = None

    def _ensure_tray(self) -> None:
        if self._tray:
            return
        self._tray = QSystemTrayIcon(self._icon, self)
        self._tray.setToolTip("Vyre")
        menu = QMenu()
        show = QAction("Open Vyre", self)
        show.triggered.connect(self._restore)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self._quit)
        menu.addAction(show)
        menu.addAction(quit_action)
        self._tray.setContextMenu(menu)
        self._tray.activated.connect(
            lambda reason: self._restore() if reason == QSystemTrayIcon.Trigger else None
        )
        self._tray.show()

    def _restore(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _quit(self) -> None:
        if self._tray:
            self._tray.hide()
        QGuiApplication.instance().quit()

    def _account_or_warn(self, account_id: str) -> Account | None:
        account = self._vault.get(account_id)
        if not account:
            self._toast.show_message("Account not found")
        return account

    def _add_account(self) -> None:
        dialog = AccountDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            account = dialog.result_account()
            self._vault.add(account)
            self._refresh()
            self._toast.show_message(f"Added {account.name}")
            self._backfill_identities()
            self._refresh_presence()

    def _bulk_import(self) -> None:
        dialog = BulkImportDialog(parent=self)
        if dialog.exec() == QDialog.Accepted and dialog.accounts:
            for account in dialog.accounts:
                self._vault.add(account)
            self._refresh()
            self._toast.show_message(f"Imported {len(dialog.accounts)} account(s)")
            self._backfill_identities()
            self._refresh_presence()

    def _edit_account(self, account_id: str) -> None:
        account = self._account_or_warn(account_id)
        if not account:
            return
        dialog = AccountDialog(account=account, parent=self)
        if dialog.exec() == QDialog.Accepted:
            updated = dialog.result_account()
            self._vault.update(updated)
            self._browser.reseed(updated)
            self._refresh()
            if self._selected == account_id:
                self._detail.set_account(updated)
            self._toast.show_message(f"Updated {updated.name}")

    def _delete_account(self, account_id: str) -> None:
        account = self._account_or_warn(account_id)
        if not account:
            return
        if self._config.get("confirm_delete"):
            confirm = QMessageBox(self)
            confirm.setWindowTitle("Delete account")
            confirm.setText(f'Remove "{account.name}" from Vyre?')
            confirm.setInformativeText("Its saved session data will be erased.")
            confirm.setStandardButtons(QMessageBox.Cancel | QMessageBox.Yes)
            confirm.setDefaultButton(QMessageBox.Cancel)
            if confirm.exec() != QMessageBox.Yes:
                return
        self._browser.forget(account_id)
        self._vault.remove(account_id)
        if self._selected == account_id:
            self._selected = None
        self._refresh()
        self._toast.show_message("Account removed")

    def _duplicate_account(self, account_id: str) -> None:
        account = self._account_or_warn(account_id)
        if not account:
            return
        clone = Account(
            name=f"{account.name} copy",
            cookie=account.cookie,
            username=account.username,
            display_name=account.display_name,
            user_id=account.user_id,
            note=account.note,
            color=account.color,
        )
        self._vault.add(clone)
        self._refresh()
        self._toast.show_message("Account duplicated")

    def _toggle_favorite(self, account_id: str) -> None:
        account = self._account_or_warn(account_id)
        if not account:
            return
        account.favorite = not account.favorite
        self._vault.update(account)
        self._refresh()

    def _move_account(self, account_id: str, delta: int) -> None:
        self._vault.move(account_id, delta)
        self._refresh()

    def _select_account(self, account_id: str) -> None:
        account = self._account_or_warn(account_id)
        if not account:
            return
        self._selected = account_id
        self._sidebar.set_active(account_id)
        self._detail.set_account(account)
        self._stack.setCurrentWidget(self._detail)

    def _browse_account(self, account_id: str) -> None:
        account = self._account_or_warn(account_id)
        if not account:
            return
        account.touch()
        self._vault.update(account)
        self._selected = account_id
        self._sidebar.set_active(account_id)
        self._browser.load_account(account)
        self._stack.setCurrentWidget(self._browser)
        self._toast.show_message(f"Browsing as {account.name}")

    def _launch_game(self, account_id: str) -> None:
        account = self._account_or_warn(account_id)
        if not account:
            return
        dialog = LaunchDialog(account, self._config.get("saved_games"), self)
        dialog.exec()

    def _join_game(self, account_id: str, place_id: str, job_id: str) -> None:
        account = self._account_or_warn(account_id)
        if not account or not place_id:
            return
        from .. import launcher

        ok, message = launcher.launch_as_account(account.cookie, place_id, job_id, proxy=account.proxy)
        self._toast.show_message(message if ok else "Could not launch")

    def _launch_vip(self, account_id: str, link: str) -> None:
        account = self._account_or_warn(account_id)
        if not account or not link:
            return
        from .. import launcher
        access, code = launcher.parse_private_server(link)
        place = launcher.parse_place_id(link)
        if not place:
            self._toast.show_message("Invalid VIP server link")
            return
        self._toast.show_message(f"Launching VIP server for {account.name}…")
        import threading
        threading.Thread(
            target=launcher.launch_as_account,
            args=(account.cookie, place),
            kwargs={"access_code": access, "link_code": code, "proxy": account.proxy},
            daemon=True
        ).start()

    def _view_web(self, account_id: str) -> None:
        account = self._account_or_warn(account_id)
        if not account:
            return
        url = roblox.profile_url(account.user_id) if account.user_id else roblox.HOME_URL
        if self._config.get("open_web_external"):
            from PySide6.QtGui import QDesktopServices
            from PySide6.QtCore import QUrl

            QDesktopServices.openUrl(QUrl(url))
            self._toast.show_message("Opened in your browser")
            return
        self._selected = account_id
        self._sidebar.set_active(account_id)
        self._browser.load_account(account)
        self._browser.open_url(url)
        self._stack.setCurrentWidget(self._browser)

    def _copy_cookie(self, account_id: str) -> None:
        account = self._account_or_warn(account_id)
        if not account:
            return
        QGuiApplication.clipboard().setText(account.cookie)
        self._toast.show_message("Cookie copied to clipboard")

    def _copy_profile(self, account_id: str) -> None:
        account = self._account_or_warn(account_id)
        if not account or not account.user_id:
            self._toast.show_message("Verify the account first")
            return
        QGuiApplication.clipboard().setText(roblox.profile_url(account.user_id))
        self._toast.show_message("Profile link copied")

    def _open_settings(self) -> None:
        dialog = SettingsDialog(self._config, self._vault, self)
        dialog.applied.connect(self._on_settings_applied)
        dialog.check_cookies_requested.connect(self._check_all_health)
        dialog.check_updates_requested.connect(self._open_updates)
        dialog.debug_requested.connect(self._open_debug)
        dialog.exec()

    def _open_debug(self) -> None:
        from .debug_dialog import DebugDialog

        DebugDialog(self).show()

    def _on_settings_applied(self) -> None:
        self._apply_config()
        self._refresh()
        if self._selected and self._vault.get(self._selected):
            self._detail.set_account(self._vault.get(self._selected))

    def _refresh_presence(self) -> None:
        accounts = [a for a in self._vault.accounts if a.user_id]
        if not accounts:
            return
        requester = next((a for a in accounts if a.cookie), None)
        if not requester:
            return
        if self._presence_worker and self._presence_worker.isRunning():
            return
        user_ids = [a.user_id for a in accounts]
        self._presence_worker = _PresenceWorker(requester.cookie, user_ids, self)
        self._presence_worker.done.connect(self._on_presence)
        self._presence_worker.start()

    def _on_presence(self, presence: dict) -> None:
        self._sidebar.update_presence(presence, self._vault.accounts)

    def _backfill_identities(self) -> None:
        pending = [
            a for a in self._vault.accounts
            if a.cookie and not a.user_id
        ]
        if not pending:
            return
        if self._backfill_worker and self._backfill_worker.isRunning():
            return
        self._backfill_worker = _BackfillWorker(pending, self)
        self._backfill_worker.done.connect(self._on_backfill)
        self._backfill_worker.start()

    def _on_backfill(self, identities: dict) -> None:
        if not identities:
            return
        for account_id, identity in identities.items():
            account = self._vault.get(account_id)
            if not account:
                continue
            account.user_id = identity["user_id"]
            account.username = identity.get("username", account.username)
            account.display_name = identity.get("display_name", account.display_name)
            self._vault.update(account)
        self._refresh()
        self._refresh_presence()

    def _reorder(self, ordered_ids: list) -> None:
        self._vault.set_order(ordered_ids)

    def _open_updates(self) -> None:
        from .update_dialog import UpdateDialog

        UpdateDialog(updater.UPDATE_URL, self).exec()

    def _auto_check_updates(self) -> None:
        self._update_worker = _UpdateWorker(updater.UPDATE_URL, self)
        self._update_worker.done.connect(self._on_update)
        self._update_worker.start()

    def _on_update(self, info: dict) -> None:
        if not info:
            self._sidebar.show_update(False)
            return
        self._sidebar.show_update(True)
        self._titlebar.show_update(info["download_url"], info["version"])
        self._toast.show_message(f"Update available — v{info['version']}")

    def _cors_response(self, data, status=None) -> QHttpServerResponse:
        from PySide6.QtNetwork import QHttpHeaders
        headers = QHttpHeaders()
        headers.append("Access-Control-Allow-Origin", "*")
        headers.append("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        headers.append("Access-Control-Allow-Headers", "Content-Type")
        if status is not None:
            resp = QHttpServerResponse(data, status)
        else:
            resp = QHttpServerResponse(data)
        resp.setHeaders(headers)
        return resp

    def _api_index(self, request: QHttpServerRequest) -> QHttpServerResponse:
        if request.method() == QHttpServerRequest.Method.Options:
            return self._cors_response(QHttpServerResponse.StatusCode.Ok)
        import json
        from .. import __version__
        body = json.dumps({"app": "Vyre", "version": __version__})
        return self._cors_response(body, QHttpServerResponse.StatusCode.Ok)

    def _api_add_account(self, request: QHttpServerRequest) -> QHttpServerResponse:
        if request.method() == QHttpServerRequest.Method.Options:
            return self._cors_response(QHttpServerResponse.StatusCode.Ok)
        import json
        if request.method() != QHttpServerRequest.Method.Post:
            return self._cors_response("Method Not Allowed", QHttpServerResponse.StatusCode.MethodNotAllowed)
        try:
            body = bytes(request.body()).decode("utf-8")
            payload = json.loads(body)
        except Exception:
            return self._cors_response("Invalid JSON Payload", QHttpServerResponse.StatusCode.BadRequest)
        name = payload.get("name", "").strip()
        cookie = payload.get("cookie", "").strip()
        proxy = payload.get("proxy", "").strip()
        color = payload.get("color", "#e5484d").strip()
        private_server_link = payload.get("private_server_link", "").strip()
        private_servers = [{"name": "VIP Server 1", "link": private_server_link}] if private_server_link else []
        if not name or not cookie:
            return self._cors_response("Missing name or cookie", QHttpServerResponse.StatusCode.BadRequest)
        account = Account(name=name, cookie=cookie, proxy=proxy, color=color, private_servers=private_servers)
        self._vault.add(account)
        QTimer.singleShot(0, self, self._refresh)
        QTimer.singleShot(100, self, self._backfill_identities)
        QTimer.singleShot(500, self, lambda: self._toast.show_message(f"Added {name} via Extension"))
        return self._cors_response("Account added", QHttpServerResponse.StatusCode.Ok)

    def _api_list_accounts(self, request: QHttpServerRequest) -> QHttpServerResponse:
        if request.method() == QHttpServerRequest.Method.Options:
            return self._cors_response(QHttpServerResponse.StatusCode.Ok)
        import json
        accounts = self._vault.list()
        result = []
        for a in accounts:
            result.append({
                "id": a.id,
                "name": a.name,
                "username": a.username or "",
                "display_name": a.display_name or "",
                "user_id": a.user_id or "",
                "color": a.color or "#e5484d",
                "presence": getattr(a, "presence", None) or "offline",
            })
        body = json.dumps(result)
        return self._cors_response(body, QHttpServerResponse.StatusCode.Ok)

    def _api_launch_game(self, request: QHttpServerRequest) -> QHttpServerResponse:
        if request.method() == QHttpServerRequest.Method.Options:
            return self._cors_response(QHttpServerResponse.StatusCode.Ok)
        import json
        if request.method() != QHttpServerRequest.Method.Post:
            return self._cors_response("Method Not Allowed", QHttpServerResponse.StatusCode.MethodNotAllowed)
        try:
            body = bytes(request.body()).decode("utf-8")
            payload = json.loads(body)
        except Exception:
            return self._cors_response("Invalid JSON Payload", QHttpServerResponse.StatusCode.BadRequest)
        account_id = payload.get("account_id", "").strip()
        place_id = payload.get("place_id", "").strip()
        private_link = payload.get("private_server_link", "").strip()
        account = self._vault.get(account_id)
        if not account:
            return self._cors_response("Account not found", QHttpServerResponse.StatusCode.NotFound)
        from .. import launcher
        access_code, link_code = launcher.parse_private_server(private_link) if private_link else ("", "")
        if not place_id and private_link:
            place_id = launcher.parse_place_id(private_link)
        if not place_id:
            return self._cors_response("Missing place_id", QHttpServerResponse.StatusCode.BadRequest)
        import threading
        threading.Thread(
            target=launcher.launch_as_account,
            args=(account.cookie, place_id),
            kwargs={"access_code": access_code, "link_code": link_code, "proxy": account.proxy},
            daemon=True
        ).start()
        QTimer.singleShot(10, self, lambda: self._toast.show_message("Launching game via Extension"))
        return self._cors_response("Launch initiated", QHttpServerResponse.StatusCode.Ok)

    def _check_health(self, account_id: str) -> None:
        account = self._account_or_warn(account_id)
        if not account:
            return
        self._toast.show_message(f"Checking {account.name}…")
        self._run_health([account])

    def _check_all_health(self) -> None:
        accounts = [a for a in self._vault.accounts if a.cookie]
        if not accounts:
            return
        self._toast.show_message(f"Checking {len(accounts)} cookies…")
        self._run_health(accounts)

    def _run_health(self, accounts: list) -> None:
        if self._health_worker and self._health_worker.isRunning():
            return
        self._health_worker = _HealthWorker(accounts, self)
        self._health_worker.done.connect(self._on_health)
        self._health_worker.start()

    def _on_health(self, results: dict) -> None:
        expired = 0
        for account_id, valid in results.items():
            self._sidebar.set_health(account_id, valid)
            if not valid:
                expired += 1
        if len(results) == 1:
            valid = next(iter(results.values()))
            self._toast.show_message("Cookie is valid" if valid else "Cookie has expired")
        else:
            self._toast.show_message(f"{len(results) - expired} valid, {expired} expired")

    def _mass_launch(self) -> None:
        ids = self._sidebar.checked_ids()
        accounts = [self._vault.get(i) for i in ids]
        accounts = [a for a in accounts if a and a.cookie]
        if not accounts:
            self._toast.show_message("Select accounts first")
            return
        MassLaunchDialog(accounts, self._config.get("saved_games"), self._config, self).exec()

    def _open_support(self) -> None:
        SupportDialog(self).exec()

    def _open_tools(self) -> None:
        ToolsDialog(self._config, self).exec()

    def _open_email_dialog(self, account_id: str) -> None:
        account = self._account_or_warn(account_id)
        if not account:
            return
        dialog = EmailDialog(account, self)
        dialog.open_web_requested.connect(self._account_settings_web)
        dialog.exec()

    def _account_settings_web(self, account_id: str) -> None:
        account = self._account_or_warn(account_id)
        if not account:
            return
        self._selected = account_id
        self._sidebar.set_active(account_id)
        self._browser.load_account(account)
        self._browser.open_url(roblox.account_settings_url())
        self._stack.setCurrentWidget(self._browser)

    def _back_to_app(self) -> None:
        if self._selected and self._vault.get(self._selected):
            self._detail.set_account(self._vault.get(self._selected))
            self._stack.setCurrentWidget(self._detail)
        else:
            self._stack.setCurrentWidget(self._placeholder)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._toast._reposition()

    def closeEvent(self, event) -> None:
        if self._config.get("minimize_to_tray") and self._tray:
            event.ignore()
            self.hide()
            self._tray.showMessage("Vyre", "Still running in the tray.", self._icon, 2000)
        else:
            super().closeEvent(event)

    def paintEvent(self, event):
        from PySide6.QtGui import QPainter
        from PySide6.QtWidgets import QStyle, QStyleOption
        p = QPainter()
        if p.begin(self):
            opt = QStyleOption()
            opt.initFrom(self)
            self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)
            p.end()
