import re
import json
import asyncio
import aiohttp
from typing import List, Dict, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, parse_qs

@dataclass
class VideoInfo:
    """视频信息"""
    id: str
    title: str
    author: str
    cover_url: str
    duration: int
    resolutions: List[str]
    download_urls: Dict[str, str]

class VideoParser:
    """视频解析器"""
    def __init__(self, cookies: Dict[str, str], max_workers: int = 3):
        self.cookies = cookies
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.douyin.com/"
        }
    
    async def parse_share_url(self, share_url: str) -> str:
        """解析分享链接获取视频ID"""
        async with aiohttp.ClientSession() as session:
            async with session.get(share_url, headers=self.headers, allow_redirects=True) as resp:
                if resp.status == 200:
                    # 从URL中提取视频ID
                    url = str(resp.url)
                    if match := re.search(r'/video/(\d+)', url):
                        return match.group(1)
        return ""
    
    async def parse_video(self, video_id: str) -> Optional[VideoInfo]:
        """解析视频信息"""
        api_url = f"https://www.douyin.com/aweme/v1/web/aweme/detail/?aweme_id={video_id}"
        
        async with aiohttp.ClientSession(cookies=self.cookies) as session:
            async with session.get(api_url, headers=self.headers) as resp:
                if resp.status != 200:
                    return None
                
                try:
                    data = await resp.json()
                    aweme = data['aweme_detail']
                    
                    # 提取视频信息
                    video_info = VideoInfo(
                        id=video_id,
                        title=aweme['desc'],
                        author=aweme['author']['nickname'],
                        cover_url=aweme['video']['cover']['url_list'][0],
                        duration=aweme['video']['duration'],
                        resolutions=[],
                        download_urls={}
                    )
                    
                    # 提取不同清晰度的下载地址
                    video_urls = aweme['video']['play_addr']['url_list']
                    if video_urls:
                        video_info.download_urls['原画'] = video_urls[0]
                        video_info.resolutions.append('原画')
                    
                    return video_info
                    
                except Exception as e:
                    print(f"解析视频信息失败: {e}")
                    return None
    
    async def parse_collection(self, collection_id: str) -> List[VideoInfo]:
        """解析视频合集"""
        api_url = f"https://www.douyin.com/aweme/v1/web/aweme/listcollection/?collection_id={collection_id}"
        videos = []
        
        async with aiohttp.ClientSession(cookies=self.cookies) as session:
            async with session.get(api_url, headers=self.headers) as resp:
                if resp.status != 200:
                    return videos
                
                try:
                    data = await resp.json()
                    aweme_list = data.get('aweme_list', [])
                    
                    # 使用线程池并发解析视频
                    tasks = [
                        self.parse_video(aweme['aweme_id'])
                        for aweme in aweme_list
                    ]
                    
                    # 等待所有视频解析完成
                    results = await asyncio.gather(*tasks)
                    videos = [video for video in results if video is not None]
                    
                except Exception as e:
                    print(f"解析合集失败: {e}")
                
                return videos
    
    def extract_video_id(self, url: str) -> str:
        """从URL中提取视频ID"""
        patterns = [
            r'video/(\d+)',  # 标准视频页面
            r'aweme_id=(\d+)',  # API链接
        ]
        
        for pattern in patterns:
            if match := re.search(pattern, url):
                return match.group(1)
        return ""
    
    async def parse_url(self, url: str) -> List[VideoInfo]:
        """解析URL（支持视频链接和合集链接）"""
        # 处理分享链接
        if "v.douyin.com" in url:
            video_id = await self.parse_share_url(url)
        else:
            video_id = self.extract_video_id(url)
        
        if not video_id:
            return []
        
        # 尝试解析为单个视频
        video = await self.parse_video(video_id)
        if video:
            return [video]
        
        # 尝试解析为合集
        videos = await self.parse_collection(video_id)
        return videos 