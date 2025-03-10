from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QPushButton, QTableWidget, QTableWidgetItem,
                           QHeaderView, QMenu)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
import os
import json
from datetime import datetime

class HistoryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.history_file = "download_history.json"
        self.setup_ui()
        self.load_history()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题栏
        header = QWidget()
        header_layout = QHBoxLayout(header)
        
        title = QLabel("下载历史")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title)
        
        clear_btn = QPushButton("清空历史")
        clear_btn.clicked.connect(self.clear_history)
        header_layout.addWidget(clear_btn)
        
        header_layout.addStretch()
        layout.addWidget(header)
        
        # 历史记录表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["标题", "作者", "画质", "大小", "下载时间"])
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(1, 120)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 150)
        
        # 允许右键菜单
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.table)
        
        # 设置样式
        self.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 8px;
                border: none;
                border-bottom: 1px solid #e0e0e0;
            }
            QPushButton {
                background-color: #f5f5f5;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
    
    def load_history(self):
        if not os.path.exists(self.history_file):
            return
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            self.table.setRowCount(len(history))
            for row, item in enumerate(history):
                self.table.setItem(row, 0, QTableWidgetItem(item['title']))
                self.table.setItem(row, 1, QTableWidgetItem(item['author']))
                self.table.setItem(row, 2, QTableWidgetItem(item['quality']))
                self.table.setItem(row, 3, QTableWidgetItem(self.format_size(item['size'])))
                self.table.setItem(row, 4, QTableWidgetItem(item['time']))
        except Exception as e:
            print(f"加载历史记录失败: {e}")
    
    def add_history(self, video_info: dict):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(video_info['title']))
        self.table.setItem(row, 1, QTableWidgetItem(video_info['author']))
        self.table.setItem(row, 2, QTableWidgetItem(video_info['quality']))
        self.table.setItem(row, 3, QTableWidgetItem(self.format_size(video_info['size'])))
        self.table.setItem(row, 4, QTableWidgetItem(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        
        self.save_history()
    
    def clear_history(self):
        self.table.setRowCount(0)
        if os.path.exists(self.history_file):
            os.remove(self.history_file)
    
    def show_context_menu(self, pos):
        menu = QMenu(self)
        
        open_action = menu.addAction("打开文件")
        open_folder_action = menu.addAction("打开所在文件夹")
        menu.addSeparator()
        delete_action = menu.addAction("删除记录")
        
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        
        if action == delete_action:
            self.delete_selected_items()
    
    def delete_selected_items(self):
        rows = set(item.row() for item in self.table.selectedItems())
        for row in sorted(rows, reverse=True):
            self.table.removeRow(row)
        self.save_history()
    
    def save_history(self):
        history = []
        for row in range(self.table.rowCount()):
            item = {
                'title': self.table.item(row, 0).text(),
                'author': self.table.item(row, 1).text(),
                'quality': self.table.item(row, 2).text(),
                'size': self.parse_size(self.table.item(row, 3).text()),
                'time': self.table.item(row, 4).text()
            }
            history.append(item)
        
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def format_size(size_in_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_in_bytes < 1024:
                return f"{size_in_bytes:.1f} {unit}"
            size_in_bytes /= 1024
        return f"{size_in_bytes:.1f} TB"
    
    @staticmethod
    def parse_size(size_str: str) -> int:
        number = float(size_str.split()[0])
        unit = size_str.split()[1]
        multiplier = {
            'B': 1,
            'KB': 1024,
            'MB': 1024**2,
            'GB': 1024**3,
            'TB': 1024**4
        }
        return int(number * multiplier[unit]) 