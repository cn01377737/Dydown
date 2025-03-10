import os
import json
import time
import qrcode
from typing import Optional, Dict, Callable
from dataclasses import dataclass
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEngineCookieStore

@dataclass
class AuthConfig:
    """认证配置"""
    cookies_file: str = "douyin_cookies.json"
    login_url: str = "https://www.douyin.com/login"
    success_url: str = "https://www.douyin.com/"
    
class AuthManager(QObject):
    """抖音认证管理器"""
    login_success = pyqtSignal(dict)  # 登录成功信号
    login_failed = pyqtSignal(str)    # 登录失败信号
    
    def __init__(self, webview: Optional[QWebEngineView] = None, config: Optional[AuthConfig] = None):
        super().__init__()
        self.webview = webview
        self.config = config or AuthConfig()
        self._cookies: Dict[str, str] = {}
        self._setup_webview()
        
    def _setup_webview(self):
        """配置WebView"""
        if not self.webview:
            return
            
        # 配置Cookie存储
        profile = QWebEngineProfile.defaultProfile()
        profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies
        )
        
        # 监听Cookie变化
        cookie_store = profile.cookieStore()
        cookie_store.cookieAdded.connect(self._on_cookie_added)
        
        # 加载登录页面
        self.webview.setUrl(self.config.login_url)
        
    def _on_cookie_added(self, cookie):
        """处理Cookie添加事件"""
        name = cookie.name().data().decode()
        value = cookie.value().data().decode()
        self._cookies[name] = value
        
        # 检查登录状态
        if "sessionid" in self._cookies:
            self._save_cookies()
            self.login_success.emit(self._cookies)
    
    def _save_cookies(self):
        """保存Cookies到文件"""
        try:
            with open(self.config.cookies_file, 'w', encoding='utf-8') as f:
                json.dump(self._cookies, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.login_failed.emit(f"保存Cookie失败: {e}")
    
    def load_cookies(self) -> Dict[str, str]:
        """加载已保存的Cookies"""
        if not os.path.exists(self.config.cookies_file):
            return {}
            
        try:
            with open(self.config.cookies_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.login_failed.emit(f"加载Cookie失败: {e}")
            return {}
    
    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        cookies = self.load_cookies()
        return "sessionid" in cookies
    
    def logout(self):
        """退出登录"""
        if os.path.exists(self.config.cookies_file):
            os.remove(self.config.cookies_file)
        
        if self.webview:
            profile = QWebEngineProfile.defaultProfile()
            profile.cookieStore().deleteAllCookies()
            self.webview.setUrl(self.config.login_url)
        
        self._cookies.clear()

class QRCodeLoginManager:
    """二维码登录管理器"""
    def __init__(self, auth_manager: AuthManager):
        self.auth_manager = auth_manager
        self.qr_code: Optional[qrcode.QRCode] = None
    
    def generate_qr_code(self, save_path: str) -> bool:
        """生成登录二维码"""
        try:
            # 获取二维码内容（实际项目中需要调用抖音API）
            qr_data = "https://www.douyin.com/qrlogin?token=example"
            
            # 生成二维码
            self.qr_code = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            self.qr_code.add_data(qr_data)
            self.qr_code.make(fit=True)
            
            # 保存二维码图片
            img = self.qr_code.make_image(fill_color="black", back_color="white")
            img.save(save_path)
            return True
            
        except Exception as e:
            self.auth_manager.login_failed.emit(f"生成二维码失败: {e}")
            return False
    
    def check_login_status(self, callback: Callable[[bool, str], None]):
        """检查登录状态"""
        # 实际项目中需要轮询抖音API
        def mock_check():
            time.sleep(1)  # 模拟网络请求
            if self.auth_manager.is_logged_in():
                callback(True, "登录成功")
            else:
                callback(False, "等待扫码") 