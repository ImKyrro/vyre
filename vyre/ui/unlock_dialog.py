from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..crypto import VaultError
from ..storage import Vault
from ..theme import PALETTE
from .widgets import Avatar


class UnlockDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_setup = not Vault.exists()
        self.vault: Vault | None = None

        self.setWindowTitle("Vyre")
        self.setModal(True)
        self.setFixedWidth(380)

        root = QVBoxLayout(self)
        root.setContentsMargins(34, 30, 34, 30)
        root.setSpacing(6)

        badge = Avatar("V", PALETTE["accent"], 58)
        holder = QWidget()
        holder_layout = QVBoxLayout(holder)
        holder_layout.setContentsMargins(0, 0, 0, 0)
        holder_layout.addWidget(badge, alignment=Qt.AlignCenter)
        root.addWidget(holder)
        root.addSpacing(10)

        title = QLabel("Create master password" if self._is_setup else "Welcome back")
        title.setObjectName("DialogTitle")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        hint_text = (
            "This encrypts your account vault. It cannot be recovered, so keep it safe."
            if self._is_setup
            else "Enter your master password to unlock the vault."
        )
        hint = QLabel(hint_text)
        hint.setObjectName("DialogHint")
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        root.addWidget(hint)
        root.addSpacing(16)

        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.Password)
        self._password.setPlaceholderText("Master password")
        self._password.returnPressed.connect(self._submit)
        root.addWidget(self._password)

        self._confirm = QLineEdit()
        self._confirm.setEchoMode(QLineEdit.Password)
        self._confirm.setPlaceholderText("Confirm password")
        self._confirm.returnPressed.connect(self._submit)
        self._confirm.setVisible(self._is_setup)
        root.addWidget(self._confirm)

        self._error = QLabel("")
        self._error.setStyleSheet(f"color: {PALETTE['danger']}; font-size: 12px;")
        self._error.setAlignment(Qt.AlignCenter)
        self._error.setVisible(False)
        root.addWidget(self._error)
        root.addSpacing(6)

        self._action = QPushButton("Create vault" if self._is_setup else "Unlock")
        self._action.setObjectName("Primary")
        self._action.clicked.connect(self._submit)
        root.addWidget(self._action)

        self._password.setFocus()

    def _fail(self, message: str) -> None:
        self._error.setText(message)
        self._error.setVisible(True)

    def _submit(self) -> None:
        password = self._password.text()
        if not password:
            self._fail("Please enter a password.")
            return

        if self._is_setup:
            if len(password) < 6:
                self._fail("Use at least 6 characters.")
                return
            if password != self._confirm.text():
                self._fail("Passwords do not match.")
                return
            self.vault = Vault.create(password)
            self.accept()
            return

        try:
            self.vault = Vault.unlock(password)
        except VaultError as error:
            self._fail(str(error))
            self._password.clear()
            self._password.setFocus()
            return
        self.accept()
