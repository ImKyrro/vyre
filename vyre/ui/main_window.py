from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QIcon
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QMessageBox,
    QWidget,
)

from ..storage import Vault
from .account_dialog import AccountDialog
from .browser import BrowserPanel
from .bulk_dialog import BulkImportDialog
from .sidebar import Sidebar
from .widgets import Toast


class MainWindow(QWidget):
    def __init__(self, vault: Vault, icon: QIcon, parent=None):
        super().__init__(parent)
        self._vault = vault

        self.setObjectName("Root")
        self.setWindowTitle("Vyre — Roblox Alt Account Manager")
        self.setWindowIcon(icon)
        self.setMinimumSize(760, 520)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.add_requested.connect(self._add_account)
        self._sidebar.bulk_requested.connect(self._bulk_import)
        self._sidebar.switch_requested.connect(self._switch_account)
        self._sidebar.edit_requested.connect(self._edit_account)
        self._sidebar.delete_requested.connect(self._delete_account)
        self._sidebar.copy_requested.connect(self._copy_cookie)
        layout.addWidget(self._sidebar)

        self._browser = BrowserPanel()
        layout.addWidget(self._browser, 1)

        self._toast = Toast(self)
        self._refresh()
        self._resize_compact()

    def _resize_compact(self) -> None:
        screen = QGuiApplication.primaryScreen().availableGeometry()
        width = min(max(int(screen.width() * 0.50), 900), screen.width() - 80)
        height = min(max(int(screen.height() * 0.62), 600), screen.height() - 80)
        self.resize(width, height)
        self.move(
            screen.x() + (screen.width() - width) // 2,
            screen.y() + (screen.height() - height) // 2,
        )

    def _refresh(self) -> None:
        self._sidebar.set_accounts(self._vault.accounts)

    def _add_account(self) -> None:
        dialog = AccountDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            account = dialog.result_account()
            self._vault.add(account)
            self._refresh()
            self._toast.show_message(f"Added {account.name}")

    def _bulk_import(self) -> None:
        dialog = BulkImportDialog(parent=self)
        if dialog.exec() == QDialog.Accepted and dialog.accounts:
            for account in dialog.accounts:
                self._vault.add(account)
            self._refresh()
            self._toast.show_message(f"Imported {len(dialog.accounts)} account(s)")

    def _edit_account(self, account_id: str) -> None:
        account = self._vault.get(account_id)
        if not account:
            return
        dialog = AccountDialog(account=account, parent=self)
        if dialog.exec() == QDialog.Accepted:
            updated = dialog.result_account()
            self._vault.update(updated)
            self._browser.reseed(updated)
            self._refresh()
            self._toast.show_message(f"Updated {updated.name}")

    def _delete_account(self, account_id: str) -> None:
        account = self._vault.get(account_id)
        if not account:
            return
        confirm = QMessageBox(self)
        confirm.setWindowTitle("Delete account")
        confirm.setText(f"Remove \"{account.name}\" from Vyre?")
        confirm.setInformativeText("Its saved session data will be erased.")
        confirm.setStandardButtons(QMessageBox.Cancel | QMessageBox.Yes)
        confirm.setDefaultButton(QMessageBox.Cancel)
        if confirm.exec() == QMessageBox.Yes:
            self._browser.forget(account_id)
            self._vault.remove(account_id)
            self._refresh()
            self._toast.show_message("Account removed")

    def _switch_account(self, account_id: str) -> None:
        account = self._vault.get(account_id)
        if not account:
            return
        account.touch()
        self._vault.update(account)
        self._sidebar.set_active(account_id)
        self._browser.load_account(account)
        self._toast.show_message(f"Switched to {account.name}")

    def _copy_cookie(self, account_id: str) -> None:
        account = self._vault.get(account_id)
        if not account:
            return
        QGuiApplication.clipboard().setText(account.cookie)
        self._toast.show_message("Cookie copied to clipboard")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._toast._reposition()
