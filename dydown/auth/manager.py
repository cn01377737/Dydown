from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWebEngineWidgets import QWebEngineView

class AuthManager(QObject):
    login_success = pyqtSignal(dict)
    login_failed = pyqtSignal(str)

    def __init__(self, webview: QWebEngineView):
        super().__init__()
        self.webview = webview
        self.cookies = {}
        self._setup_webview()

    def _setup_webview(self):
        self.webview.load("https://www.douyin.com/login")
        self.webview.urlChanged.connect(self._check_login_status)

    def _check_login_status(self, url):
        if "www.douyin.com/login" not in url.toString():
            self._extract_cookies()

    def _extract_cookies(self):
        self.webview.page().profile().cookieStore().getAllCookies()
        self.webview.page().toHtml(lambda html: self._validate_login(html))

    def _validate_login(self, html):
        if "登录成功" in html:
            self.login_success.emit(self.cookies)
        else:
            self.login_failed.emit("Cookie验证失败")

    def is_logged_in(self):
        return bool(self.cookies)