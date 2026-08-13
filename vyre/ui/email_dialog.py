from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from .. import roblox
from ..models import Account
from ..theme import PALETTE
from . import icons


class _EmailWorker(QThread):
    done = Signal(dict)

    def __init__(self, cookie: str, parent=None):
        super().__init__(parent)
        self._cookie = cookie

    def run(self) -> None:
        self.done.emit(roblox.get_email(self._cookie))


class _ResendWorker(QThread):
    done = Signal(bool)

    def __init__(self, cookie: str, parent=None):
        super().__init__(parent)
        self._cookie = cookie

    def run(self) -> None:
        self.done.emit(roblox.resend_verification(self._cookie))


class EmailDialog(QDialog):
    open_web_requested = Signal(str)

    def __init__(self, account: Account, parent=None):
        super().__init__(parent)
        self._account = account
        self._worker = None
        self._resend = None

        self.setWindowTitle("Account & email")
        self.setModal(True)
        self.setFixedWidth(440)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(12)

        title = QLabel("Account & email")
        title.setObjectName("DialogTitle")
        root.addWidget(title)

        sub = QLabel(f"For {account.username or account.name}")
        sub.setObjectName("Muted")
        root.addWidget(sub)

        root.addWidget(self._label("Current email"))
        self._email = QLineEdit("Loading…")
        self._email.setReadOnly(True)
        root.addWidget(self._email)

        self._verified = QLabel("")
        self._verified.setObjectName("Muted")
        root.addWidget(self._verified)

        resend = QPushButton("  Resend verification email")
        resend.setIcon(icons.icon("mail", PALETTE["text_dim"], 16))
        resend.setCursor(Qt.PointingHandCursor)
        resend.clicked.connect(self._do_resend)
        root.addWidget(resend)

        change = QPushButton("  Change email on Roblox")
        change.setObjectName("Primary")
        change.setIcon(icons.icon("external", "#ffffff", 16))
        change.setCursor(Qt.PointingHandCursor)
        change.clicked.connect(self._open_web)
        root.addWidget(change)

        hint = QLabel("Changing your email needs your Roblox password, so Vyre opens Roblox's own secure page for that — it never handles your password.")
        hint.setObjectName("Faint")
        hint.setWordWrap(True)
        root.addWidget(hint)

        self._status = QLabel("")
        self._status.setObjectName("StatusText")
        root.addWidget(self._status)

        self._worker = _EmailWorker(account.cookie, self)
        self._worker.done.connect(self._on_email)
        self._worker.start()

    def _label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        return label

    def _on_email(self, data: dict) -> None:
        email = data.get("email", "")
        self._email.setText(email or "Unavailable (cookie may be expired)")
        if email:
            verified = data.get("verified")
            self._verified.setText("✓ Verified" if verified else "⚠ Not verified")
            color = PALETTE["online"] if verified else PALETTE["studio"]
            self._verified.setStyleSheet(f"color: {color}; font-size: 12px; font-weight: 600;")

    def _do_resend(self) -> None:
        self._status.setStyleSheet(f"color: {PALETTE['text_dim']}; font-size: 12px;")
        self._status.setText("Sending verification email…")
        self._resend = _ResendWorker(self._account.cookie, self)
        self._resend.done.connect(self._on_resend)
        self._resend.start()

    def _on_resend(self, ok: bool) -> None:
        self._status.setStyleSheet(
            f"color: {PALETTE['online'] if ok else PALETTE['danger']}; font-size: 12px;"
        )
        self._status.setText("Verification email sent." if ok else "Could not send (cookie may be expired).")

    def _open_web(self) -> None:
        self.open_web_requested.emit(self._account.id)
        self.accept()
