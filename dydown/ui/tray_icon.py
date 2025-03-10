from PyQt6.QtWidgets import (QSystemTrayIcon, QMenu, QWidget, 
                           QProgressBar, QVBoxLayout, QWidgetAction)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, pyqtSignal
import os

class ProgressWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedSize(200, 15)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% - %v/%m")
        layout.addWidget(self.progress_bar)
        
        self.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 2px;
                background-color: #f5f5f5;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #ee1d52;
                border-radius: 2px;
            }
        """)

class TrayIcon(QSystemTrayIcon):
    show_main_window = pyqtSignal()
    quick_download = pyqtSignal(str)  # 发送剪贴板链接信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setIcon(QIcon("icon.svg"))
        self.setToolTip("抖音视频下载器")
        
        # 创建进度条组件
        self.progress_widget = ProgressWidget()
        
        # 初始化菜单
        self.setup_menu()
        
        # 连接信号
        self.activated.connect(self._on_activated)
    
    def setup_menu(self):
        menu = QMenu()
        
        # 添加标题
        title = menu.addAction("抖音视频下载器")
        title.setEnabled(False)
        title.setIcon(QIcon("icon.svg"))
        menu.addSeparator()
        
        # 添加主要操作
        show_action = menu.addAction("显示主窗口")
        show_action.triggered.connect(self.show_main_window.emit)
        
        quick_download = menu.addAction("快速下载")
        quick_download.triggered.connect(self._quick_download)
        quick_download.setToolTip("从剪贴板获取链接并下载")
        
        menu.addSeparator()
        
        # 添加下载进度条
        progress_action = QWidgetAction(menu)
        progress_action.setDefaultWidget(self.progress_widget)
        menu.addAction(progress_action)
        
        menu.addSeparator()
        
        # 添加下载控制
        self.pause_all = menu.addAction("暂停所有下载")
        self.pause_all.triggered.connect(self._pause_all_downloads)
        
        self.resume_all = menu.addAction("恢复所有下载")
        self.resume_all.triggered.connect(self._resume_all_downloads)
        self.resume_all.setEnabled(False)
        
        menu.addSeparator()
        
        # 添加设置和退出
        settings = menu.addAction("设置")
        settings.triggered.connect(lambda: self.show_main_window.emit())
        
        exit_action = menu.addAction("退出")
        exit_action.triggered.connect(self._exit_app)
        
        self.setContextMenu(menu)
    
    def update_progress(self, current: int, total: int):
        """更新下载进度"""
        self.progress_widget.progress_bar.setMaximum(total)
        self.progress_widget.progress_bar.setValue(current)
        
        # 更新托盘图标提示
        if total > 0:
            percentage = int(current / total * 100)
            self.setToolTip(f"抖音视频下载器 - {percentage}%")
        else:
            self.setToolTip("抖音视频下载器")
    
    def _on_activated(self, reason):
        """处理托盘图标点击事件"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_main_window.emit()
    
    def _quick_download(self):
        """从剪贴板获取链接并触发下载"""
        clipboard = QApplication.clipboard()
        url = clipboard.text()
        
        if "douyin.com" in url:
            self.quick_download.emit(url)
            self.showMessage(
                "开始下载",
                "已添加到下载队列",
                QIcon("icon.svg"),
                2000  # 显示2秒
            )
        else:
            self.showMessage(
                "错误",
                "剪贴板中未找到抖音链接",
                QSystemTrayIcon.MessageIcon.Warning,
                2000
            )
    
    def _pause_all_downloads(self):
        """暂停所有下载"""
        self.pause_all.setEnabled(False)
        self.resume_all.setEnabled(True)
        # TODO: 实现暂停所有下载的逻辑
    
    def _resume_all_downloads(self):
        """恢复所有下载"""
        self.pause_all.setEnabled(True)
        self.resume_all.setEnabled(False)
        # TODO: 实现恢复所有下载的逻辑
    
    def _exit_app(self):
        """退出应用程序"""
        # 保存必要的状态
        self.parent().close()
        QApplication.quit() 