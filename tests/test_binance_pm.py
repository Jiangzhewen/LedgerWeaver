"""
Binance Portfolio Margin 适配器测试
"""
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock, patch

from crypto_history_exporter.exchanges.binance_pm import BinancePMClient
from crypto_history_exporter.config import ExchangeConfig, AccountConfig, RateLimitConfig
from crypto_history_exporter.models import TradeRecord, FundingRecord, TransferRecord, FeeRecord


def create_binance_pm_config():
    """创建 Binance Portfolio Margin 配置"""
    account = AccountConfig(
        name="test_account",
        api_key="test_api_key",
        api_secret="test_api_secret",
        account_type="portfolio_margin"
    )
    
    rate_limit = RateLimitConfig(
        max_requests_per_minute=1200,
        max_weight_per_minute=6000
    )
    
    return ExchangeConfig(
        enabled=True,
        accounts=[account],
        rate_limit=rate_limit
    )


def create_binance_pm_client():
    """创建 Binance Portfolio Margin 客户端"""
    config = create_binance_pm_config()
    return BinancePMClient(config)


def test_binance_pm_client_init():
    """测试 Binance Portfolio Margin 客户端初始化"""
    client = create_binance_pm_client()
    assert client.name == "binancepm"
    assert client.base_url == "https://papi.binance.com"


@patch('crypto_history_exporter.exchanges.binance_pm.HTTPClient')
def test_fetch_trades(mock_http_client):
    """测试获取交易历史"""
    # 创建客户端
    client = create_binance_pm_client()
    
    # 模拟 HTTP 响应
    mock_response = Mock()
    mock_response.json.return_value = {
        'data': [
            {
                'symbol': 'BTCUSDT',
                'side': 'BUY',
                'type': 'LIMIT',
                'price': '50000.0',
                'qty': '0.1',
                'commission': '5.0',
                'commissionAsset': 'USDT',
                'id': 12345,
                'orderId': 67890,
                'time': 1640995200000
            }
        ]
    }
    mock_response.raise_for_status.return_value = None
    
    # 设置 mock
    mock_http_instance = Mock()
    mock_http_instance.get.return_value = mock_response
    mock_http_client.return_value = mock_http_instance
    
    # 设置客户端的 account_clients
    client.account_clients['test_account'] = mock_http_instance
    
    # 调用方法
    start_time = datetime(2022, 1, 1, tzinfo=timezone.utc)
    end_time = datetime(2022, 1, 2, tzinfo=timezone.utc)
    trades = client.fetch_trades(start_time, end_time)
    
    # 验证结果
    assert len(trades) == 1
    trade = trades[0]
    assert isinstance(trade, TradeRecord)
    assert trade.exchange == 'binance_pm'
    assert trade.account_name == 'test_account'
    assert trade.symbol == 'BTCUSDT'
    assert trade.side == 'buy'
    assert trade.order_type == 'limit'
    assert trade.price == Decimal('50000.0')
    assert trade.amount == Decimal('0.1')
    assert trade.fee == Decimal('5.0')
    assert trade.fee_currency == 'USDT'
    assert trade.trade_id == '12345'
    assert trade.order_id == '67890'
    assert trade.timestamp == 1640995200000


@patch('crypto_history_exporter.exchanges.binance_pm.HTTPClient')
def test_fetch_funding(mock_http_client):
    """测试获取资金费历史"""
    # 创建客户端
    client = create_binance_pm_client()
    
    # 模拟 HTTP 响应
    mock_response = Mock()
    mock_response.json.return_value = {
        'data': [
            {
                'symbol': 'BTCUSDT',
                'fundingRate': '0.0001',
                'fee': '-0.5',
                'positionSize': '1.0',
                'time': 1640995200000
            }
        ]
    }
    mock_response.raise_for_status.return_value = None
    
    # 设置 mock
    mock_http_instance = Mock()
    mock_http_instance.get.return_value = mock_response
    mock_http_client.return_value = mock_http_instance
    
    # 设置客户端的 account_clients
    client.account_clients['test_account'] = mock_http_instance
    
    # 调用方法
    start_time = datetime(2022, 1, 1, tzinfo=timezone.utc)
    end_time = datetime(2022, 1, 2, tzinfo=timezone.utc)
    fundings = client.fetch_funding(start_time, end_time)
    
    # 验证结果
    assert len(fundings) == 1
    funding = fundings[0]
    assert isinstance(funding, FundingRecord)
    assert funding.exchange == 'binance_pm'
    assert funding.account_name == 'test_account'
    assert funding.symbol == 'BTCUSDT'
    assert funding.funding_rate == Decimal('0.0001')
    assert funding.funding_fee == Decimal('-0.5')
    assert funding.position_size == Decimal('1.0')
    assert funding.timestamp == 1640995200000


