"""
配置加载模块
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from decimal import Decimal
import yaml
import os


@dataclass
class AccountConfig:
    """账户配置"""
    name: str
    api_key: str
    api_secret: str
    account_type: str
    passphrase: Optional[str] = None
    flag: Optional[str] = None


@dataclass
class RateLimitConfig:
    """限频配置"""
    max_requests_per_minute: int = 1200
    max_weight_per_minute: int = 6000


@dataclass
class ExchangeConfig:
    """交易所配置"""
    enabled: bool
    accounts: List[AccountConfig]
    rate_limit: RateLimitConfig


@dataclass
class GlobalConfig:
    """全局配置"""
    proxy: Optional[str] = None
    retry_times: int = 3
    timeout: int = 30


class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_path: str = "config.yml"):
        self.config_path = config_path
        self._config = None
    
    def load(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self._config is not None:
            return self._config
            
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # 解析环境变量
        self._config = self._resolve_env_vars(config_data)
        return self._config
    
    def _resolve_env_vars(self, config: Dict) -> Dict:
        """解析配置中的环境变量"""
        if isinstance(config, dict):
            return {k: self._resolve_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._resolve_env_vars(item) for item in config]
        elif isinstance(config, str) and config.startswith('${') and config.endswith('}'):
            env_var = config[2:-1]
            return os.environ.get(env_var, config)
        else:
            return config
    
    def get_global_config(self) -> GlobalConfig:
        """获取全局配置"""
        config = self.load()
        global_config = config.get('global', {})
        return GlobalConfig(
            proxy=global_config.get('proxy'),
            retry_times=global_config.get('retry_times', 3),
            timeout=global_config.get('timeout', 30)
        )
    
    def get_exchange_config(self, exchange_name: str) -> ExchangeConfig:
        """获取指定交易所配置"""
        config = self.load()
        exchange_data = config.get('exchanges', {}).get(exchange_name, {})
        
        # 解析账户配置
        accounts = []
        for account_data in exchange_data.get('accounts', []):
            accounts.append(AccountConfig(
                name=account_data['name'],
                api_key=account_data['api_key'],
                api_secret=account_data['api_secret'],
                account_type=account_data['account_type'],
                passphrase=account_data.get('passphrase'),
                flag=account_data.get('flag')
            ))
        
        # 解析限频配置
        rate_limit_data = exchange_data.get('rate_limit', {})
        rate_limit = RateLimitConfig(
            max_requests_per_minute=rate_limit_data.get('max_requests_per_minute', 1200),
            max_weight_per_minute=rate_limit_data.get('max_weight_per_minute', 6000)
        )
        
        return ExchangeConfig(
            enabled=exchange_data.get('enabled', True),
            accounts=accounts,
            rate_limit=rate_limit
        )