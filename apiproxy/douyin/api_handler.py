# -*- coding: utf-8 -*-

import re
import json
import time
from typing import Tuple, Optional
from requests.exceptions import RequestException
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.console import Console

from apiproxy.douyin import douyin_headers
from apiproxy.douyin.urls import Urls
from apiproxy.douyin.result import Result
from apiproxy.common import utils
from utils import logger

class APIHandler:
    def __init__(self):
        self.urls = Urls()
        self.result = Result()
        self.timeout = 10
        self.console = Console()

    def getShareLink(self, string: str) -> str:
        return re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*(),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', string)[0]

    def getKey(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        key = None
        key_type = None

        try:
            r = requests.get(url=url, headers=douyin_headers)
        except Exception as e:
            print('[  错误  ]:输入链接有误！\r')
            return key_type, key

        urlstr = str(r.request.path_url)

        if "/user/" in urlstr:
            if '?' in r.request.path_url:
                for one in re.finditer(r'user\/([\d\D]*)([?])', str(r.request.path_url)):
                    key = one.group(1)
            else:
                for one in re.finditer(r'user\/([\d\D]*)', str(r.request.path_url)):
                    key = one.group(1)
            key_type = "user"
        elif "/video/" in urlstr:
            key = re.findall('video/(\d+)?', urlstr)[0]
            key_type = "aweme"
        elif "/note/" in urlstr:
            key = re.findall('note/(\d+)?', urlstr)[0]
            key_type = "aweme"
        elif "/mix/detail/" in urlstr:
            key = re.findall('/mix/detail/(\d+)?', urlstr)[0]
            key_type = "mix"
        elif "/collection/" in urlstr:
            key = re.findall('/collection/(\d+)?', urlstr)[0]
            key_type = "mix"
        elif "/music/" in urlstr:
            key = re.findall('music/(\d+)?', urlstr)[0]
            key_type = "music"
        elif "/webcast/reflow/" in urlstr:
            key1 = re.findall('reflow/(\d+)?', urlstr)[0]
            url = self.urls.LIVE2 + utils.getXbogus(
                f'live_id=1&room_id={key1}&app_id=1128')
            res = requests.get(url, headers=douyin_headers)
            resjson = json.loads(res.text)
            key = resjson['data']['room']['owner']['web_rid']
            key_type = "live"
        elif "live.douyin.com" in r.url:
            key = r.url.replace('https://live.douyin.com/', '')
            key_type = "live"

        if key is None or key_type is None:
            print('[  错误  ]:输入链接有误！无法获取 id\r')
            return key_type, key

        return key_type, key

    def getAwemeInfo(self, aweme_id: str) -> dict:
        retries = 3
        for attempt in range(retries):
            try:
                print('[  提示  ]:正在请求的作品 id = %s\r' % aweme_id)
                if aweme_id is None:
                    return {}

                start = time.time()
                while True:
                    try:
                        jx_url = self.urls.POST_DETAIL + utils.getXbogus(
                            f'aweme_id={aweme_id}&device_platform=webapp&aid=6383')

                        raw = requests.get(url=jx_url, headers=douyin_headers).text
                        datadict = json.loads(raw)
                        if datadict is not None and datadict["status_code"] == 0:
                            break
                    except Exception as e:
                        end = time.time()
                        if end - start > self.timeout:
                            print("[  提示  ]:重复请求该接口" + str(self.timeout) + "s, 仍然未获取到数据")
                            return {}

                self.result.clearDict(self.result.awemeDict)
                awemeType = 0
                try:
                    if datadict['aweme_detail']["images"] is not None:
                        awemeType = 1
                except Exception as e:
                    print("[  警告  ]:接口中未找到 images\r")

                self.result.dataConvert(awemeType, self.result.awemeDict, datadict['aweme_detail'])
                return self.result.awemeDict
            except RequestException as e:
                logger.warning(f"请求失败（尝试 {attempt+1}/{retries}）: {str(e)}")
                time.sleep(2 ** attempt)
            except KeyError as e:
                logger.error(f"响应数据格式异常: {str(e)}")
                break
        return {}