import json

from PySide6.QtCore import QUrl, Qt
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineScript
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
        anti_detect = QWebEngineScript()
        anti_detect.setSourceCode("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = {runtime: {}};
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        """)
        anti_detect.setInjectionPoint(QWebEngineScript.DocumentCreation)
        anti_detect.setWorldId(QWebEngineScript.MainWorld)
        anti_detect.setRunsOnSubFrames(True)
        self._profile.scripts().insert(anti_detect)
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


class SignupCaptureDialog(QDialog):
    def __init__(self, username: str = "", password: str = "", gender: str = "Random", parent=None):
        super().__init__(parent)
        self.cookie = ""
        self._username = username
        self._password = password
        self._gender = gender
        self._prefilled = False
        self.setWindowTitle("Create Roblox Account")
        self.setModal(True)
        self.resize(900, 720)
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        bar = QHBoxLayout()
        bar.setContentsMargins(16, 12, 16, 12)
        bar.setSpacing(10)
        self._status = QLabel("Autofilling signup details. Complete captcha if prompted.")
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
        anti_detect = QWebEngineScript()
        anti_detect.setSourceCode("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = {runtime: {}};
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        """)
        anti_detect.setInjectionPoint(QWebEngineScript.DocumentCreation)
        anti_detect.setWorldId(QWebEngineScript.MainWorld)
        anti_detect.setRunsOnSubFrames(True)
        self._profile.scripts().insert(anti_detect)
        self._page = QWebEnginePage(self._profile, self)
        self._view = QWebEngineView(self)
        self._view.setPage(self._page)
        self._view.loadFinished.connect(self._on_loaded)
        root.addWidget(self._view, 1)
        self._store = self._profile.cookieStore()
        self._store.cookieAdded.connect(self._on_cookie)
        self._view.load(QUrl("https://www.roblox.com/CreateAccount"))

    def _on_loaded(self, ok: bool) -> None:
        if not ok or self._prefilled or not self._username:
            return
        self._prefilled = True
        user = json.dumps(self._username)
        pwd = json.dumps(self._password)
        gnd = json.dumps(self._gender)
        script = f"""
        (function() {{
            function fill() {{
                var mSelect = document.querySelector('#birthday-month, #MonthDropdown, select[name*="month"], select[data-testid*="month"]');
                var dSelect = document.querySelector('#birthday-day, #DayDropdown, select[name*="day"], select[data-testid*="day"]');
                var ySelect = document.querySelector('#birthday-year, #YearDropdown, select[name*="year"], select[data-testid*="year"]');
                var uInput = document.querySelector('#signup-username, input[name*="username"], input[id*="username"]');
                var pInput = document.querySelector('#signup-password, input[name*="password"], input[id*="password"]');
                var submitBtn = document.querySelector('#signup-button, button[name*="signup"], button[id*="signup"], button[class*="signup"]');
                var maleBtn = document.querySelector('#male-button, button[id*="male"], button[data-testid*="male"], [class*="gender-male"]');
                var femaleBtn = document.querySelector('#female-button, button[id*="female"], button[data-testid*="female"], [class*="gender-female"]');
                if (mSelect && dSelect && ySelect && uInput && pInput && submitBtn) {{
                    function setSelect(selectElem, possibleValues) {{
                        for (var i = 0; i < selectElem.options.length; i++) {{
                            var opt = selectElem.options[i];
                            if (possibleValues.indexOf(opt.value) !== -1 || possibleValues.indexOf(opt.text) !== -1) {{
                                selectElem.selectedIndex = i;
                                selectElem.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                return true;
                            }}
                        }}
                        return false;
                    }}
                    function setInput(elem, val) {{
                        var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                        if (setter) {{
                            setter.call(elem, val);
                        }} else {{
                            elem.value = val;
                        }}
                        elem.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}
                    setSelect(mSelect, ["1", "01", "Jan", "January"]);
                    setSelect(dSelect, ["1", "01"]);
                    setSelect(ySelect, ["2005", "2004", "2003", "2002", "2001", "2000", "1999", "1998"]);
                    setInput(uInput, {user});
                    setInput(pInput, {pwd});
                    if (maleBtn && femaleBtn) {{
                        var g = {gnd};
                        if (g === "Male") {{
                            maleBtn.click();
                        }} else if (g === "Female") {{
                            femaleBtn.click();
                        }} else {{
                            var choice = Math.random() < 0.5 ? maleBtn : femaleBtn;
                            choice.click();
                        }}
                    }}
                    setTimeout(function() {{
                        submitBtn.click();
                    }}, 800);
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
