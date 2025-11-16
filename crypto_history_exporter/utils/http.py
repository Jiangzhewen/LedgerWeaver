"""
HTTP请求/限频/重试封装
"""
import time
import hashlib
import hmac
import urllib.parse
from typing import Dict, Any, Optional
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimitInfo:
    """限频信息"""
    used_weight: int = 0
    max_weight: int = 6000
    reset_time: float = 0


class HTTPClient:
    """HTTP客户端，支持限频和重试"""
    
    def __init__(self, timeout: int = 30, retry_times: int = 3, rate_limit: Optional[RateLimitInfo] = None):
        self.timeout = timeout
        self.retry_times = retry_times
        self.rate_limit = rate_limit or RateLimitInfo()
        
        # 创建session并配置重试策略
        self.session = requests.Session()
        retry_strategy = Retry(
            total=retry_times,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _check_rate_limit(self):
        """检查限频并等待"""
        if self.rate_limit.reset_time > time.time():
            sleep_time = self.rate_limit.reset_time - time.time()
            logger.debug(f"接近限频，等待 {sleep_time:.2f} 秒")
            time.sleep(sleep_time)
    
    def _update_rate_limit(self, response):
        """更新限频信息"""
        # Binance限频头
        used_weight_1m = response.headers.get('X-MBX-USED-WEIGHT-1M')
        sapi_used_weight = response.headers.get('X-SAPI-USED-IP-WEIGHT-1M')
        
        # OKX限频头
        rate_limit_remaining = response.headers.get('X-RateLimit-Remaining')
        rate_limit_reset = response.headers.get('X-RateLimit-Reset')
        
        if used_weight_1m:
            self.rate_limit.used_weight = int(used_weight_1m)
        elif sapi_used_weight:
            self.rate_limit.used_weight = int(sapi_used_weight)
        
        if rate_limit_remaining and int(rate_limit_remaining) < 10:
            if rate_limit_reset:
                self.rate_limit.reset_time = time.time() + int(rate_limit_reset)
    
    def get(self, url: str, params: Optional[Dict] = None, headers: Optional[Dict] = None, **kwargs) -> requests.Response:
        """GET请求"""
        self._check_rate_limit()
        
        response = self.session.get(url, params=params, headers=headers, timeout=self.timeout, **kwargs)
        self._update_rate_limit(response)
        
        # 处理429错误
        if response.status_code == 429:
            logger.warning("遇到限频错误，等待后重试")
            time.sleep(2 ** self.retry_times)  # 指数退避
            response = self.session.get(url, params=params, headers=headers, timeout=self.timeout, **kwargs)
        
        return response
    
    def post(self, url: str, data: Optional[Dict] = None, headers: Optional[Dict] = None, **kwargs) -> requests.Response:
        """POST请求"""
        self._check_rate_limit()
        
        response = self.session.post(url, json=data, headers=headers, timeout=self.timeout, **kwargs)
        self._update_rate_limit(response)
        
        # 处理429错误
        if response.status_code == 429:
            logger.warning("遇到限频错误，等待后重试")
            time.sleep(2 ** self.retry_times)  # 指数退避
            response = self.session.post(url, json=data, headers=headers, timeout=self.timeout, **kwargs)
        
        return response


def generate_signature(secret: str, data: str) -> str:
    """生成HMAC-SHA256签名"""
    return hmac.new(secret.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()


def redact_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """脱敏敏感数据"""
    sensitive_fields = ['api_key', 'api_secret', 'passphrase', 'signature', 'key', 'secret']
    redacted_data = data.copy()
    
    for key, value in redacted_data.items():
        if isinstance(value, str) and any(field in key.lower() for field in sensitive_fields):
            if len(value) > 6:
                redacted_data[key] = f"{value[:3]}***{value[-3:]}"
            else:
                redacted_data[key] = "***"
    
    return redacted_data