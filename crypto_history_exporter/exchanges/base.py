"""
交易所抽象基类
"""
from abc import ABC, abstractmethod
from typing import List, Iterator, Optional
from datetime import datetime
from decimal import Decimal

from ..config import ExchangeConfig
from ..models import TradeRecord, FundingRecord, TransferRecord, FeeRecord


class ExchangeClient(ABC):
    """交易所客户端抽象基类"""
    
    def __init__(self, config: ExchangeConfig):
        self.config = config
        self.name = self.__class__.__name__.replace('Client', '').lower()
    
    @abstractmethod
    def fetch_trades(self, start_time: datetime, end_time: datetime, symbols: Optional[List[str]] = None) -> List[TradeRecord]:
        """获取交易历史"""
        pass
    
    @abstractmethod
    def iter_trades(self, start_time: datetime, end_time: datetime, symbols: Optional[List[str]] = None) -> Iterator[TradeRecord]:
        """流式获取交易历史"""
        pass
    
    @abstractmethod
    def fetch_funding(self, start_time: datetime, end_time: datetime, symbols: Optional[List[str]] = None) -> List[FundingRecord]:
        """获取资金费历史"""
        pass
    
    @abstractmethod
    def iter_funding(self, start_time: datetime, end_time: datetime, symbols: Optional[List[str]] = None) -> Iterator[FundingRecord]:
        """流式获取资金费历史"""
        pass
    
    @abstractmethod
    def fetch_deposits(self, start_time: datetime, end_time: datetime) -> List[TransferRecord]:
        """获取充值记录"""
        pass
    
    @abstractmethod
    def iter_deposits(self, start_time: datetime, end_time: datetime) -> Iterator[TransferRecord]:
        """流式获取充值记录"""
        pass
    
    @abstractmethod
    def fetch_withdrawals(self, start_time: datetime, end_time: datetime) -> List[TransferRecord]:
        """获取提现记录"""
        pass
    
    @abstractmethod
    def iter_withdrawals(self, start_time: datetime, end_time: datetime) -> Iterator[TransferRecord]:
        """流式获取提现记录"""
        pass
    
    def fetch_all_data(self, start_time: datetime, end_time: datetime, data_types: List[str], symbols: Optional[List[str]] = None) -> dict:
        """获取所有类型的数据"""
        result = {}
        
        if 'trades' in data_types:
            result['trades'] = self.fetch_trades(start_time, end_time, symbols)
        
        if 'funding' in data_types:
            result['funding'] = self.fetch_funding(start_time, end_time, symbols)
        
        if 'deposits' in data_types:
            result['deposits'] = self.fetch_deposits(start_time, end_time)
        
        if 'withdrawals' in data_types:
            result['withdrawals'] = self.fetch_withdrawals(start_time, end_time)
        
        # 扩展类型
        if 'interest' in data_types:
            result['interest'] = self.fetch_interest(start_time, end_time)
        
        if 'earn_interest' in data_types:
            result['earn_interest'] = self.fetch_earn_interest(start_time, end_time)
        
        if 'liquidation' in data_types:
            result['liquidation'] = self.fetch_liquidation(start_time, end_time)
        
        if 'rebate' in data_types:
            result['rebate'] = self.fetch_rebate(start_time, end_time)
        
        return result
    
    def fetch_interest(self, start_time: datetime, end_time: datetime) -> List[FeeRecord]:
        """获取杠杆/合约借币利息（可选实现）"""
        return []
    
    def fetch_earn_interest(self, start_time: datetime, end_time: datetime) -> List[FeeRecord]:
        """获取理财/赚币利息（可选实现）"""
        return []
    
    def fetch_liquidation(self, start_time: datetime, end_time: datetime) -> List[FeeRecord]:
        """获取强平/清算记录（可选实现）"""
        return []
    
    def fetch_rebate(self, start_time: datetime, end_time: datetime) -> List[FeeRecord]:
        """获取返佣/奖励/活动发放（可选实现）"""
        return []


def get_exchange_client(exchange_name: str, config: ExchangeConfig) -> ExchangeClient:
    """获取交易所客户端实例"""
    # 动态导入交易所客户端
    if exchange_name == 'binance_pm':
        # 延迟导入，避免循环依赖
        from crypto_history_exporter.exchanges.binance_pm import BinancePMClient
        return BinancePMClient(config)
    elif exchange_name == 'hyperliquid':
        from crypto_history_exporter.exchanges.hyperliquid import HyperliquidClient
        return HyperliquidClient(config)
    elif exchange_name == 'whitebit':
        from crypto_history_exporter.exchanges.whitebit import WhitebitClient
        return WhitebitClient(config)
    elif exchange_name == 'okx':
        from crypto_history_exporter.exchanges.okx import OKXClient
        return OKXClient(config)
    else:
        raise ValueError(f"不支持的交易所: {exchange_name}")