@patch('crypto_history_exporter.exchanges.binance_pm.HTTPClient')
def test_fetch_deposits(mock_http_client):
    """测试获取充值记录"""
    # 创建客户端
    client = create_binance_pm_client()
    
    # 模拟 HTTP 响应
    mock_response = Mock()
    mock_response.json.return_value = [
        {
            'coin': 'BTC',
            'amount': '1.0',
            'network': 'Bitcoin',
            'address': '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
            'txId': 'abc123',
            'status': 1,
            'insertTime': 1640995200000
        }
    ]
    mock_response.raise_for_status.return_value = None
    
    # 设置 mock
    mock_http_instance = Mock()
    mock_http_instance.get.return_value = mock_response
    mock_http_client.return_value = mock_http_instance
    
    # 调用方法
    start_time = datetime(2022, 1, 1, tzinfo=timezone.utc)
    end_time = datetime(2022, 1, 2, tzinfo=timezone.utc)
    deposits = client.fetch_deposits(start_time, end_time)
    
    # 验证结果
    assert len(deposits) == 1
    deposit = deposits[0]
    assert isinstance(deposit, TransferRecord)
    assert deposit.exchange == 'binance_pm'
    assert deposit.account_name == 'test_account'
    assert deposit.direction == 'deposit'
    assert deposit.currency == 'BTC'
    assert deposit.amount == Decimal('1.0')
    assert deposit.network == 'Bitcoin'
    assert deposit.address == '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'
    assert deposit.tx_hash == 'abc123'
    assert deposit.status == 'success'
    assert deposit.timestamp == 1640995200000


@patch('crypto_history_exporter.exchanges.binance_pm.HTTPClient')
def test_fetch_withdrawals(mock_http_client):
    """测试获取提现记录"""
    # 创建客户端
    client = create_binance_pm_client()
    
    # 模拟 HTTP 响应
    mock_response = Mock()
    mock_response.json.return_value = [
        {
            'coin': 'BTC',
            'amount': '1.0',
            'network': 'Bitcoin',
            'address': '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
            'txId': 'abc123',
            'status': 6,
            'applyTime': '2022-01-01 12:00:00',
            'transactionFee': '0.001'
        }
    ]
    mock_response.raise_for_status.return_value = None
    
    # 设置 mock
    mock_http_instance = Mock()
    mock_http_instance.get.return_value = mock_response
    mock_http_client.return_value = mock_http_instance
    
    # 调用方法
    start_time = datetime(2022, 1, 1, tzinfo=timezone.utc)
    end_time = datetime(2022, 1, 2, tzinfo=timezone.utc)
    withdrawals = client.fetch_withdrawals(start_time, end_time)
    
    # 验证结果
    assert len(withdrawals) == 1
    withdrawal = withdrawals[0]
    assert isinstance(withdrawal, TransferRecord)
    assert withdrawal.exchange == 'binance_pm'
    assert withdrawal.account_name == 'test_account'
    assert withdrawal.direction == 'withdrawal'
    assert withdrawal.currency == 'BTC'
    assert withdrawal.amount == Decimal('1.0')
    assert withdrawal.network == 'Bitcoin'
    assert withdrawal.address == '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'
    assert withdrawal.tx_hash == 'abc123'
    assert withdrawal.status == 'success'
    assert withdrawal.fee == Decimal('0.001')
    assert withdrawal.fee_currency == 'BTC'