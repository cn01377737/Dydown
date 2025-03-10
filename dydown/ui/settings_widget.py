from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QPushButton, QLineEdit, QSpinBox, QComboBox,
                           QFormLayout, QFileDialog, QFrame)
from PyQt6.QtCore import Qt
import json
import os

class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.settings_file = "settings.json"
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 标题
        title = QLabel("设置")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        
        # 设置表单容器
        form_container = QFrame()
        form_container.setObjectName("formContainer")
        form_layout = QFormLayout(form_container)
        form_layout.setSpacing(15)
        
        # 下载路径设置
        path_widget = QWidget()
        path_layout = QHBoxLayout(path_widget)
        path_layout.setContentsMargins(0, 0, 0, 0)
        
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        path_layout.addWidget(self.path_input)
        
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_btn)
        
        form_layout.addRow("下载路径:", path_widget)
        
        # 并发下载数
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 10)
        self.concurrent_spin.setValue(3)
        form_layout.addRow("并发下载数:", self.concurrent_spin)
        
        # 默认下载画质
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["自动", "4K", "2K", "1080P", "720P"])
        form_layout.addRow("默认下载画质:", self.quality_combo)
        
        # 下载完成后动作
        self.after_download_combo = QComboBox()
        self.after_download_combo.addItems(["无动作", "打开文件夹", "关机"])
        form_layout.addRow("下载完成后:", self.after_download_combo)
        
        layout.addWidget(form_container)
        
        # 保存按钮
        save_btn = QPushButton("保存设置")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setObjectName("saveButton")
        layout.addWidget(save_btn)
        
        layout.addStretch()
        
        # 设置样式
        self.setStyleSheet("""
            #formContainer {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
            }
            QLineEdit, QSpinBox, QComboBox {
                padding: 8px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
            }
            #saveButton {
                background-color: #ee1d52;
                color: white;
                border: none;
                font-weight: bold;
            }
            #saveButton:hover {
                background-color: #dc1a4a;
            }
        """)
    
    def browse_path(self):
        path = QFileDialog.getExistingDirectory(
            self,
            "选择下载目录",
            self.path_input.text() or os.path.expanduser("~")
        )
        if path:
            self.path_input.setText(path)
    
    def load_settings(self):
        if not os.path.exists(self.settings_file):
            # 设置默认值
            self.path_input.setText(os.path.join(os.path.expanduser("~"), "Downloads", "DyDown"))
            return
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            self.path_input.setText(settings.get('download_path', ''))
            self.concurrent_spin.setValue(settings.get('concurrent_downloads', 3))
            
            quality_index = self.quality_combo.findText(settings.get('default_quality', '自动'))
            if quality_index >= 0:
                self.quality_combo.setCurrentIndex(quality_index)
            
            action_index = self.after_download_combo.findText(settings.get('after_download', '无动作'))
            if action_index >= 0:
                self.after_download_combo.setCurrentIndex(action_index)
        
        except Exception as e:
            print(f"加载设置失败: {e}")
    
    def save_settings(self):
        settings = {
            'download_path': self.path_input.text(),
            'concurrent_downloads': self.concurrent_spin.value(),
            'default_quality': self.quality_combo.currentText(),
            'after_download': self.after_download_combo.currentText()
        }
        
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存设置失败: {e}")
    
    def get_settings(self) -> dict:
        return {
            'download_path': self.path_input.text(),
            'concurrent_downloads': self.concurrent_spin.value(),
            'default_quality': self.quality_combo.currentText(),
            'after_download': self.after_download_combo.currentText()
        } 