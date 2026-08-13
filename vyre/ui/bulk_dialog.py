from PySide6.QtCore import Qt, QThread, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .. import generator, roblox
from ..models import Account
from ..theme import PALETTE
from .login_capture import LoginCaptureDialog, SignupCaptureDialog


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
        self._tabs.addTab(self._build_generate_tab(), "Generate")
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

    def _build_generate_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        hint = QLabel(
            "Generate credentials and automate account creation. The browser will prefill "
            "details (18+ age, selected gender, and credentials) and submit automatically. "
            "Simply solve any captcha if prompted."
        )
        hint.setObjectName("DialogHint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        row = QHBoxLayout()
        row.addWidget(QLabel("How many"))
        self._gen_count = QSpinBox()
        self._gen_count.setRange(1, 50)
        self._gen_count.setValue(5)
        row.addWidget(self._gen_count)
        row.addWidget(QLabel("Gender"))
        self._gen_gender = QComboBox()
        self._gen_gender.addItems(["Random", "Male", "Female"])
        row.addWidget(self._gen_gender)
        gen = QPushButton("Generate")
        gen.setObjectName("Primary")
        gen.clicked.connect(self._generate)
        row.addWidget(gen)
        row.addStretch(1)
        layout.addLayout(row)

        self._gen_box = QPlainTextEdit()
        self._gen_box.setPlaceholderText("Generated username:password lines appear here")
        self._gen_box.setFixedHeight(150)
        layout.addWidget(self._gen_box)

        buttons = QHBoxLayout()
        copy = QPushButton("Copy all")
        copy.clicked.connect(lambda: QGuiApplication.clipboard().setText(self._gen_box.toPlainText()))
        save = QPushButton("Save as drafts")
        save.clicked.connect(self._save_drafts)
        signup = QPushButton("Start signup queue")
        signup.setObjectName("Primary")
        signup.clicked.connect(self._signup_queue)
        buttons.addWidget(copy)
        buttons.addWidget(save)
        buttons.addWidget(signup)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        return widget

    def _generate(self) -> None:
        pairs = generator.generate_pairs(self._gen_count.value())
        self._gen_box.setPlainText("\n".join(f"{u}:{p}" for u, p in pairs))

    def _save_drafts(self) -> None:
        added = 0
        for line in self._gen_box.toPlainText().splitlines():
            line = line.strip()
            if not line or ":" not in line:
                continue
            user, _, password = line.partition(":")
            user, password = user.strip(), password.strip()
            if not user:
                continue
            self.accounts.append(
                Account(
                    name=user,
                    username=user,
                    note=f"Draft account\nUsername: {user}\nPassword: {password}",
                )
            )
            added += 1
        self._status.setStyleSheet(f"color: {PALETTE['success']}; font-size: 12px;")
        self._status.setText(f"Saved {added} draft(s). Create them on Roblox, then Edit to add the cookie.")

    def _signup_queue(self) -> None:
        pairs = []
        for line in self._gen_box.toPlainText().splitlines():
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
        gender_opt = self._gen_gender.currentText()
        added = 0
        for index, (user, password) in enumerate(pairs, start=1):
            self._status.setStyleSheet(f"color: {PALETTE['text_dim']}; font-size: 12px;")
            self._status.setText(f"Signing up {index} of {len(pairs)}: {user}")
            dialog = SignupCaptureDialog(user, password, gender_opt, self)
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
        self._status.setText(f"Created and imported {added} of {len(pairs)} account(s). Click Close to finish.")

    def _finish(self) -> None:
        if self.accounts:
            self.accept()
        else:
            self.reject()
