from PySide6.QtCore import Qt, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QStackedWidget,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from .. import multi_instance, roblox
from ..config import Config
from ..models import Account
from ..storage import Vault
from .account_dialog import AccountDialog
from .browser import BrowserPanel
from .bulk_dialog import BulkImportDialog
from .detail_panel import DetailPanel
from .launch_dialog import LaunchDialog
from .mass_launch_dialog import MassLaunchDialog
from .settings_dialog import SettingsDialog
from .sidebar import Sidebar
from .support_dialog import SupportDialog
from .tools_dialog import ToolsDialog
from .widgets import Toast


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
        self._items = [(a.id, a.cookie) for a in accounts]

    def run(self) -> None:
        result = {}
        for account_id, cookie in self._items:
            identity = roblox.fetch_identity(cookie)
            if identity.get("user_id"):
                result[account_id] = identity
        self.done.emit(result)


class MainWindow(QWidget):
    def __init__(self, vault: Vault, config: Config, icon: QIcon, parent=None):
        super().__init__(parent)
        self._vault = vault
        self._config = config
        self._icon = icon
        self._selected: str | None = None
        self._presence_worker: _PresenceWorker | None = None
        self._backfill_worker: _BackfillWorker | None = None
        self._tray: QSystemTrayIcon | None = None

        self.setObjectName("Root")
        self.setWindowTitle("Vyre — Roblox Alt Account Manager")
        self.setWindowIcon(icon)
        self.setMinimumSize(820, 560)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._sidebar = Sidebar()
        self._wire_sidebar()
        layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        self._placeholder = self._build_placeholder()
        self._detail = DetailPanel()
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

        self._refresh()
        self._resize_compact()
        self._apply_config()
        QTimer.singleShot(400, self._backfill_identities)
        QTimer.singleShot(1200, self._refresh_presence)

    def _wire_sidebar(self) -> None:
        s = self._sidebar
        s.add_requested.connect(self._add_account)
        s.bulk_requested.connect(self._bulk_import)
        s.settings_requested.connect(self._open_settings)
        s.refresh_requested.connect(self._refresh_presence)
        s.support_requested.connect(self._open_support)
        s.tools_requested.connect(self._open_tools)
        s.mass_launch_requested.connect(self._mass_launch)
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
        d.settings_web_requested.connect(self._account_settings_web)
        d.join_requested.connect(self._join_game)

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
        self._sidebar.set_accounts(self._vault.accounts)
        if not self._vault.accounts:
            self._stack.setCurrentWidget(self._placeholder)
            self._selected = None

    def _apply_config(self) -> None:
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

        ok, message = launcher.launch_as_account(account.cookie, place_id, job_id)
        self._toast.show_message(message if ok else "Could not launch")

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
        dialog.exec()

    def _on_settings_applied(self) -> None:
        self._refresh()
        self._apply_config()

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

    def _mass_launch(self) -> None:
        ids = self._sidebar.checked_ids()
        accounts = [self._vault.get(i) for i in ids]
        accounts = [a for a in accounts if a and a.cookie]
        if not accounts:
            self._toast.show_message("Select accounts first")
            return
        MassLaunchDialog(accounts, self._config.get("saved_games"), self).exec()

    def _open_support(self) -> None:
        SupportDialog(self).exec()

    def _open_tools(self) -> None:
        ToolsDialog(self._config, self).exec()

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
