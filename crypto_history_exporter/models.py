"""
统一数据结构模型
"""
from dataclasses import dataclass
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


@dataclass
class BaseRecord:
    """基础记录"""
    exchange: str
    account_name: str
    source: str
    ingested_at: datetime


@dataclass
class TradeRecord(BaseRecord):
    """交易记录"""
    symbol: str
    side: str  # buy/sell
    order_type: str  # limit/market
    price: Decimal
    amount: Decimal
    cost: Decimal
    fee: Decimal
    fee_currency: str
    trade_id: str
    order_id: str
    timestamp: int  # UTC毫秒时间戳
    datetime: str  # ISO8601字符串
    # 扩展字段
    position_side: Optional[str] = None  # long/short/dual
    liquidity: Optional[str] = None  # maker/taker
    fee_rate: Optional[Decimal] = None
    realized_pnl: Optional[Decimal] = None
    raw: Optional[dict] = None


@dataclass
class FundingRecord(BaseRecord):
    """资金费记录"""
    symbol: str
    funding_rate: Optional[Decimal]
    funding_fee: Decimal
    position_size: Optional[Decimal]
    timestamp: int  # UTC毫秒时间戳
    datetime: str  # ISO8601字符串
    # 扩展字段
    settlement_period: Optional[str] = None  # 8h, 1h
    funding_index: Optional[str] = None
    cycle: Optional[str] = None
    raw: Optional[dict] = None


@dataclass
class TransferRecord(BaseRecord):
    """充提记录"""
    direction: str  # deposit/withdrawal
    currency: str
    amount: Decimal
    network: Optional[str]  # 链名称
    address: Optional[str]
    tx_hash: Optional[str]
    status: str  # pending/success/failed
    timestamp: int  # UTC毫秒时间戳
    datetime: str  # ISO8601字符串
    # 扩展字段
    fee: Optional[Decimal] = None
    fee_currency: Optional[str] = None
    internal_transfer: Optional[bool] = False  # 内部划转标记
    tag: Optional[str] = None  # 地址备注
    memo: Optional[str] = None
    raw: Optional[dict] = None


@dataclass
class FeeRecord(BaseRecord):
    """费用记录"""
    fee_type: str  # trading_fee, funding_fee, interest, earn_interest, liquidation, rebate, bonus
    currency: str
    amount: Decimal
    timestamp: int  # UTC毫秒时间戳
    datetime: str  # ISO8601字符串
    # 关联ID
    trade_id: Optional[str] = None
    order_id: Optional[str] = None
    funding_id: Optional[str] = None
    raw: Optional[dict] = None