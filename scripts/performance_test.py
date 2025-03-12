import time
import random
from locust import HttpUser, task, between

class DownloadUser(HttpUser):
    wait_time = between(1, 5)
    
    @task
    def download_video(self):
        test_cases = [
            '/api/download?url=https://v.douyin.com/xxxx',
            '/api/download?url=https://v.douyin.com/yyyy'
        ]
        self.client.get(random.choice(test_cases))
        
    def on_start(self):
        self.client.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

# 导出Prometheus格式的监控数据
from prometheus_client import start_http_server, Summary
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
@REQUEST_TIME.time()
def process_request(t):
    time.sleep(t)

if __name__ == "__main__":
    start_http_server(8000)