from enum import Enum
from dataclasses import dataclass

class TaskStatus(Enum):
    PENDING = '等待中'
    DOWNLOADING = '下载中'
    PAUSED = '已暂停'
    COMPLETED = '已完成'
    FAILED = '失败'

@dataclass
class DownloadTask:
    url: str
    save_path: str
    progress: float = 0.0
    status: TaskStatus = TaskStatus.PENDING
    title: str = None

class DownloadManager:
    def __init__(self):
        self.tasks = []
        self.on_progress_callback = None

    def add_task(self, url: str, save_path: str) -> DownloadTask:
        task = DownloadTask(url=url, save_path=save_path)
        self.tasks.append(task)
        return task

    def start_workers(self):
        pass

    def pause_task(self, task: DownloadTask):
        task.status = TaskStatus.PAUSED

    def resume_task(self, task: DownloadTask):
        task.status = TaskStatus.DOWNLOADING

    def on_progress_callback(self, task: DownloadTask):
        pass