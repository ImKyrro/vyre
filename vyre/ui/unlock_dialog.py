from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import profiles
from ..crypto import VaultError
from ..storage import Vault
from ..theme import PALETTE
from .widgets import Avatar


class UnlockDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vault: Vault | None = None
        self._profiles = profiles.list_profiles()
        self._current = self._profiles[0]

        self.setWindowTitle("Vyre")
        self.setModal(True)
        self.setFixedWidth(400)

        root = QVBoxLayout(self)
        root.setContentsMargins(34, 30, 34, 28)
        root.setSpacing(6)

        badge = Avatar("V", PALETTE["accent"], 58)
        holder = QWidget()
        holder_layout = QVBoxLayout(holder)
        holder_layout.setContentsMargins(0, 0, 0, 0)
        holder_layout.addWidget(badge, alignment=Qt.AlignCenter)
        root.addWidget(holder)
        root.addSpacing(8)

        self._title = QLabel("")
        self._title.setObjectName("DialogTitle")
        self._title.setAlignment(Qt.AlignCenter)
        root.addWidget(self._title)

        self._hint = QLabel("")
        self._hint.setObjectName("DialogHint")
        self._hint.setAlignment(Qt.AlignCenter)
        self._hint.setWordWrap(True)
        root.addWidget(self._hint)
        root.addSpacing(12)

        profile_row = QHBoxLayout()
        self._profile_box = QComboBox()
        self._profile_box.currentIndexChanged.connect(self._on_profile)
        profile_row.addWidget(self._profile_box, 1)
        new_btn = QPushButton("New")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.clicked.connect(self._new_profile)
        profile_row.addWidget(new_btn)
        root.addLayout(profile_row)
        root.addSpacing(6)

        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.Password)
        self._password.setPlaceholderText("Master password")
        self._password.returnPressed.connect(self._submit)
        root.addWidget(self._password)

        self._confirm = QLineEdit()
        self._confirm.setEchoMode(QLineEdit.Password)
        self._confirm.setPlaceholderText("Confirm password")
        self._confirm.returnPressed.connect(self._submit)
        root.addWidget(self._confirm)

        self._error = QLabel("")
        self._error.setStyleSheet(f"color: {PALETTE['danger']}; font-size: 12px;")
        self._error.setAlignment(Qt.AlignCenter)
        self._error.setVisible(False)
        root.addWidget(self._error)
        root.addSpacing(4)

        self._action = QPushButton("Unlock")
        self._action.setObjectName("Primary")
        self._action.clicked.connect(self._submit)
        root.addWidget(self._action)

        self._forgot = QPushButton("Forgot password?")
        self._forgot.setObjectName("Ghost")
        self._forgot.clicked.connect(self._forgot_password)
        root.addWidget(self._forgot)

        self._reload_profiles()
        self._password.setFocus()

    def _reload_profiles(self) -> None:
        self._profiles = profiles.list_profiles()
        self._profile_box.blockSignals(True)
        self._profile_box.clear()
        for profile in self._profiles:
            self._profile_box.addItem(profile["name"])
        self._profile_box.blockSignals(False)
        self._on_profile(self._profile_box.currentIndex())

    def _on_profile(self, index: int) -> None:
        if index < 0 or index >= len(self._profiles):
            return
        self._current = self._profiles[index]
        self._setup = not Vault.exists(self._current["path"])
        self._title.setText("Create master password" if self._setup else "Welcome back")
        self._hint.setText(
            "This encrypts this profile's vault. It cannot be recovered, so keep it safe."
            if self._setup
            else f"Enter the password for '{self._current['name']}'."
        )
        self._confirm.setVisible(self._setup)
        self._action.setText("Create vault" if self._setup else "Unlock")
        self._forgot.setVisible(not self._setup)
        self._error.setVisible(False)
        self._password.clear()
        self._confirm.clear()

    def _new_profile(self) -> None:
        name, ok = QInputDialog.getText(self, "New profile", "Profile name:")
        if not ok or not name.strip():
            return
        profiles.add_profile(name.strip())
        self._reload_profiles()
        self._profile_box.setCurrentIndex(self._profile_box.count() - 1)

    def _forgot_password(self) -> None:
        confirm = QMessageBox.question(
            self,
            "Reset profile",
            f"Vyre can't recover a lost password. Reset '{self._current['name']}' to a new empty "
            "vault? Your old encrypted data is archived and its accounts are lost.",
        )
        if confirm != QMessageBox.Yes:
            return
        profiles.reset_profile(self._current["file"])
        self._on_profile(self._profile_box.currentIndex())

    def _fail(self, message: str) -> None:
        self._error.setText(message)
        self._error.setVisible(True)

    def _submit(self, checked: bool = False) -> None:
        password = self._password.text()
        path = self._current["path"]
        if not password:
            self._fail("Please enter a password.")
            return
        if self._setup:
            if len(password) < 6:
                self._fail("Use at least 6 characters.")
                return
            if password != self._confirm.text():
                self._fail("Passwords do not match.")
                return
            self.vault = Vault.create(password, path)
            self.accept()
            return
        try:
            self.vault = Vault.unlock(password, path)
        except VaultError as error:
            self._fail(str(error))
            self._password.clear()
            self._password.setFocus()
            return
        self.accept()
