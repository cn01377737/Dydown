import threading
from queue import Queue
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Callable
import yt_dlp
import ffmpeg

class TaskStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class DownloadTask:
    url: str
    save_path: str
    status: TaskStatus
    progress: float = 0
    title: Optional[str] = None
    error_message: Optional[str] = None

class DownloadManager:
    def __init__(self, max_concurrent_downloads: int = 3):
        self.task_queue = Queue()
        self.active_tasks: List[DownloadTask] = []
        self.completed_tasks: List[DownloadTask] = []
        self.max_concurrent_downloads = max_concurrent_downloads
        self.lock = threading.Lock()
        self.workers: List[threading.Thread] = []
        self.on_progress_callback: Optional[Callable] = None
        
    def add_task(self, url: str, save_path: str) -> DownloadTask:
        task = DownloadTask(url=url, save_path=save_path, status=TaskStatus.PENDING)
        self.task_queue.put(task)
        return task
    
    def start_workers(self):
        for _ in range(self.max_concurrent_downloads):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self.workers.append(worker)
    
    def _worker_loop(self):
        while True:
            task = self.task_queue.get()
            if task.status != TaskStatus.PAUSED:
                self._process_task(task)
            self.task_queue.task_done()
    
    def _process_task(self, task: DownloadTask):
        try:
            with self.lock:
                task.status = TaskStatus.DOWNLOADING
                self.active_tasks.append(task)
            
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': f'{task.save_path}/%(title)s.%(ext)s',
                'progress_hooks': [lambda d: self._progress_hook(task, d)],
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(task.url, download=True)
                task.title = info.get('title', None)
            
            with self.lock:
                task.status = TaskStatus.COMPLETED
                self.active_tasks.remove(task)
                self.completed_tasks.append(task)
                
        except Exception as e:
            with self.lock:
                task.status = TaskStatus.FAILED
                task.error_message = str(e)
                self.active_tasks.remove(task)
    
    def _progress_hook(self, task: DownloadTask, d: dict):
        if d['status'] == 'downloading':
            task.progress = float(d.get('downloaded_bytes', 0)) / float(d.get('total_bytes', 1))
            if self.on_progress_callback:
                self.on_progress_callback(task)
    
    def pause_task(self, task: DownloadTask):
        if task.status == TaskStatus.DOWNLOADING:
            task.status = TaskStatus.PAUSED
    
    def resume_task(self, task: DownloadTask):
        if task.status == TaskStatus.PAUSED:
            task.status = TaskStatus.PENDING
            self.task_queue.put(task)
    
    def get_all_tasks(self) -> List[DownloadTask]:
        return self.active_tasks + list(self.task_queue.queue) + self.completed_tasks 