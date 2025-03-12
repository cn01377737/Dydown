import os
import asyncio
import aiohttp
import aiofiles
import ffmpeg
from typing import Dict, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class DownloadTask:
    """下载任务"""
    url: str
    save_path: str
    filename: str
    total_size: int = 0
    downloaded_size: int = 0
    status: DownloadStatus = DownloadStatus.PENDING
    error: Optional[str] = None

class ProgressCallback:
    """进度回调"""
    def __init__(self):
        self._callbacks: List[Callable[[DownloadTask], None]] = []
    
    def add(self, callback: Callable[[DownloadTask], None]):
        self._callbacks.append(callback)
    
    def notify(self, task: DownloadTask):
        for callback in self._callbacks:
            callback(task)

class VideoDownloader:
    """视频下载器"""
    def __init__(self, max_workers: int = (os.cpu_count() or 1) * 2):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.progress_callback = ProgressCallback()
        self.tasks: Dict[str, DownloadTask] = {}
        self._paused = set()
    
    def add_task(self, url: str, save_path: str, filename: str) -> DownloadTask:
        """添加下载任务"""
        task = DownloadTask(url=url, save_path=save_path, filename=filename)
        self.tasks[url] = task
        return task
    
    async def start_task(self, task: DownloadTask):
        """开始下载任务"""
        if task.status == DownloadStatus.COMPLETED:
            return
        
        task.status = DownloadStatus.DOWNLOADING
        self.progress_callback.notify(task)
        
        try:
            # 创建保存目录
            os.makedirs(task.save_path, exist_ok=True)
            save_path = os.path.join(task.save_path, task.filename)
            
            # 获取文件大小
            async with aiohttp.ClientSession() as session:
                async with session.head(task.url) as resp:
                    task.total_size = int(resp.headers.get('content-length', 0))
            
            # 下载文件
            async with aiohttp.ClientSession() as session:
                async with session.get(task.url) as resp:
                    if resp.status != 200:
                        raise Exception(f"下载失败: HTTP {resp.status}")
                    
                    async with aiofiles.open(save_path, 'wb') as f:
                        async for chunk in resp.content.iter_chunked(8192):
                            if task.url in self._paused:
                                task.status = DownloadStatus.PAUSED
                                self.progress_callback.notify(task)
                                return
                            
                            await f.write(chunk)
                            task.downloaded_size += len(chunk)
                            self.progress_callback.notify(task)
            
            task.status = DownloadStatus.COMPLETED
            self.progress_callback.notify(task)
            
        except Exception as e:
            task.status = DownloadStatus.FAILED
            task.error = str(e)
            self.progress_callback.notify(task)
    
    def pause_task(self, task: DownloadTask):
        """暂停下载任务"""
        if task.status == DownloadStatus.DOWNLOADING:
            self._paused.add(task.url)
    
    def resume_task(self, task: DownloadTask):
        """恢复下载任务"""
        if task.status == DownloadStatus.PAUSED:
            self._paused.discard(task.url)
            asyncio.create_task(self.start_task(task))
    
    def get_progress(self, task: DownloadTask) -> float:
        """获取下载进度"""
        if task.total_size == 0:
            return 0
        return task.downloaded_size / task.total_size

class MediaProcessor:
    """媒体处理器"""
    @staticmethod
    async def merge_audio_video(video_path: str, audio_path: str, output_path: str):
        """合并音视频"""
        try:
            # 使用ffmpeg合并
            stream = ffmpeg.input(video_path)
            audio = ffmpeg.input(audio_path)
            stream = ffmpeg.output(stream, audio, output_path,
                                 vcodec='copy', acodec='copy')
            await asyncio.to_thread(ffmpeg.run, stream, capture_stdout=True, capture_stderr=True)
            
            # 删除临时文件
            os.remove(video_path)
            os.remove(audio_path)
            
        except ffmpeg.Error as e:
            print(f"合并音视频失败: {e.stderr.decode()}")
            raise
    
    @staticmethod
    async def extract_audio(video_path: str, output_path: str):
        """提取音频"""
        try:
            stream = ffmpeg.input(video_path)
            stream = ffmpeg.output(stream, output_path, acodec='copy')
            await asyncio.to_thread(ffmpeg.run, stream, capture_stdout=True, capture_stderr=True)
            
        except ffmpeg.Error as e:
            print(f"提取音频失败: {e.stderr.decode()}")
            raise