"""
网络代理配置 - 解决连接问题
"""
import os
import aiohttp
from typing import Optional

class ProxyConfig:
    """代理配置管理"""
    
    def __init__(self):
        # 从环境变量读取代理设置
        self.http_proxy = os.getenv('HTTP_PROXY', '')
        self.https_proxy = os.getenv('HTTPS_PROXY', '')
        
        # 如果没有配置，尝试常见的代理端口
        if not self.http_proxy:
            self.http_proxy = self._detect_proxy()
    
    def _detect_proxy(self) -> str:
        """自动检测本地代理"""
        common_proxies = [
            'http://127.0.0.1:7890',  # Clash
            'http://127.0.0.1:7891',  # Clash
            'http://127.0.0.1:1080',  # Shadowsocks
            'http://127.0.0.1:10809', # V2Ray
        ]
        
        # 这里可以添加检测逻辑
        # 暂时返回空，让用户手动配置
        return ''
    
    def get_connector(self) -> Optional[aiohttp.TCPConnector]:
        """获取带代理的连接器"""
        if self.http_proxy or self.https_proxy:
            return aiohttp.TCPConnector(ssl=False)
        return None
    
    def get_proxy_url(self) -> Optional[str]:
        """获取代理URL"""
        return self.https_proxy or self.http_proxy or None


# 全局代理配置
proxy_config = ProxyConfig()


def get_session_with_proxy() -> aiohttp.ClientSession:
    """创建带代理的会话"""
    proxy_url = proxy_config.get_proxy_url()
    connector = proxy_config.get_connector()
    
    if proxy_url:
        return aiohttp.ClientSession(
            connector=connector,
            trust_env=True
        )
    else:
        return aiohttp.ClientSession()


# 使用示例
async def fetch_with_proxy(url: str, **kwargs):
    """使用代理获取数据"""
    proxy_url = proxy_config.get_proxy_url()
    
    async with get_session_with_proxy() as session:
        if proxy_url:
            kwargs['proxy'] = proxy_url
        
        async with session.get(url, **kwargs) as resp:
            return await resp.json()


