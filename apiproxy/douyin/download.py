#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import json
import time
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from typing import List, Optional
from pathlib import Path
# import asyncio  # 暂时注释掉
# import aiohttp  # 暂时注释掉
import logging
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

from apiproxy.douyin import douyin_headers
from apiproxy.common import utils

logger = logging.getLogger("douyin_downloader")
console = Console()

class Download(object):
    def __init__(self, thread=5, music=True, cover=True, avatar=True, resjson=True, folderstyle=True):
        # 自动检测ffmpeg路径
        self.ffmpeg_path = self._detect_ffmpeg()

    def _detect_ffmpeg(self):
        """自动检测ffmpeg安装路径"""
        import platform
        import shutil
        
        # 优先检测环境变量中的ffmpeg
        ffmpeg_path = shutil.which('ffmpeg')
        if ffmpeg_path:
            return ffmpeg_path
        
        # 根据不同平台查找默认安装路径
        system = platform.system()
        if system == 'Windows':
            # Windows下查找常见安装路径
            for path in ['C:\Program Files\ffmpeg\bin\ffmpeg.exe',
                        'C:\ffmpeg\bin\ffmpeg.exe',
                        'D:\ffmpeg\bin\ffmpeg.exe']:
                if os.path.exists(path):
                    return path
        elif system == 'Linux':
            # Linux下查找常见安装路径
            for path in ['/usr/bin/ffmpeg',
                        '/usr/local/bin/ffmpeg',
                        '/opt/ffmpeg/bin/ffmpeg']:
                if os.path.exists(path):
                    return path
        elif system == 'Darwin':  # macOS
            # macOS下查找常见安装路径
            for path in ['/usr/local/bin/ffmpeg',
                        '/opt/homebrew/bin/ffmpeg',
                        '/Applications/ffmpeg/ffmpeg']:
                if os.path.exists(path):
                    return path
        
        return None
        self.thread = thread
        self.music = music
        self.cover = cover
        self.avatar = avatar
        self.resjson = resjson
        self.folderstyle = folderstyle
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            transient=True  # 添加这个参数，进度条完成后自动消失
        )
        self.retry_times = 3
        self.chunk_size = 8192
        self.timeout = 30

    def _download_media(self, url: str, path: Path, desc: str) -> bool:
        """通用下载方法，处理所有类型的媒体下载"""
        if path.exists():
            self.console.print(f"[cyan]⏭️  跳过已存在: {desc}[/]")
            return True
            
        # 使用新的断点续传下载方法替换原有的下载逻辑
        return self.download_with_resume(url, path, desc)

    def _download_media_files(self, aweme: dict, path: Path, name: str, desc: str) -> None:
        """下载所有媒体文件"""
        try:
            # 下载视频或图集
            if aweme["awemeType"] == 0:  # 视频
                video_path = path / f"{name}_video.mp4"
                if url := aweme.get("video", {}).get("play_addr", {}).get("url_list", [None])[0]:
                    if not self._download_media(url, video_path, f"[视频]{desc}"):
                        raise Exception("视频下载失败")
                    
            elif aweme["awemeType"] == 1:  # 图集
                for i, image in enumerate(aweme.get("images", [])):
                    if url := image.get("url_list", [None])[0]:
                        image_path = path / f"{name}_image_{i}.jpeg"
                        if not self._download_media(url, image_path, f"[图集{i+1}]{desc}"):
                            raise Exception(f"图片{i+1}下载失败")

            # 下载音乐
            if self.music and (url := aweme.get("music", {}).get("play_url", {}).get("url_list", [None])[0]):
                music_name = utils.replaceStr(aweme["music"]["title"])
                music_path = path / f"{name}_music_{music_name}.mp3"
                if not self._download_media(url, music_path, f"[音乐]{desc}"):
                    self.console.print(f"[yellow]⚠️  音乐下载失败: {desc}[/]")

            # 下载封面
            if self.cover and aweme["awemeType"] == 0:
                if url := aweme.get("video", {}).get("cover", {}).get("url_list", [None])[0]:
                    cover_path = path / f"{name}_cover.jpeg"
                    if not self._download_media(url, cover_path, f"[封面]{desc}"):
                        self.console.print(f"[yellow]⚠️  封面下载失败: {desc}[/]")

            # 下载头像
            if self.avatar:
                if url := aweme.get("author", {}).get("avatar", {}).get("url_list", [None])[0]:
                    avatar_path = path / f"{name}_avatar.jpeg"
                    if not self._download_media(url, avatar_path, f"[头像]{desc}"):
                        self.console.print(f"[yellow]⚠️  头像下载失败: {desc}[/]")
                    
        except Exception as e:
            raise Exception(f"下载失败: {str(e)}")

    def awemeDownload(self, awemeDict: dict, savePath: Path) -> None:
        """下载单个作品的所有内容"""
        if not awemeDict:
            logger.warning("无效的作品数据")
            return
            
        try:
            # 创建保存目录
            save_path = Path(savePath)
            save_path.mkdir(parents=True, exist_ok=True)
            
            # 构建文件名
            file_name = f"{awemeDict['create_time']}_{utils.replaceStr(awemeDict['desc'])}"
            aweme_path = save_path / file_name if self.folderstyle else save_path
            aweme_path.mkdir(exist_ok=True)
            
            # 保存JSON数据
            if self.resjson:
                self._save_json(aweme_path / f"{file_name}_result.json", awemeDict)
                
            # 下载媒体文件
            desc = file_name[:30]
            self._download_media_files(awemeDict, aweme_path, file_name, desc)
                
        except Exception as e:
            logger.error(f"处理作品时出错: {str(e)}")

    def _save_json(self, path: Path, data: dict) -> None:
        """保存JSON数据"""
        try:
            with open(path, "w", encoding='utf-8') as f:
                json.dump(data, ensure_ascii=False, indent=2, fp=f)
        except Exception as e:
            logger.error(f"保存JSON失败: {path}, 错误: {str(e)}")

    def userDownload(self, awemeList: List[dict], savePath: Path):
        if not awemeList:
            self.console.print("[yellow]⚠️  没有找到可下载的内容[/]")
            return

        save_path = Path(savePath)
        save_path.mkdir(parents=True, exist_ok=True)

        start_time = time.time()
        total_count = len(awemeList)
        success_count = 0
        
        # 显示下载信息面板
        self.console.print(Panel(
            Text.assemble(
                ("下载配置\n", "bold cyan"),
                (f"总数: {total_count} 个作品\n", "cyan"),
                (f"线程: {self.thread}\n", "cyan"),
                (f"保存路径: {save_path}\n", "cyan"),
            ),
            title="抖音下载器",
            border_style="cyan"
        ))

        with self.progress:
            download_task = self.progress.add_task(
                "[cyan]📥 批量下载进度", 
                total=total_count
            )
            
            for aweme in awemeList:
                try:
                    self.awemeDownload(awemeDict=aweme, savePath=save_path)
                    success_count += 1
                    self.progress.update(download_task, advance=1)
                except Exception as e:
                    self.console.print(f"[red]❌ 下载失败: {str(e)}[/]")

        # 显示下载完成统计
        end_time = time.time()
        duration = end_time - start_time
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        
        self.console.print(Panel(
            Text.assemble(
                ("下载完成\n", "bold green"),
                (f"成功: {success_count}/{total_count}\n", "green"),
                (f"用时: {minutes}分{seconds}秒\n", "green"),
                (f"保存位置: {save_path}\n", "green"),
            ),
            title="下载统计",
            border_style="green"
        ))

    def download_with_resume(self, url: str, filepath: Path, desc: str) -> bool:
        """支持断点续传的下载方法"""
        # 多平台路径处理
