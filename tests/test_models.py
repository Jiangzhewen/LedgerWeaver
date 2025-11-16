"""
数据模型测试
"""
from decimal import Decimal
from datetime import datetime
from crypto_history_exporter.models import TradeRecord, FundingRecord, TransferRecord, FeeRecord


def test_trade_record():
    """测试交易记录模型"""
    now = datetime.utcnow()
    trade = TradeRecord(
        exchange='binance_pm',
        account_name='main_pm',
        source='rest',
        ingested_at=now,
        symbol='BTC/USDT',
        side='buy',
        order_type='limit',
        price=Decimal('50000.0'),
        amount=Decimal('0.1'),
        cost=Decimal('5000.0'),
        fee=Decimal('5.0'),
        fee_currency='USDT',
        trade_id='12345',
        order_id='67890',
        timestamp=1640995200000,
        datetime='2022-01-01T00:00:00.000Z'
    )
    
    assert trade.exchange == 'binance_pm'
    assert trade.account_name == 'main_pm'
    assert trade.source == 'rest'
    assert trade.ingested_at == now
    assert trade.symbol == 'BTC/USDT'
    assert trade.side == 'buy'
    assert trade.order_type == 'limit'
    assert trade.price == Decimal('50000.0')
    assert trade.amount == Decimal('0.1')
    assert trade.cost == Decimal('5000.0')
    assert trade.fee == Decimal('5.0')
    assert trade.fee_currency == 'USDT'
    assert trade.trade_id == '12345'
    assert trade.order_id == '67890'
    assert trade.timestamp == 1640995200000
    assert trade.datetime == '2022-01-01T00:00:00.000Z'


def test_funding_record():
    """测试资金费记录模型"""
    now = datetime.utcnow()
    funding = FundingRecord(
        exchange='binance_pm',
        account_name='main_pm',
        source='rest',
        ingested_at=now,
        symbol='BTC/USDT',
        funding_rate=Decimal('0.0001'),
        funding_fee=Decimal('0.5'),
        position_size=Decimal('1.0'),
        timestamp=1640995200000,
        datetime='2022-01-01T00:00:00.000Z'
    )
    
    assert funding.exchange == 'binance_pm'
    assert funding.account_name == 'main_pm'
    assert funding.source == 'rest'
    assert funding.ingested_at == now
    assert funding.symbol == 'BTC/USDT'
    assert funding.funding_rate == Decimal('0.0001')
    assert funding.funding_fee == Decimal('0.5')
    assert funding.position_size == Decimal('1.0')
    assert funding.timestamp == 1640995200000
    assert funding.datetime == '2022-01-01T00:00:00.000Z'


def test_transfer_record():
    """测试充提记录模型"""
    now = datetime.utcnow()
    transfer = TransferRecord(
        exchange='binance_pm',
        account_name='main_pm',
        source='rest',
        ingested_at=now,
        direction='deposit',
        currency='BTC',
        amount=Decimal('1.0'),
        network='Bitcoin',
        address='1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
        tx_hash='abc123',
        status='success',
        timestamp=1640995200000,
        datetime='2022-01-01T00:00:00.000Z'
    )
    
    assert transfer.exchange == 'binance_pm'
    assert transfer.account_name == 'main_pm'
    assert transfer.source == 'rest'
    assert transfer.ingested_at == now
    assert transfer.direction == 'deposit'
    assert transfer.currency == 'BTC'
    assert transfer.amount == Decimal('1.0')
    assert transfer.network == 'Bitcoin'
    assert transfer.address == '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa'
    assert transfer.tx_hash == 'abc123'
    assert transfer.status == 'success'
    assert transfer.timestamp == 1640995200000
    assert transfer.datetime == '2022-01-01T00:00:00.000Z'


def test_fee_record():
    """测试费用记录模型"""
    now = datetime.utcnow()
    fee = FeeRecord(
        exchange='binance_pm',
        account_name='main_pm',
        source='rest',
        ingested_at=now,
        fee_type='trading_fee',
        currency='USDT',
        amount=Decimal('5.0'),
        trade_id='12345',
        timestamp=1640995200000,
        datetime='2022-01-01T00:00:00.000Z'
    )
    
    assert fee.exchange == 'binance_pm'
    assert fee.account_name == 'main_pm'
    assert fee.source == 'rest'
    assert fee.ingested_at == now
    assert fee.fee_type == 'trading_fee'
    assert fee.currency == 'USDT'
    assert fee.amount == Decimal('5.0')
    assert fee.trade_id == '12345'
    assert fee.timestamp == 1640995200000
    assert fee.datetime == '2022-01-01T00:00:00.000Z'