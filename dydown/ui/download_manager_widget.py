from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                           QPushButton, QScrollArea, QGridLayout, QFrame,
                           QLabel, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from .video_card import VideoCard
from ..download_manager import DownloadManager, DownloadTask

class DownloadManagerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.download_manager = DownloadManager()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 顶部搜索栏
        search_container = QFrame()
        search_container.setObjectName("searchContainer")
        search_layout = QHBoxLayout(search_container)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入抖音视频链接（支持单个视频或合集）")
        self.url_input.setMinimumHeight(40)
        search_layout.addWidget(self.url_input)
        
        parse_btn = QPushButton("解析")
        parse_btn.setObjectName("parseButton")
        parse_btn.setFixedSize(100, 40)
        parse_btn.clicked.connect(self.parse_url)
        search_layout.addWidget(parse_btn)
        
        layout.addWidget(search_container)
        
        # 视频卡片网格区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        scroll_content = QWidget()
        self.grid_layout = QGridLayout(scroll_content)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(20)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # 设置样式
        self.setStyleSheet("""
            #searchContainer {
                background-color: white;
                border-radius: 8px;
                padding: 10px;
            }
            QLineEdit {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
            #parseButton {
                background-color: #ee1d52;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            #parseButton:hover {
                background-color: #dc1a4a;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
    
    def parse_url(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "错误", "请输入视频链接")
            return
        
        # TODO: 实现视频链接解析
        # 这里模拟一些视频数据
        video_info = {
            "url": url,
            "title": "示例视频标题",
            "author": "示例作者",
            "resolution": "1080P",
            "cover_url": "path/to/cover.jpg",
            "author_avatar": "path/to/avatar.jpg"
        }
        
        self.add_video_card(video_info)
        self.url_input.clear()
    
    def add_video_card(self, video_info: dict):
        card = VideoCard(video_info)
        card.download_requested.connect(self.start_download)
        
        # 计算网格位置
        count = self.grid_layout.count()
        row = count // 3
        col = count % 3
        
        self.grid_layout.addWidget(card, row, col)
    
    def start_download(self, url: str, quality: str):
        # 创建下载任务
        save_path = "downloads"  # TODO: 从设置中获取保存路径
        task = self.download_manager.add_task(url, save_path)
        
        # TODO: 更新下载进度UI 