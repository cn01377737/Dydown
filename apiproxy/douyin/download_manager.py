# -*- coding: utf-8 -*-

import os
import json
import time
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from typing import List, Optional
from pathlib import Path
import logging
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint
from prometheus_client import start_http_server, Summary, Gauge

# Prometheus监控指标
DOWNLOAD_SPEED = Gauge('download_speed_bytes', '实时下载速度')
QUEUE_SIZE = Gauge('download_queue_size', '当前下载队列长度')
REQUEST_TIME = Summary('request_processing_seconds', '请求处理时间')

from apiproxy.douyin import douyin_headers
from apiproxy.common import utils

logger = logging.getLogger("douyin_downloader")
console = Console()

class DownloadManager:
    def __init__(self, thread=5, music=True, cover=True, avatar=True, resjson=True, folderstyle=True):
        # 自动检测ffmpeg路径
        self.ffmpeg_path = self._detect_ffmpeg()
        if self.ffmpeg_path:
            logger.info(f"✅ FFmpeg路径已自动检测: {self.ffmpeg_path}")
        else:
            logger.warning("⚠️  未检测到FFmpeg路径，部分功能可能受限")

        # 在下载信息面板添加FFmpeg状态显示
        self.console.print(Panel(
            Text.assemble(
                ("FFmpeg状态: ", "bold cyan"),
                ("已就绪" if self.ffmpeg_path else "未配置", "green" if self.ffmpeg_path else "yellow")
            ),
            title="系统检测",
            border_style="cyan"
        ))
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
            BarColumn(bar_width=None, complete_style='blue', finished_style='green', pulse_style='red'),
            TextColumn("[retry]{task.fields[retry]}"),
            transient=True
        )
        self.retry_times = 3
        self.chunk_size = 8192
        self.timeout = 30

    def _download_media(self, url: str, path: Path, desc: str) -> bool:
        retry_count = 0
        if path.exists():
            self.console.print(f"[cyan]⏭️  跳过已存在: {desc}[/]")
            return True
        return self.download_with_resume(url, path, desc)

    def _download_media_files(self, aweme: dict, path: Path, name: str, desc: str) -> None:
        try:
            if aweme["awemeType"] == 0:
                video_path = path / f"{name}_video.mp4"
                if url := aweme.get("video", {}).get("play_addr", {}).get("url_list", [None])[0]:
                    if not self._download_media(url, video_path, f"[视频]{desc}"):
                        raise Exception("视频下载失败")
            elif aweme["awemeType"] == 1:
                for i, image in enumerate(aweme.get("images", [])):
                    if url := image.get("url_list", [None])[0]:
                        image_path = path / f"{name}_image_{i}.jpeg"
                        if not self._download_media(url, image_path, f"[图集{i+1}]{desc}"):
                            raise Exception(f"图片{i+1}下载失败")
            if self.music and (url := aweme.get("music", {}).get("play_url", {}).get("url_list", [None])[0]):
                music_name = utils.replaceStr(aweme["music"]["title"])
                music_path = path / f"{name}_music_{music_name}.mp3"
                if not self._download_media(url, music_path, f"[音乐]{desc}"):
                    self.console.print(f"[yellow]⚠️  音乐下载失败: {desc}[/]")
            if self.cover and aweme["awemeType"] == 0:
                if url := aweme.get("video", {}).get("cover", {}).get("url_list", [None])[0]:
                    cover_path = path / f"{name}_cover.jpeg"
                    if not self._download_media(url, cover_path, f"[封面]{desc}"):
                        self.console.print(f"[yellow]⚠️  封面下载失败: {desc}[/]")
            if self.avatar:
                if url := aweme.get("author", {}).get("avatar", {}).get("url_list", [None])[0]:
                    avatar_path = path / f"{name}_avatar.jpeg"
                    if not self._download_media(url, avatar_path, f"[头像]{desc}"):
                        self.console.print(f"[yellow]⚠️  头像下载失败: {desc}[/]")
        except Exception as e:
            raise Exception(f"下载失败: {str(e)}")

    def awemeDownload(self, awemeDict: dict, savePath: Path) -> None:
        if not awemeDict:
            logger.warning("无效的作品数据")
            return
        try:
            save_path = Path(savePath)
            save_path.mkdir(parents=True, exist_ok=True)
            file_name = f"{awemeDict['create_time']}_{utils.replaceStr(awemeDict['desc'])}"
            aweme_path = save_path / file_name if self.folderstyle else save_path
            aweme_path.mkdir(exist_ok=True)
            if self.resjson:
                self._save_json(aweme_path / f"{file_name}_result.json", awemeDict)
            desc = file_name[:30]
            self._download_media_files(awemeDict, aweme_path, file_name, desc)
        except Exception as e:
            logger.error(f"处理作品时出错: {str(e)}")

    def _save_json(self, path: Path, data: dict) -> None:
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
        self.console.print(Panel(
            Text.assemble(
                ("下载配置\n", "bold cyan"),
                (f"总数: {total_count} 个作品\n", "cyan"),
                (f"线程数: {self.thread}\n", "cyan"),
                (f"音乐: {self.music}\n", "cyan"),
                (f"封面: {self.cover}\n", "cyan"),
                (f"头像: {self.avatar}\n", "cyan"),
                (f"JSON: {self.resjson}\n", "cyan"),
                (f"文件夹风格: {self.folderstyle}\n", "cyan")
            )
        ))
        with self.progress:
            download_task = self.progress.add_task("[cyan]📥 下载中...", total=total_count)
            with ThreadPoolExecutor(max_workers=self.thread) as executor:
                futures = [executor.submit(self.awemeDownload, aweme, save_path) for aweme in awemeList]
                wait(futures, return_when=ALL_COMPLETED)
                for future in futures:
                    if future.exception() is None:
                        success_count += 1
                    self.progress.update(download_task, advance=1)
        end_time = time.time()
        self.console.print(Panel(
            Text.assemble(
                ("下载结果\n", "bold cyan"),
                (f"成功: {success_count} 个作品\n", "cyan"),
                (f"失败: {total_count - success_count} 个作品\n", "cyan"),
                (f"耗时: {round(end_time - start_time, 2)} 秒\n", "cyan")
            )
        ))