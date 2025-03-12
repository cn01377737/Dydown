import sys
import os
import platform
import ctypes
import winreg
import wmi
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QPushButton, QSystemTrayIcon, QMenu, QLineEdit,
                           QProgressBar, QListWidget, QListWidgetItem, QMessageBox, QDialog, QLabel, QCheckBox, QDialogButtonBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWebEngineWidgets import QWebEngineView

from .auth.manager import AuthManager
from .downloader.manager import DownloadManager, DownloadTask, TaskStatus

class DouYinDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 系统兼容性检测
        self.check_system_compatibility()

    def check_tpm_version(self):
        try:
            c = wmi.WMI()
            tpm = c.Win32_Tpm()[0]
            return tpm.SpecVersion.split(',')[0] >= '2.0'
        except IndexError:
            print("TPM设备未找到，请确认系统支持TPM 2.0")
            return False
        except Exception as e:
            print(f"TPM检测失败: {str(e)}")
            return False

    def check_system_compatibility(self):
        # Windows版本检测
        if not self.check_windows_version():
            QMessageBox.critical(None, '系统不兼容', '需要Windows 11 21H2及以上版本才能运行')
            sys.exit(1)
            
        # TPM 2.0检测（改为警告提示而非强制退出）
        if not self.check_tpm_version():
            QMessageBox.warning(None, '安全提示', '建议启用TPM 2.0以获得完整安全功能')
            
        # 配置长路径支持
        self.enable_long_path_support()

    def enable_long_path_support(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                r'SYSTEM\CurrentControlSet\Control\FileSystem',
                                0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, 'LongPathsEnabled', 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
        except Exception as e:
            print(f"注册表修改失败: {e}")

    def check_windows_version(self):
        version = platform.uname().version.split('.')
        major, minor, build = int(version[0]), int(version[1]), int(version[2])
        # 检测Windows 11 build 22000及以上
        return (major > 10) or (major == 10 and build >= 22000)
        
        self.setWindowTitle("抖音视频下载器")
        self.setGeometry(100, 100, 800, 600)
        
        # 创建主窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建登录WebView
        self.webview = QWebEngineView()
        layout.addWidget(self.webview)
        
        # 创建URL输入框
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入抖音视频链接（支持单个视频或合集）")
        layout.addWidget(self.url_input)
        
        # 创建下载按钮
        self.download_btn = QPushButton("开始下载")
        self.download_btn.clicked.connect(self.start_download)
        layout.addWidget(self.download_btn)
        
        # 创建下载列表
        self.download_list = QListWidget()
        layout.addWidget(self.download_list)
        
        # 初始化下载管理器
        self.download_manager = DownloadManager()
        self.download_manager.on_progress_callback = self.update_progress
        self.download_manager.start_workers()
        
        # 初始化认证管理器
        self.auth_manager = AuthManager(self.webview)
        self.auth_manager.login_success.connect(self.on_login_success)
        self.auth_manager.login_failed.connect(self.on_login_failed)
        
        # 初始化系统托盘
        self.setup_system_tray()
        
        # 检查登录状态
        if not self.login_manager.is_logged_in():
            self.download_btn.setEnabled(False)
            self.url_input.setEnabled(False)
    
    def setup_system_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(QIcon("icon.png"))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        show_action = tray_menu.addAction("显示主窗口")
        show_action.triggered.connect(self.show)
        
        quick_download = tray_menu.addAction("快速下载")
        quick_download.triggered.connect(self.quick_download)
        
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(QApplication.quit)
        
        self.tray.setContextMenu(tray_menu)
        self.tray.show()
    
    def on_login_success(self, cookies):
        self.download_btn.setEnabled(True)
        self.url_input.setEnabled(True)
        QMessageBox.information(self, "登录成功", "抖音账号登录成功！")
    
    def on_login_failed(self, error):
        QMessageBox.warning(self, "登录失败", f"登录失败：{error}")
    
    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "错误", "请输入视频链接")
            return
        
        # 创建下载任务
        save_path = os.path.join(os.path.expanduser("~"), "Downloads", "DyDown")
        os.makedirs(save_path, exist_ok=True)
        
        task = self.download_manager.add_task(url, save_path)
        self._add_task_to_list(task)
        
        self.url_input.clear()
    
    def _add_task_to_list(self, task: DownloadTask):
        item = QListWidgetItem()
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title_label = QLineEdit(task.url)
        title_label.setReadOnly(True)
        
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(0)
        
        control_btn = QPushButton("暂停")
        control_btn.clicked.connect(lambda: self._toggle_task(task, control_btn))
        
        layout.addWidget(title_label)
        layout.addWidget(progress_bar)
        layout.addWidget(control_btn)
        
        item.setSizeHint(widget.sizeHint())
        self.download_list.addItem(item)
        self.download_list.setItemWidget(item, widget)
        
        # 保存进度条引用以便更新
        task.progress_bar = progress_bar
        task.control_btn = control_btn
        task.list_item = item
    
    def _toggle_task(self, task: DownloadTask, btn: QPushButton):
        if task.status == TaskStatus.DOWNLOADING:
            self.download_manager.pause_task(task)
            btn.setText("继续")
        elif task.status == TaskStatus.PAUSED:
            self.download_manager.resume_task(task)
            btn.setText("暂停")
    
    def update_progress(self, task: DownloadTask):
        if hasattr(task, 'progress_bar'):
            task.progress_bar.setValue(int(task.progress * 100))
            
            if task.title and task.status == TaskStatus.COMPLETED:
                item_widget = self.download_list.itemWidget(task.list_item)
                title_label = item_widget.findChild(QLineEdit)
                title_label.setText(task.title)
                task.control_btn.setEnabled(False)
                task.control_btn.setText("已完成")
    
    def quick_download(self):
        clipboard = QApplication.clipboard()
        url = clipboard.text()
        
        if "douyin.com" in url:
            self.url_input.setText(url)
            self.start_download()
    
    def closeEvent(self, event):
        # 关闭窗口时最小化到托盘
        event.ignore()
        self.hide()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 首次运行声明
    settings = QSettings('Dydown', 'Preferences')
    if not settings.value('disclaimer_accepted', False, type=bool):
        dialog = QDialog()
        dialog.setWindowTitle('免责声明')
        layout = QVBoxLayout()
        
        text = QLabel('''欢迎使用本软件，请仔细阅读以下条款：

1. 本软件仅供个人学习研究使用，禁止用于商业用途
2. 下载内容24小时内须删除，违规使用责任自负
3. 开发者不承担用户滥用造成的法律责任''')
        checkbox = QCheckBox('我已阅读并同意上述条款')
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        
        buttons.accepted.connect(lambda: settings.setValue('disclaimer_accepted', True))
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        checkbox.stateChanged.connect(lambda state: buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(state == 2))
        
        layout.addWidget(text)
        layout.addWidget(checkbox)
        layout.addWidget(buttons)
        dialog.setLayout(layout)
        
        if dialog.exec() != QDialog.DialogCode.Accepted:
            sys.exit(1)
    
    window = DouYinDownloader()
    window.show()
    sys.exit(app.exec())