filepath = Path(str(filepath).replace('\\', '/'))  # 统一路径分隔符
file_size = filepath.stat().st_size if filepath.exists() else 0
        headers = {'Range': f'bytes={file_size}-'} if file_size > 0 else {}
        
        for attempt in range(self.retry_times):
            try:
                response = requests.get(url, headers={**douyin_headers, **headers}, 
                                     stream=True, timeout=self.timeout)
                
                # 处理HTTP 429 Too Many Requests
if response.status_code == 429:
    retry_after = int(response.headers.get('Retry-After', 5))
    logger.warning(f'HTTP 429 Too Many Requests, 将在 {retry_after} 秒后重试')
    time.sleep(retry_after)
    continue

if response.status_code not in (200, 206):
                    raise Exception(f"HTTP {response.status_code}")
                    
                total_size = int(response.headers.get('content-length', 0)) + file_size
                mode = 'ab' if file_size > 0 else 'wb'
                
                with self.progress:
                    task = self.progress.add_task(f"[cyan]⬇️  {desc}", total=total_size)
                    self.progress.update(task, completed=file_size)  # 更新断点续传的进度
                    
                    with open(filepath, mode) as f:
                        for chunk in response.iter_content(chunk_size=self.chunk_size):
                            if chunk:
                                size = f.write(chunk)
                                self.progress.update(task, advance=size)
                                
                return True
                
            except Exception as e:
                logger.warning(f"下载失败 (尝试 {attempt + 1}/{self.retry_times}): {str(e)}")
                if attempt == self.retry_times - 1:
                    self.console.print(f"[red]❌ 下载失败: {desc}\n   {str(e)}[/]")
                    return False
                time.sleep(1)  # 重试前等待


class DownloadManager:
    __slots__ = ['executor']
    
    def __init__(self, max_workers=3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def download_with_resume(self, url, filepath, callback=None):
        file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
        headers = {'Range': f'bytes={file_size}-'}
        
        with requests.get(url, headers=headers, stream=True) as response:
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0)) + file_size
            
            mode = 'ab' if file_size > 0 else 'wb'
            with open(filepath, mode) as f, tqdm(
                initial=file_size,
                total=total_size,
                unit='B',
                unit_scale=True,
                desc=os.path.basename(filepath)
            ) as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
                        if callback:
                            callback(len(chunk))


if __name__ == "__main__":
    pass
