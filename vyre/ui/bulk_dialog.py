from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .. import roblox
from ..models import Account
from ..theme import PALETTE
from .login_capture import LoginCaptureDialog


class _BulkCookieWorker(QThread):
    progress = Signal(int, int)
    finished_all = Signal(list)

    def __init__(self, cookies: list[str], parent=None):
        super().__init__(parent)
        self._cookies = cookies

    def run(self) -> None:
        results = []
        total = len(self._cookies)
        for index, cookie in enumerate(self._cookies, start=1):
            self.progress.emit(index, total)
            identity = roblox.fetch_identity(cookie)
            results.append((cookie, identity))
        self.finished_all.emit(results)


class BulkImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.accounts: list[Account] = []
        self._worker: _BulkCookieWorker | None = None

        self.setWindowTitle("Bulk import")
        self.setModal(True)
        self.setFixedWidth(500)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        title = QLabel("Bulk import accounts")
        title.setObjectName("DialogTitle")
        root.addWidget(title)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_cookie_tab(), "Cookies")
        self._tabs.addTab(self._build_cred_tab(), "Credentials")
        root.addWidget(self._tabs)

        self._status = QLabel("")
        self._status.setObjectName("StatusText")
        self._status.setWordWrap(True)
        root.addWidget(self._status)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        close = QPushButton("Close")
        close.clicked.connect(self._finish)
        buttons.addWidget(close)
        root.addLayout(buttons)

    def _build_cookie_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        hint = QLabel("Paste one .ROBLOSECURITY cookie per line. Vyre verifies each and names it automatically.")
        hint.setObjectName("DialogHint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._cookie_box = QPlainTextEdit()
        self._cookie_box.setPlaceholderText("cookie 1\ncookie 2\ncookie 3")
        self._cookie_box.setFixedHeight(150)
        layout.addWidget(self._cookie_box)

        self._cookie_button = QPushButton("Import cookies")
        self._cookie_button.setObjectName("Primary")
        self._cookie_button.clicked.connect(self._import_cookies)
        layout.addWidget(self._cookie_button, alignment=Qt.AlignLeft)
        return widget

    def _build_cred_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        hint = QLabel("Paste one username:password per line. Vyre opens each login prefilled — solve any puzzle and it captures the session. Credentials are never stored.")
        hint.setObjectName("DialogHint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._cred_box = QPlainTextEdit()
        self._cred_box.setPlaceholderText("username1:password1\nusername2:password2")
        self._cred_box.setFixedHeight(150)
        layout.addWidget(self._cred_box)

        self._cred_button = QPushButton("Start sign-in queue")
        self._cred_button.setObjectName("Primary")
        self._cred_button.clicked.connect(self._import_credentials)
        layout.addWidget(self._cred_button, alignment=Qt.AlignLeft)
        return widget

    def _import_cookies(self) -> None:
        lines = [line.strip() for line in self._cookie_box.toPlainText().splitlines()]
        cookies = [roblox.normalize_cookie(line) for line in lines if line]
        cookies = [cookie for cookie in cookies if roblox.is_valid_cookie(cookie)]
        if not cookies:
            self._status.setStyleSheet(f"color: {PALETTE['danger']}; font-size: 12px;")
            self._status.setText("No valid cookies found.")
            return
        self._cookie_button.setEnabled(False)
        self._status.setStyleSheet(f"color: {PALETTE['text_dim']}; font-size: 12px;")
        self._status.setText(f"Verifying {len(cookies)} cookies...")
        self._worker = _BulkCookieWorker(cookies, self)
        self._worker.progress.connect(
            lambda i, total: self._status.setText(f"Verifying {i} of {total}...")
        )
        self._worker.finished_all.connect(self._on_cookies_done)
        self._worker.start()

    def _on_cookies_done(self, results: list) -> None:
        self._cookie_button.setEnabled(True)
        added = 0
        for index, (cookie, identity) in enumerate(results, start=1):
            username = identity.get("username", "")
            account = Account(
                name=username or f"Account {index}",
                cookie=cookie,
                username=username,
                user_id=identity.get("user_id", ""),
            )
            self.accounts.append(account)
            added += 1
        self._status.setStyleSheet(f"color: {PALETTE['success']}; font-size: 12px;")
        self._status.setText(f"Imported {added} account(s). Click Close to finish.")

    def _import_credentials(self) -> None:
        pairs = []
        for line in self._cred_box.toPlainText().splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            user, _, password = line.partition(":")
            user, password = user.strip(), password.strip()
            if user and password:
                pairs.append((user, password))
        if not pairs:
            self._status.setStyleSheet(f"color: {PALETTE['danger']}; font-size: 12px;")
            self._status.setText("No valid username:password lines found.")
            return

        added = 0
        for index, (user, password) in enumerate(pairs, start=1):
            self._status.setStyleSheet(f"color: {PALETTE['text_dim']}; font-size: 12px;")
            self._status.setText(f"Signing in {index} of {len(pairs)}: {user}")
            dialog = LoginCaptureDialog(user, password, self)
            if dialog.exec() == QDialog.Accepted and dialog.cookie:
                identity = roblox.fetch_identity(dialog.cookie)
                username = identity.get("username", user)
                self.accounts.append(
                    Account(
                        name=username,
                        cookie=dialog.cookie,
                        username=username,
                        user_id=identity.get("user_id", ""),
                    )
                )
                added += 1
        self._status.setStyleSheet(f"color: {PALETTE['success']}; font-size: 12px;")
        self._status.setText(f"Captured {added} of {len(pairs)} account(s). Click Close to finish.")

    def _finish(self) -> None:
        if self.accounts:
            self.accept()
        else:
            self.reject()
