import json

from PySide6.QtCore import QUrl, Qt
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from .. import roblox

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


class LoginCaptureDialog(QDialog):
    def __init__(self, username: str = "", password: str = "", parent=None):
        super().__init__(parent)
        self.cookie = ""
        self._username = username
        self._password = password
        self._prefilled = False

        self.setWindowTitle("Log in to Roblox")
        self.setModal(True)
        self.resize(900, 720)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        bar = QHBoxLayout()
        bar.setContentsMargins(16, 12, 16, 12)
        bar.setSpacing(10)
        note = (
            "Complete the sign in below — Vyre captures the session automatically."
            if not username
            else "Credentials filled in. Solve any puzzle and sign in; Vyre captures it."
        )
        self._status = QLabel(note)
        self._status.setObjectName("StatusText")
        bar.addWidget(self._status)
        bar.addStretch(1)
        cancel = QPushButton("Cancel")
        cancel.setObjectName("Ghost")
        cancel.clicked.connect(self.reject)
        bar.addWidget(cancel)
        root.addLayout(bar)

        self._profile = QWebEngineProfile(self)
        self._profile.setHttpUserAgent(_USER_AGENT)
        self._page = QWebEnginePage(self._profile, self)
        self._view = QWebEngineView(self)
        self._view.setPage(self._page)
        self._view.loadFinished.connect(self._on_loaded)
        root.addWidget(self._view, 1)

        self._store = self._profile.cookieStore()
        self._store.cookieAdded.connect(self._on_cookie)
        self._view.load(QUrl(roblox.LOGIN_URL))

    def _on_loaded(self, ok: bool) -> None:
        if not ok or self._prefilled or not self._username:
            return
        self._prefilled = True
        user = json.dumps(self._username)
        pwd = json.dumps(self._password)
        script = f"""
        (function() {{
            function fill() {{
                var u = document.querySelector('#login-username, input[name="username"]');
                var p = document.querySelector('#login-password, input[name="password"]');
                if (u && p) {{
                    var setter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value').set;
                    setter.call(u, {user});
                    u.dispatchEvent(new Event('input', {{bubbles: true}}));
                    setter.call(p, {pwd});
                    p.dispatchEvent(new Event('input', {{bubbles: true}}));
                }} else {{
                    setTimeout(fill, 400);
                }}
            }}
            fill();
        }})();
        """
        self._page.runJavaScript(script)

    def _on_cookie(self, cookie) -> None:
        if bytes(cookie.name()).decode("utf-8", "ignore") != roblox.COOKIE_NAME:
            return
        value = bytes(cookie.value()).decode("utf-8", "ignore")
        if roblox.is_valid_cookie(value):
            self.cookie = roblox.normalize_cookie(value)
            self._status.setText("Session captured.")
            self.accept()
