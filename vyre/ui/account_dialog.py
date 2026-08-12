from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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

SWATCHES = [
    "#7C5CFF", "#4b6bff", "#3fb87f", "#f0a63f",
    "#f0566a", "#e05cc8", "#41c7d8", "#8b93a6",
]


class _IdentityWorker(QThread):
    done = Signal(dict)

    def __init__(self, cookie: str, parent=None):
        super().__init__(parent)
        self._cookie = cookie

    def run(self) -> None:
        self.done.emit(roblox.fetch_identity(self._cookie))


class _Swatch(QPushButton):
    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self.color = color
        self.setFixedSize(26, 26)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self._apply(False)

    def _apply(self, selected: bool) -> None:
        border = "#ffffff" if selected else "transparent"
        width = 2 if selected else 0
        self.setStyleSheet(
            f"QPushButton {{ background-color: {self.color}; border-radius: 13px;"
            f" border: {width}px solid {border}; }}"
        )

    def setChecked(self, value: bool) -> None:
        super().setChecked(value)
        self._apply(value)


class AccountDialog(QDialog):
    def __init__(self, account: Account | None = None, parent=None):
        super().__init__(parent)
        self._editing = account is not None
        self._account = account or Account(name="")
        self._worker: _IdentityWorker | None = None

        self.setWindowTitle("Edit account" if self._editing else "Add account")
        self.setModal(True)
        self.setFixedWidth(480)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(14)

        title = QLabel("Edit account" if self._editing else "Add account")
        title.setObjectName("DialogTitle")
        root.addWidget(title)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_cookie_tab(), "Paste cookie")
        self._tabs.addTab(self._build_signin_tab(), "Sign in")
        self._tabs.addTab(self._build_credentials_tab(), "Username")
        root.addWidget(self._tabs)

        self._identity = QLabel("")
        self._identity.setObjectName("StatusText")
        self._identity.setWordWrap(True)
        root.addWidget(self._identity)

        root.addWidget(self._label("Display name"))
        self._name = QLineEdit(self._account.name)
        self._name.setPlaceholderText("e.g. Main, Trading alt, Test account")
        root.addWidget(self._name)

        root.addWidget(self._label("Accent color"))
        swatch_row = QHBoxLayout()
        swatch_row.setSpacing(8)
        self._swatches: list[_Swatch] = []
        for color in SWATCHES:
            swatch = _Swatch(color)
            swatch.clicked.connect(lambda _=False, c=color: self._pick_color(c))
            swatch_row.addWidget(swatch)
            self._swatches.append(swatch)
        swatch_row.addStretch(1)
        root.addLayout(swatch_row)
        self._pick_color(self._account.color)

        root.addWidget(self._label("Note (optional)"))
        self._note = QLineEdit(self._account.note)
        self._note.setPlaceholderText("Anything you want to remember")
        root.addWidget(self._note)

        self._error = QLabel("")
        self._error.setStyleSheet(f"color: {PALETTE['danger']}; font-size: 12px;")
        self._error.setVisible(False)
        root.addWidget(self._error)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        save = QPushButton("Save account")
        save.setObjectName("Primary")
        save.clicked.connect(self._save)
        buttons.addWidget(save)
        root.addLayout(buttons)

    def _label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        return label

    def _build_cookie_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        layout.addWidget(self._label("Roblox cookie (.ROBLOSECURITY)"))
        self._cookie = QPlainTextEdit()
        self._cookie.setPlaceholderText("Paste the .ROBLOSECURITY value here")
        self._cookie.setFixedHeight(90)
        if self._account.cookie:
            self._cookie.setPlainText(self._account.cookie)
        layout.addWidget(self._cookie)

        verify = QPushButton("Verify cookie")
        verify.clicked.connect(lambda: self._verify(self._cookie.toPlainText()))
        layout.addWidget(verify, alignment=Qt.AlignLeft)
        return widget

    def _build_signin_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 18, 14, 18)
        layout.setSpacing(10)

        info = QLabel("Open a secure Roblox login window. When you sign in, Vyre grabs the session for you.")
        info.setObjectName("DialogHint")
        info.setWordWrap(True)
        layout.addWidget(info)

        button = QPushButton("Open login window")
        button.setObjectName("Primary")
        button.clicked.connect(lambda: self._capture())
        layout.addWidget(button, alignment=Qt.AlignLeft)
        layout.addStretch(1)
        return widget

    def _build_credentials_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        layout.addWidget(self._label("Username"))
        self._cred_user = QLineEdit()
        self._cred_user.setPlaceholderText("Roblox username")
        layout.addWidget(self._cred_user)

        layout.addWidget(self._label("Password"))
        self._cred_pass = QLineEdit()
        self._cred_pass.setEchoMode(QLineEdit.Password)
        self._cred_pass.setPlaceholderText("Password")
        layout.addWidget(self._cred_pass)

        hint = QLabel("Vyre fills these in the Roblox login window. You solve any puzzle, then it captures the session. Credentials are never stored.")
        hint.setObjectName("DialogHint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        button = QPushButton("Fill and sign in")
        button.setObjectName("Primary")
        button.clicked.connect(
            lambda: self._capture(self._cred_user.text().strip(), self._cred_pass.text())
        )
        layout.addWidget(button, alignment=Qt.AlignLeft)
        return widget

    def _pick_color(self, color: str) -> None:
        self._account.color = color
        for swatch in self._swatches:
            swatch.setChecked(swatch.color.lower() == color.lower())

    def _capture(self, username: str = "", password: str = "") -> None:
        if username and not password:
            self._show_identity("Enter a password to sign in.", PALETTE["danger"])
            return
        dialog = LoginCaptureDialog(username, password, self)
        if dialog.exec() == QDialog.Accepted and dialog.cookie:
            self._cookie.setPlainText(dialog.cookie)
            self._verify(dialog.cookie)

    def _show_identity(self, text: str, color: str) -> None:
        self._identity.setStyleSheet(f"color: {color}; font-size: 12px;")
        self._identity.setText(text)

    def _verify(self, raw: str) -> None:
        cookie = roblox.normalize_cookie(raw)
        if not roblox.is_valid_cookie(cookie):
            self._show_identity("That does not look like a valid cookie.", PALETTE["danger"])
            return
        self._show_identity("Checking session...", PALETTE["text_dim"])
        self._worker = _IdentityWorker(cookie, self)
        self._worker.done.connect(self._on_identity)
        self._worker.start()

    def _on_identity(self, identity: dict) -> None:
        if not identity.get("username"):
            self._show_identity("Could not verify. The session may be expired.", PALETTE["danger"])
            return
        self._account.username = identity["username"]
        self._account.user_id = identity["user_id"]
        self._show_identity(
            f"Verified as {identity['username']} (#{identity['user_id']})",
            PALETTE["success"],
        )
        if not self._name.text().strip():
            self._name.setText(identity["username"])

    def _save(self) -> None:
        name = self._name.text().strip()
        cookie = roblox.normalize_cookie(self._cookie.toPlainText())
        if not roblox.is_valid_cookie(cookie):
            self._error.setText("Add a valid session using one of the tabs above.")
            self._error.setVisible(True)
            return
        if not name:
            name = self._account.username or "Account"
        self._account.name = name
        self._account.cookie = cookie
        self._account.note = self._note.text().strip()
        self.accept()

    def result_account(self) -> Account:
        return self._account
