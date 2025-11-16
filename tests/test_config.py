"""
配置模块测试
"""
import os
import tempfile
import yaml
from crypto_history_exporter.config import ConfigLoader, AccountConfig, RateLimitConfig, ExchangeConfig, GlobalConfig


def test_config_loader():
    """测试配置加载器"""
    # 创建临时配置文件
    config_data = {
        'global': {
            'retry_times': 5,
            'timeout': 60
        },
        'exchanges': {
            'binance_pm': {
                'enabled': True,
                'accounts': [
                    {
                        'name': 'main_pm',
                        'api_key': '${BINANCE_PM_API_KEY}',
                        'api_secret': '${BINANCE_PM_API_SECRET}',
                        'account_type': 'portfolio_margin'
                    }
                ],
                'rate_limit': {
                    'max_requests_per_minute': 1200,
                    'max_weight_per_minute': 6000
                }
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(config_data, f)
        config_file = f.name
    
    try:
        # 设置环境变量
        os.environ['BINANCE_PM_API_KEY'] = 'test_key'
        os.environ['BINANCE_PM_API_SECRET'] = 'test_secret'
        
        # 测试配置加载
        loader = ConfigLoader(config_file)
        
        # 测试全局配置
        global_config = loader.get_global_config()
        assert isinstance(global_config, GlobalConfig)
        assert global_config.retry_times == 5
        assert global_config.timeout == 60
        
        # 测试交易所配置
        exchange_config = loader.get_exchange_config('binance_pm')
        assert isinstance(exchange_config, ExchangeConfig)
        assert exchange_config.enabled is True
        assert len(exchange_config.accounts) == 1
        
        # 测试账户配置
        account = exchange_config.accounts[0]
        assert isinstance(account, AccountConfig)
        assert account.name == 'main_pm'
        assert account.api_key == 'test_key'
        assert account.api_secret == 'test_secret'
        assert account.account_type == 'portfolio_margin'
        
        # 测试限频配置
        rate_limit = exchange_config.rate_limit
        assert isinstance(rate_limit, RateLimitConfig)
        assert rate_limit.max_requests_per_minute == 1200
        assert rate_limit.max_weight_per_minute == 6000
        
    finally:
        # 清理
        os.unlink(config_file)
        os.environ.pop('BINANCE_PM_API_KEY', None)
        os.environ.pop('BINANCE_PM_API_SECRET', None)


def test_config_loader_with_missing_env():
    """测试配置加载器处理缺失环境变量"""
    # 创建临时配置文件
    config_data = {
        'exchanges': {
            'binance_pm': {
                'enabled': True,
                'accounts': [
                    {
                        'name': 'main_pm',
                        'api_key': '${MISSING_API_KEY}',
                        'api_secret': '${MISSING_API_SECRET}',
                        'account_type': 'portfolio_margin'
                    }
                ],
                'rate_limit': {
                    'max_requests_per_minute': 1200
                }
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(config_data, f)
        config_file = f.name
    
    try:
        # 测试配置加载
        loader = ConfigLoader(config_file)
        exchange_config = loader.get_exchange_config('binance_pm')
        account = exchange_config.accounts[0]
        
        # 应该返回原始字符串而不是环境变量值
        assert account.api_key == '${MISSING_API_KEY}'
        assert account.api_secret == '${MISSING_API_SECRET}'
        
    finally:
        # 清理
        os.unlink(config_file)