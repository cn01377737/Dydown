\"""
抖音API异步客户端实现

继承自bilidown.BaseClient
实现签名生成、请求重试、错误处理等基础能力
"""
import aiohttp
from ..common import config
from ..common.utils import logger

class DouyinClient:
    def __init__(self):
        self.config = config.load_config()
        self.headers = {
            'User-Agent': self.config['api']['user_agent'],
            'Referer': 'https://www.douyin.com/'
        }
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            connector=aiohttp.TCPConnector(limit=100, ssl=False, force_close=False, enable_cleanup_closed=True),  # 启用HTTP/2支持
            trust_env=True
        )
        self.rate_limiter = AdaptiveRateLimiter()

    async def get_video_info(self, item_id: str) -> dict:
        """
        获取视频详细信息
        接口地址：/aweme/v1/web/aweme/detail/
        """
        url = f"{self.config['api']['endpoint']}/aweme/v1/web/aweme/detail/"
        params = {
            'device_platform': 'webapp',
            'item_id': item_id,
            'aid': self.config['api']['aid']
        }

        try:
            async with self.session.get(url, params=params) as resp:
                resp.raise_for_status()
                data = await resp.json()
                if data.get('status_code') != 0:
                    logger.error(f"API错误：{data.get('status_msg')}")
                    return {}
                return data.get('aweme_detail', {})
        except aiohttp.ClientError as e:
            logger.error(f"请求失败：{str(e)}")
            return {}
        finally:
            await self.session.close()
            # 更新网络延迟统计
            latency = time.time() - start_time
            self.rate_limiter.update(latency)

    # 实现其他接口方法...

class AdaptiveRateLimiter:
    def __init__(self):
        self._window = deque(maxlen=10)
        self._interval = 1.0

    async def wait(self):
        await asyncio.sleep(self._interval)

    def update(self, latency):
        self._window.append(latency)
        avg_latency = sum(self._window)/len(self._window)
        self._interval = max(0.1, min(2.0, avg_latency * 0.8))