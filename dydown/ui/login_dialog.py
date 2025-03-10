from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton,
                           QProgressBar)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile
import json
import os

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("登录抖音账号")
        self.setFixedSize(400, 600)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题
        title = QLabel("扫码登录抖音")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            padding: 20px;
            background-color: #ee1d52;
            color: white;
        """)
        layout.addWidget(title)
        
        # WebView用于显示登录页面
        self.webview = QWebEngineView()
        self.webview.setFixedSize(400, 500)
        layout.addWidget(self.webview)
        
        # 设置WebView
        self._setup_webview()
        
        # 取消按钮
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f5f5f5;
                border: none;
                padding: 10px;
                border-radius: 4px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        layout.addWidget(cancel_btn)
        
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border-radius: 8px;
            }
        """)
    
    def _setup_webview(self):
        # 配置WebView
        profile = QWebEngineProfile.defaultProfile()
        profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
        )
        
        # 监听cookie变化
        profile.cookieStore().cookieAdded.connect(self._on_cookie_added)
        
        # 加载抖音登录页面
        self.webview.setUrl("https://www.douyin.com/login")
    
    def _on_cookie_added(self, cookie):
        # 检查是否包含登录态cookie
        if cookie.name().data().decode() == "sessionid":
            self._save_cookies()
            self.accept()
    
    def _save_cookies(self):
        profile = QWebEngineProfile.defaultProfile()
        cookies = {}
        
        def callback(cookie):
            name = cookie.name().data().decode()
            value = cookie.value().data().decode()
            cookies[name] = value
        
        profile.cookieStore().loadAllCookies()
        
        with open("douyin_cookies.json", 'w') as f:
            json.dump(cookies, f)
    
    def is_logged_in(self) -> bool:
        if os.path.exists("douyin_cookies.json"):
            with open("douyin_cookies.json", 'r') as f:
                cookies = json.load(f)
                return "sessionid" in cookies
        return False 