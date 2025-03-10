from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                           QMenu, QPushButton, QSizePolicy)
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon, QAction, QCursor

class VideoCard(QWidget):
    download_requested = pyqtSignal(str, str)  # 信号：url, quality
    
    def __init__(self, video_info: dict):
        super().__init__()
        self.video_info = video_info
        self.setup_ui()
        
    def setup_ui(self):
        self.setFixedSize(300, 400)
        self.setObjectName("videoCard")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 封面图片
        self.cover = QLabel()
        self.cover.setFixedSize(300, 200)
        self.cover.setScaledContents(True)
        if "cover_url" in self.video_info:
            pixmap = QPixmap(self.video_info["cover_url"])
            self.cover.setPixmap(pixmap)
        layout.addWidget(self.cover)
        
        # 信息容器
        info_container = QWidget()
        info_container.setObjectName("infoContainer")
        info_layout = QVBoxLayout(info_container)
        
        # 标题
        title = QLabel(self.video_info.get("title", "未知标题"))
        title.setWordWrap(True)
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        info_layout.addWidget(title)
        
        # 作者信息
        author_layout = QHBoxLayout()
        author_avatar = QLabel()
        author_avatar.setFixedSize(24, 24)
        if "author_avatar" in self.video_info:
            avatar_pixmap = QPixmap(self.video_info["author_avatar"])
            author_avatar.setPixmap(avatar_pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio))
        author_layout.addWidget(author_avatar)
        
        author_name = QLabel(self.video_info.get("author", "未知作者"))
        author_layout.addWidget(author_name)
        author_layout.addStretch()
        info_layout.addLayout(author_layout)
        
        # 分辨率信息
        resolution = QLabel(f"分辨率: {self.video_info.get('resolution', '未知')}")
        info_layout.addWidget(resolution)
        
        # 下载按钮
        download_btn = QPushButton("下载")
        download_btn.setObjectName("downloadButton")
        download_btn.clicked.connect(self.show_quality_menu)
        info_layout.addWidget(download_btn)
        
        layout.addWidget(info_container)
        
        # 设置样式
        self.setStyleSheet("""
            #videoCard {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
            #videoCard:hover {
                box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
            }
            #infoContainer {
                padding: 12px;
            }
            #downloadButton {
                background-color: #ee1d52;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            #downloadButton:hover {
                background-color: #dc1a4a;
            }
        """)
    
    def show_quality_menu(self):
        menu = QMenu(self)
        qualities = [
            ("4K", "2160p"),
            ("2K", "1440p"),
            ("1080P", "1080p"),
            ("720P", "720p")
        ]
        
        for label, quality in qualities:
            action = QAction(label, self)
            action.triggered.connect(lambda checked, q=quality: 
                self.download_requested.emit(self.video_info["url"], q))
            menu.addAction(action)
        
        menu.exec(QCursor.pos())
    
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        
        # 添加右键菜单选项
        copy_link = menu.addAction("复制链接")
        copy_link.triggered.connect(self.copy_video_link)
        
        menu.addSeparator()
        
        download_menu = menu.addMenu("下载")
        qualities = [("4K", "2160p"), ("2K", "1440p"), 
                    ("1080P", "1080p"), ("720P", "720p")]
        
        for label, quality in qualities:
            action = QAction(label, self)
            action.triggered.connect(lambda checked, q=quality: 
                self.download_requested.emit(self.video_info["url"], q))
            download_menu.addAction(action)
        
        menu.exec(event.globalPos())
    
    def copy_video_link(self):
        if "url" in self.video_info:
            QApplication.clipboard().setText(self.video_info["url"]) 