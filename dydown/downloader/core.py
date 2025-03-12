"""
异步下载器核心模块

实现基于asyncio的协程池管理和下载队列调度
"""
import asyncio
from typing import Optional
from ..common import logger

class AsyncDownloader:
    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.queue = asyncio.PriorityQueue()
        self.semaphore = asyncio.Semaphore(max_workers)
        self.active_tasks = set()
        self.failed_tasks = dict()
        self.lock = asyncio.Lock()

    async def add_task(self, url: str):
        await self.queue.put(url)

    async def worker(self):
        while True:
            async with self.semaphore:
                # 批量获取任务（每次处理5个）
                tasks = [await self.queue.get() for _ in range(5) if not self.queue.empty()]
                async with self.lock:
                    self.active_tasks.update(tasks)
                
                try:
                    # 使用gather并行处理批量任务
                    results = await asyncio.gather(*[self._download(task.url) for task in tasks])
                    
                    for task, result in zip(tasks, results):
                        if result.get('status') == 'failed' and task.retries > 0:
                            task.retries -= 1
                            await self.queue.put(task)
                except Exception as e:
                    logger.error(f"批量任务处理异常: {str(e)}")
                finally:
                    async with self.lock:
                        for task in tasks:
                            self.active_tasks.remove(task)
                    for _ in tasks:
                        self.queue.task_done()

    async def _download(self, url: str):
        try:
            # 实际下载逻辑
            from ..common import utils
from pathlib import Path
import os

        # 生成作者文件夹路径
        author_id = url.split('/')[-2]
        author_name = await DouyinParser.get_author_info(url)
        save_path = Path(config['download']['path']) / utils.replaceStr(f"{author_name}_{author_id}")
        save_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"开始下载：{url}"
            file_path = save_path / f"{utils.replaceStr(title)}.mp4"
        await self._save_file(content, file_path)
        
        # 记录下载元数据
        await self._save_metadata(author_id, file_path)
        
        await asyncio.sleep(0.1)  # 模拟下载
        except Exception as e:
            logger.error(f"下载失败：{str(e)}")

    async def start(self):
        workers = [asyncio.create_task(self.worker()) for _ in range(self.max_workers)]
        await asyncio.gather(*workers)

    async def stop(self):
        await self.queue.join()
        for task in self.tasks:
            task.cancel()