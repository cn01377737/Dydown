"""
抖音开放平台API接口模块

遵循bilidown架构规范：
- 所有API接口统一使用异步async/await语法
- 错误处理遵循统一异常体系
- 请求头签名逻辑抽离到独立模块
"""

from .client import DouyinClient

__all__ = ['DouyinClient']