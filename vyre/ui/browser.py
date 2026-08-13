from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtNetwork import QNetworkCookie
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from PySide6.QtGui import QGuiApplication

from .. import roblox
from ..models import Account
from ..paths import profile_dir
from ..theme import PALETTE
from . import icons
from .widgets import Avatar

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


class BrowserPanel(QWidget):
    back_to_app = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("BrowserPanel")
        self._profiles: dict[str, QWebEngineProfile] = {}
        self._pages: dict[str, QWebEnginePage] = {}
        self._seeded: set[str] = set()
        self._current: str | None = None
        self._current_account: Account | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_toolbar())

        self._stack = QStackedWidget()
        root.addWidget(self._stack, 1)

        self._placeholder = self._build_placeholder()
        self._stack.addWidget(self._placeholder)

        self._view = QWebEngineView()
        self._view.urlChanged.connect(self._on_url)
        self._view.loadStarted.connect(lambda: self._set_loading(True))
        self._view.loadFinished.connect(lambda _: self._set_loading(False))
        self._stack.addWidget(self._view)
        self._stack.setCurrentWidget(self._placeholder)

    def _build_toolbar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(56)
        bar.setStyleSheet(
            f"background-color: {PALETTE['surface']};"
            f" border-bottom: 1px solid {PALETTE['border']};"
        )
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(10, 8, 12, 8)
        layout.setSpacing(4)

        self._home_app = QPushButton("  Vyre")
        self._home_app.setObjectName("Ghost")
        self._home_app.setIcon(icons.icon("back", PALETTE["text"], 16))
        self._home_app.setCursor(Qt.PointingHandCursor)
        self._home_app.setToolTip("Back to Vyre")
        self._home_app.clicked.connect(self.back_to_app.emit)
        layout.addWidget(self._home_app)

        self._back = self._nav_button("back", "Back", self._go_back)
        self._forward = self._nav_button("forward", "Forward", self._go_forward)
        self._reload = self._nav_button("refresh", "Reload", self._reload_page)
        self._home = self._nav_button("home", "Home", self._go_home)
        for button in (self._back, self._forward, self._reload, self._home):
            layout.addWidget(button)

        self._address = QLineEdit()
        self._address.setObjectName("AddressBar")
        self._address.setPlaceholderText("Switch to an account to start browsing")
        self._address.setReadOnly(True)
        layout.addWidget(self._address, 1)

        self._copy = self._nav_button("copy", "Copy this account's cookie", self._copy_cookie)
        self._external = self._nav_button("external", "Open in system browser", self._open_external)
        layout.addWidget(self._copy)
        layout.addWidget(self._external)

        self._badge = Avatar("V", PALETTE["surface_alt"], 28)
        layout.addWidget(self._badge)
        self._who = QLabel("No account")
        self._who.setStyleSheet("font-size: 12px; font-weight: 600;")
        layout.addWidget(self._who)

        self._set_nav_enabled(False)
        return bar

    def _nav_button(self, name: str, tip: str, handler) -> QToolButton:
        button = QToolButton()
        button.setIcon(icons.icon(name, PALETTE["text_dim"], 18))
        button.setToolTip(tip)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(handler)
        return button

    def _build_placeholder(self) -> QWidget:
        widget = QWidget()
        widget.setObjectName("Root")
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        mark = Avatar("V", PALETTE["accent"], 72)
        layout.addWidget(mark, alignment=Qt.AlignCenter)

        title = QLabel("Select an account")
        title.setObjectName("EmptyTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        body = QLabel("Choose an account from the left to open its Roblox session.")
        body.setObjectName("EmptyBody")
        body.setAlignment(Qt.AlignCenter)
        layout.addWidget(body)
        return widget

    def _profile_for(self, account: Account) -> QWebEngineProfile:
        if account.id in self._profiles:
            return self._profiles[account.id]
        profile = QWebEngineProfile(f"vyre_{account.id}", self)
        profile.setPersistentStoragePath(str(profile_dir(account.id)))
        profile.setCachePath(str(profile_dir(account.id) / "cache"))
        profile.setPersistentCookiesPolicy(QWebEngineProfile.ForcePersistentCookies)
        profile.setHttpUserAgent(_USER_AGENT)
        self._profiles[account.id] = profile
        return profile

    def _seed_cookie(self, profile: QWebEngineProfile, account: Account) -> None:
        store = profile.cookieStore()
        cookie = QNetworkCookie(
            roblox.COOKIE_NAME.encode("utf-8"),
            roblox.normalize_cookie(account.cookie).encode("utf-8"),
        )
        cookie.setDomain(roblox.COOKIE_DOMAIN)
        cookie.setPath("/")
        cookie.setSecure(True)
        cookie.setHttpOnly(True)
        store.setCookie(cookie, QUrl("https://www.roblox.com"))

    def load_account(self, account: Account) -> None:
        profile = self._profile_for(account)
        page = self._pages.get(account.id)
        if page is None:
            page = QWebEnginePage(profile, self)
            self._pages[account.id] = page

        if account.id not in self._seeded:
            self._seed_cookie(profile, account)
            self._seeded.add(account.id)
            page.setUrl(QUrl(roblox.HOME_URL))
        elif page.url().isEmpty():
            page.setUrl(QUrl(roblox.HOME_URL))

        self._view.setPage(page)
        self._current = account.id
        self._current_account = account
        self._stack.setCurrentWidget(self._view)
        self._badge.update_data(account.initials(), account.color)
        if account.user_id:
            self._badge.set_image_url(
                "https://thumbnails.roblox.com/v1/users/avatar-headshot"
                f"?userIds={account.user_id}&size=150x150&format=Png&isCircular=false"
            )
        self._who.setText(account.username or account.name)
        self._address.setText(page.url().toString())
        self._set_nav_enabled(True)

    def reseed(self, account: Account) -> None:
        self._seeded.discard(account.id)
        if account.id in self._profiles:
            self._seed_cookie(self._profiles[account.id], account)
            self._seeded.add(account.id)

    def forget(self, account_id: str) -> None:
        if self._current == account_id:
            self._stack.setCurrentWidget(self._placeholder)
            self._current = None
            self._current_account = None
            self._set_nav_enabled(False)
        self._pages.pop(account_id, None)
        self._profiles.pop(account_id, None)
        self._seeded.discard(account_id)

    def open_url(self, url: str) -> None:
        if self._current:
            self._view.setUrl(QUrl(url))
            self._stack.setCurrentWidget(self._view)

    def _open_external(self) -> None:
        from PySide6.QtGui import QDesktopServices

        QDesktopServices.openUrl(self._view.url())

    def _copy_cookie(self) -> None:
        if self._current_account:
            QGuiApplication.clipboard().setText(self._current_account.cookie)

    def _set_nav_enabled(self, enabled: bool) -> None:
        for button in (self._back, self._forward, self._reload, self._home, self._external, self._copy):
            button.setEnabled(enabled)

    def _set_loading(self, loading: bool) -> None:
        self._reload.setIcon(icons.icon("x" if loading else "refresh", PALETTE["text_dim"], 18))

    def _on_url(self, url: QUrl) -> None:
        self._address.setText(url.toString())

    def _go_back(self) -> None:
        self._view.back()

    def _go_forward(self) -> None:
        self._view.forward()

    def _reload_page(self) -> None:
        self._view.reload()

    def _go_home(self) -> None:
        self._view.setUrl(QUrl(roblox.HOME_URL))
