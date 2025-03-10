import os
import json
import sys
import requests
from packaging import version
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton,
                           QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class UpdateChecker(QThread):
    update_available = pyqtSignal(dict)  # 发送更新信息
    check_failed = pyqtSignal(str)       # 发送错误信息
    
    def __init__(self, current_version: str):
        super().__init__()
        self.current_version = current_version
        self.api_url = "https://api.github.com/repos/your-repo/dydown/releases/latest"
    
    def run(self):
        try:
            response = requests.get(self.api_url)
            response.raise_for_status()
            
            latest = response.json()
            latest_version = latest["tag_name"].lstrip("v")
            
            if version.parse(latest_version) > version.parse(self.current_version):
                update_info = {
                    "version": latest_version,
                    "description": latest["body"],
                    "download_url": latest["assets"][0]["browser_download_url"]
                }
                self.update_available.emit(update_info)
        except Exception as e:
            self.check_failed.emit(str(e))

class Downloader(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, url: str, save_path: str):
        super().__init__()
        self.url = url
        self.save_path = save_path
    
    def run(self):
        try:
            response = requests.get(self.url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get("content-length", 0))
            block_size = 1024
            downloaded = 0
            
            with open(self.save_path, "wb") as f:
                for data in response.iter_content(block_size):
                    f.write(data)
                    downloaded += len(data)
                    if total_size:
                        progress = int((downloaded / total_size) * 100)
                        self.progress.emit(progress)
            
            self.finished.emit(self.save_path)
        except Exception as e:
            self.error.emit(str(e))

class UpdateDialog(QDialog):
    def __init__(self, update_info: dict, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("发现新版本")
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # 版本信息
        version_label = QLabel(f"新版本: v{self.update_info['version']}")
        version_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(version_label)
        
        # 更新说明
        desc_label = QLabel(self.update_info["description"])
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        self.update_btn = QPushButton("立即更新")
        self.update_btn.clicked.connect(self.start_update)
        btn_layout.addWidget(self.update_btn)
        
        cancel_btn = QPushButton("稍后再说")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton#update_btn {
                background-color: #ee1d52;
                color: white;
                border: none;
            }
            QProgressBar {
                border: 1px solid #e0e0e0;
                border-radius: 2px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #ee1d52;
            }
        """)
    
    def start_update(self):
        self.update_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        save_path = os.path.join(os.path.expanduser("~"), "Downloads",
                                f"DyDown-Setup-{self.update_info['version']}.exe")
        
        self.downloader = Downloader(self.update_info["download_url"], save_path)
        self.downloader.progress.connect(self.progress_bar.setValue)
        self.downloader.finished.connect(self.update_downloaded)
        self.downloader.error.connect(self.download_failed)
        self.downloader.start()
    
    def update_downloaded(self, file_path: str):
        reply = QMessageBox.question(
            self,
            "下载完成",
            "新版本已下载完成，是否立即安装？\n"
            "注意：安装过程中会关闭当前程序。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            os.startfile(file_path)
            QApplication.quit()
        else:
            self.accept()
    
    def download_failed(self, error: str):
        QMessageBox.warning(self, "下载失败", f"更新下载失败：{error}")
        self.update_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

def check_for_updates(current_version: str, parent=None):
    """检查更新的主函数"""
    checker = UpdateChecker(current_version)
    
    def on_update_available(update_info):
        dialog = UpdateDialog(update_info, parent)
        dialog.exec()
    
    def on_check_failed(error):
        QMessageBox.warning(
            parent,
            "检查更新失败",
            f"无法检查更新：{error}"
        )
    
    checker.update_available.connect(on_update_available)
    checker.check_failed.connect(on_check_failed)
    checker.start() 