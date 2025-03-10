from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                           QListWidget, QStackedWidget, QPushButton, QLabel,
                           QSystemTrayIcon, QMenu, QProgressBar, QFrame, QApplication)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QAction
from .video_card import VideoCard
from .login_dialog import LoginDialog
from .download_manager_widget import DownloadManagerWidget
from .history_widget import HistoryWidget
from .settings_widget import SettingsWidget
from .tray_icon import TrayIcon

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("抖音视频下载器")
        self.setMinimumSize(1200, 800)
        
        # 创建主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 创建左侧导航栏
        self.setup_sidebar()
        main_layout.addWidget(self.sidebar_frame)
        
        # 创建主内容区域
        self.setup_main_content()
        main_layout.addWidget(self.content_stack)
        
        # 设置托盘图标
        self.setup_tray()
        
        # 初始化登录对话框
        self.login_dialog = LoginDialog(self)
        
        # 显示登录对话框
        if not self.login_dialog.is_logged_in():
            self.login_dialog.show()
    
    def setup_sidebar(self):
        # 创建侧边栏框架
        self.sidebar_frame = QFrame()
        self.sidebar_frame.setObjectName("sidebar")
        self.sidebar_frame.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(self.sidebar_frame)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        # 添加导航按钮
        self.history_btn = self.create_nav_button("历史记录", "history.svg")
        self.downloads_btn = self.create_nav_button("下载任务", "download.svg")
        self.settings_btn = self.create_nav_button("设置", "settings.svg")
        
        sidebar_layout.addWidget(self.history_btn)
        sidebar_layout.addWidget(self.downloads_btn)
        sidebar_layout.addWidget(self.settings_btn)
        sidebar_layout.addStretch()
        
        # 设置样式
        self.sidebar_frame.setStyleSheet("""
            #sidebar {
                background-color: #2c2c2c;
                border: none;
            }
            QPushButton {
                color: #ffffff;
                text-align: left;
                padding: 12px 20px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
            }
            QPushButton:checked {
                background-color: #ee1d52;
            }
        """)
    
    def create_nav_button(self, text, icon_path):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.setIcon(QIcon(f"icons/{icon_path}"))
        btn.setIconSize(QSize(20, 20))
        return btn
    
    def setup_main_content(self):
        self.content_stack = QStackedWidget()
        
        # 创建各个页面
        self.history_widget = HistoryWidget()
        self.download_widget = DownloadManagerWidget()
        self.settings_widget = SettingsWidget()
        
        # 添加到堆叠窗口
        self.content_stack.addWidget(self.history_widget)
        self.content_stack.addWidget(self.download_widget)
        self.content_stack.addWidget(self.settings_widget)
        
        # 连接导航按钮信号
        self.history_btn.clicked.connect(lambda: self.content_stack.setCurrentWidget(self.history_widget))
        self.downloads_btn.clicked.connect(lambda: self.content_stack.setCurrentWidget(self.download_widget))
        self.settings_btn.clicked.connect(lambda: self.content_stack.setCurrentWidget(self.settings_widget))
        
        # 默认选中下载页面
        self.downloads_btn.setChecked(True)
        self.content_stack.setCurrentWidget(self.download_widget)
    
    def setup_tray(self):
        self.tray = TrayIcon(self)
        
        # 连接信号
        self.tray.show_main_window.connect(self.show)
        self.tray.quick_download.connect(self._handle_quick_download)
        
        # 监听下载进度
        self.download_widget.download_manager.on_progress_callback = self._update_download_progress
        
        self.tray.show()
    
    def _handle_quick_download(self, url: str):
        """处理快速下载请求"""
        self.download_widget.url_input.setText(url)
        self.download_widget.parse_url()
    
    def _update_download_progress(self, task):
        """更新下载进度"""
        total_tasks = len(self.download_widget.download_manager.active_tasks)
        completed_tasks = len(self.download_widget.download_manager.completed_tasks)
        
        if total_tasks > 0:
            # 计算总体进度
            total_progress = completed_tasks
            for active_task in self.download_widget.download_manager.active_tasks:
                total_progress += active_task.progress
            
            self.tray.update_progress(
                int(total_progress * 100),
                total_tasks * 100
            )
    
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        if self.tray.isVisible():
            event.ignore()
            self.hide()
            self.tray.showMessage(
                "提示",
                "程序已最小化到系统托盘，双击图标可以重新打开主窗口。",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            event.accept() 