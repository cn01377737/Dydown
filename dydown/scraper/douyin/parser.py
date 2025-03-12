\"""
抖音链接解析模块

实现抖音分享链接的正则匹配、URL参数提取等核心功能
"""
import re
from urllib.parse import urlparse

class DouyinParser:
    @staticmethod
    async def parse(url: str) -> dict:
        """
        解析抖音分享链接
        返回格式：{type: video/music/playlist, id: str}
        """
        patterns = [
            r'(https?://v.douyin.com/[\w-]+/)',
            r'(www.iesdouyin.com/share/video/[\w-]+/)',
            r'(www.douyin.com/video/[\w-]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                path = urlparse(url).path
                return {
                    'type': 'video',
                    'id': path.split('/')[-2] if 'video' in path else match.group(1)
                }
        return {}

    @staticmethod
    def is_valid(url: str) -> bool:
        """验证是否为抖音域名"""
        domains = ['douyin.com', 'iesdouyin.com', 'tiktok.com']
        return any(d in url for d in domains)