import qrcode
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile
import json
import os
from typing import Optional

class LoginManager(QObject):
    login_success = pyqtSignal(dict)
    login_failed = pyqtSignal(str)
    
    def __init__(self, webview: QWebEngineView):
        super().__init__()
        self.webview = webview
        self.cookies_file = "douyin_cookies.json"
        self._setup_webview()
        
    def _setup_webview(self):
        # 配置WebView
        profile = QWebEngineProfile.defaultProfile()
        profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)
        
        # 监听cookie变化
        profile.cookieStore().cookieAdded.connect(self._on_cookie_added)
        
        # 加载抖音登录页面
        self.webview.setUrl("https://www.douyin.com/login")
    
    def _on_cookie_added(self, cookie):
        # 检查是否包含登录态cookie
        if cookie.name().data().decode() == "sessionid":
            self._save_cookies()
            self.login_success.emit(self.get_cookies())
    
    def _save_cookies(self):
        profile = QWebEngineProfile.defaultProfile()
        cookies = {}
        
        def callback(cookie):
            name = cookie.name().data().decode()
            value = cookie.value().data().decode()
            cookies[name] = value
        
        profile.cookieStore().loadAllCookies()
        
        with open(self.cookies_file, 'w') as f:
            json.dump(cookies, f)
    
    def get_cookies(self) -> dict:
        if os.path.exists(self.cookies_file):
            with open(self.cookies_file, 'r') as f:
                return json.load(f)
        return {}
    
    def is_logged_in(self) -> bool:
        cookies = self.get_cookies()
        return "sessionid" in cookies
    
    def logout(self):
        if os.path.exists(self.cookies_file):
            os.remove(self.cookies_file)
        
        profile = QWebEngineProfile.defaultProfile()
        profile.cookieStore().deleteAllCookies()
        self.webview.setUrl("https://www.douyin.com/login") 