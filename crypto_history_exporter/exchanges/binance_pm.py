"""
Binance Portfolio Margin 子账户适配器
"""
import hashlib
import hmac
import time
import urllib.parse
from typing import List, Iterator, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from .base import ExchangeClient
from ..config import ExchangeConfig, AccountConfig
from ..models import TradeRecord, FundingRecord, TransferRecord, FeeRecord
from ..utils.time import parse_time, to_timestamp_ms, from_timestamp_ms, format_iso8601
from ..utils.http import HTTPClient, generate_signature, redact_sensitive_data
from ..utils.pagination import PaginationHelper, PaginationResult

logger = logging.getLogger(__name__)


class BinancePMClient(ExchangeClient):
    """Binance Portfolio Margin 子账户客户端"""
    
    def __init__(self, config: ExchangeConfig):
        super().__init__(config)
        self.base_url = "https://papi.binance.com"
        self.http_client = HTTPClient()
        
        # 初始化账户HTTP客户端
        self.account_clients = {}
        for account in self.config.accounts:
            self.account_clients[account.name] = HTTPClient(
                timeout=30,
                retry_times=3
            )
    
    def _generate_signature(self, secret: str, params: dict) -> str:
        """生成签名"""
        query_string = urllib.parse.urlencode(params)
        return hmac.new(secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    
    def _make_request(self, account: AccountConfig, method: str, endpoint: str, params: Optional[dict] = None, sign: bool = True) -> dict:
        """发起API请求"""
        url = f"{self.base_url}{endpoint}"
        headers = {
            'X-MBX-APIKEY': account.api_key
        }
        
        if params is None:
            params = {}
        
        # 添加时间戳
        params['timestamp'] = int(time.time() * 1000)
        
        # 生成签名
        if sign:
            params['signature'] = self._generate_signature(account.api_secret, params)
        
        # 脱敏日志
        safe_params = redact_sensitive_data(params)
        logger.debug(f"发起请求: {method} {url} params={safe_params}")
        
        try:
            if method == 'GET':
                response = self.account_clients[account.name].get(url, params=params, headers=headers)
            else:
                response = self.account_clients[account.name].post(url, data=params, headers=headers)
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"请求失败: {e}")
            raise
    
    def fetch_trades(self, start_time: datetime, end_time: datetime, symbols: Optional[List[str]] = None) -> List[TradeRecord]:
        """获取交易历史"""
        all_trades = []
        for account in self.config.accounts:
            trades = list(self.iter_trades(start_time, end_time, symbols, account))
            all_trades.extend(trades)
        return all_trades
    
    def iter_trades(self, start_time: datetime, end_time: datetime, symbols: Optional[List[str]] = None, account: Optional[AccountConfig] = None) -> Iterator[TradeRecord]:
        """流式获取交易历史"""
        accounts = [account] if account else self.config.accounts
        
        for acc in accounts:
            # Binance Portfolio Margin API限制每次请求最大24小时
            time_windows = self._generate_time_windows(start_time, end_time, timedelta(hours=24))
            
            for window_start, window_end in time_windows:
                page = 1
                while True:
                    params = {
                        'startTime': to_timestamp_ms(window_start),
                        'endTime': to_timestamp_ms(window_end),
                        'page': page,
                        'limit': 100
                    }
                    
                    if symbols:
                        # Binance Portfolio Margin API可能不支持直接筛选symbol，需要在客户端过滤
                        pass
                    
                    try:
                        response = self._make_request(acc, 'GET', '/papi/v1/pm/trade', params)
                        
                        if not response.get('data'):
                            break
                        
                        trades = response['data']
                        for trade in trades:
                            # 转换为统一格式
                            record = self._convert_trade(trade, acc.name)
                            # 如果指定了symbols，进行过滤
                            if symbols is None or record.symbol in symbols:
                                yield record
                        
                        # 如果返回记录数小于限制，说明已经是最后一页
                        if len(trades) < 100:
                            break
                            
                        page += 1
                        
                    except Exception as e:
                        logger.error(f"获取交易历史失败: {e}")
                        break
    
    def _convert_trade(self, trade: dict, account_name: str) -> TradeRecord:
        """转换交易记录为统一格式"""
        timestamp = trade['time']
        dt = from_timestamp_ms(timestamp)
        
        return TradeRecord(
            exchange='binance_pm',
            account_name=account_name,
            source='rest',
            ingested_at=datetime.utcnow(),
            symbol=trade['symbol'],
            side=trade['side'].lower(),
            order_type=trade['type'].lower(),
            price=Decimal(str(trade['price'])),
            amount=Decimal(str(trade['qty'])),
            cost=Decimal(str(float(trade['price']) * float(trade['qty']))),
            fee=Decimal(str(trade['commission'])),
            fee_currency=trade['commissionAsset'],
            trade_id=str(trade['id']),
            order_id=str(trade['orderId']),
            timestamp=timestamp,
            datetime=format_iso8601(dt),
            raw=trade
        )
    
    def fetch_funding(self, start_time: datetime, end_time: datetime, symbols: Optional[List[str]] = None) -> List[FundingRecord]:
        """获取资金费历史"""
        all_funding = []
        for account in self.config.accounts:
            funding = list(self.iter_funding(start_time, end_time, symbols, account))
            all_funding.extend(funding)
        return all_funding
    
    def iter_funding(self, start_time: datetime, end_time: datetime, symbols: Optional[List[str]] = None, account: Optional[AccountConfig] = None) -> Iterator[FundingRecord]:
        """流式获取资金费历史"""
        accounts = [account] if account else self.config.accounts
        
        for acc in accounts:
            # Binance Portfolio Margin API限制每次请求最大24小时
            time_windows = self._generate_time_windows(start_time, end_time, timedelta(hours=24))
            
            for window_start, window_end in time_windows:
                page = 1
                while True:
                    params = {
                        'startTime': to_timestamp_ms(window_start),
                        'endTime': to_timestamp_ms(window_end),
                        'page': page,
                        'limit': 100
                    }
                    
                    try:
                        response = self._make_request(acc, 'GET', '/papi/v1/pm/funding', params)
                        
                        if not response.get('data'):
                            break
                        
                        fundings = response['data']
                        for funding in fundings:
                            # 转换为统一格式
                            record = self._convert_funding(funding, acc.name)
                            # 如果指定了symbols，进行过滤
                            if symbols is None or record.symbol in symbols:
                                yield record
                        
                        # 如果返回记录数小于限制，说明已经是最后一页
                        if len(fundings) < 100:
                            break
                            
                        page += 1
                        
                    except Exception as e:
                        logger.error(f"获取资金费历史失败: {e}")
                        break
    
    def _convert_funding(self, funding: dict, account_name: str) -> FundingRecord:
        """转换资金费记录为统一格式"""
        timestamp = funding['time']
        dt = from_timestamp_ms(timestamp)
        
        return FundingRecord(
            exchange='binance_pm',
            account_name=account_name,
            source='rest',
            ingested_at=datetime.utcnow(),
            symbol=funding['symbol'],
            funding_rate=Decimal(str(funding.get('fundingRate'))) if funding.get('fundingRate') else None,
            funding_fee=Decimal(str(funding['fee'])),
            position_size=Decimal(str(funding.get('positionSize'))) if funding.get('positionSize') else None,
            timestamp=timestamp,
            datetime=format_iso8601(dt),
            raw=funding
        )
    
    def fetch_deposits(self, start_time: datetime, end_time: datetime) -> List[TransferRecord]:
        """获取充值记录"""
        all_deposits = []
        for account in self.config.accounts:
            deposits = list(self.iter_deposits(start_time, end_time, account))
            all_deposits.extend(deposits)
        return all_deposits
    
    def iter_deposits(self, start_time: datetime, end_time: datetime, account: Optional[AccountConfig] = None) -> Iterator[TransferRecord]:
        """流式获取充值记录"""
        accounts = [account] if account else self.config.accounts
        
        for acc in accounts:
            # 使用SAPI接口获取充值记录
            page = 1
            while True:
                params = {
                    'startTime': to_timestamp_ms(start_time),
                    'endTime': to_timestamp_ms(end_time),
                    'page': page,
                    'limit': 100
                }
                
                try:
                    # 需要切换到SAPI端点
                    sapi_client = HTTPClient()
                    headers = {'X-MBX-APIKEY': acc.api_key}
                    params['timestamp'] = int(time.time() * 1000)
                    params['signature'] = self._generate_signature(acc.api_secret, params)
                    
                    response = sapi_client.get('https://api.binance.com/sapi/v1/capital/deposit/hisrec', 
                                             params=params, headers=headers)
                    response.raise_for_status()
                    deposits = response.json()
                    
                    if not deposits:
                        break
                    
                    for deposit in deposits:
                        # 转换为统一格式
                        record = self._convert_deposit(deposit, acc.name)
                        yield record
                    
                    # 如果返回记录数小于限制，说明已经是最后一页
                    if len(deposits) < 100:
                        break
                        
                    page += 1
                    
                except Exception as e:
                    logger.error(f"获取充值记录失败: {e}")
                    break
    
    def _convert_deposit(self, deposit: dict, account_name: str) -> TransferRecord:
        """转换充值记录为统一格式"""
        timestamp = deposit['insertTime']
        dt = from_timestamp_ms(timestamp)
        
        # 状态映射
        status_map = {
            0: 'pending',
            1: 'success',
            6: 'failed'
        }
        
        return TransferRecord(
            exchange='binance_pm',
            account_name=account_name,
            source='rest',
            ingested_at=datetime.utcnow(),
            direction='deposit',
            currency=deposit['coin'],
            amount=Decimal(str(deposit['amount'])),
            network=deposit.get('network'),
            address=deposit.get('address'),
            tx_hash=deposit.get('txId'),
            status=status_map.get(deposit['status'], 'unknown'),
            timestamp=timestamp,
            datetime=format_iso8601(dt),
            raw=deposit
        )
    
    def fetch_withdrawals(self, start_time: datetime, end_time: datetime) -> List[TransferRecord]:
        """获取提现记录"""
        all_withdrawals = []
        for account in self.config.accounts:
            withdrawals = list(self.iter_withdrawals(start_time, end_time, account))
            all_withdrawals.extend(withdrawals)
        return all_withdrawals
    
    def iter_withdrawals(self, start_time: datetime, end_time: datetime, account: Optional[AccountConfig] = None) -> Iterator[TransferRecord]:
        """流式获取提现记录"""
        accounts = [account] if account else self.config.accounts
        
        for acc in accounts:
            # 使用SAPI接口获取提现记录
            page = 1
            while True:
                params = {
                    'startTime': to_timestamp_ms(start_time),
                    'endTime': to_timestamp_ms(end_time),
                    'page': page,
                    'limit': 100
                }
                
                try:
                    # 需要切换到SAPI端点
                    sapi_client = HTTPClient()
                    headers = {'X-MBX-APIKEY': acc.api_key}
                    params['timestamp'] = int(time.time() * 1000)
                    params['signature'] = self._generate_signature(acc.api_secret, params)
                    
                    response = sapi_client.get('https://api.binance.com/sapi/v1/capital/withdraw/history', 
                                             params=params, headers=headers)
                    response.raise_for_status()
                    withdrawals = response.json()
                    
                    if not withdrawals:
                        break
                    
                    for withdrawal in withdrawals:
                        # 转换为统一格式
                        record = self._convert_withdrawal(withdrawal, acc.name)
                        yield record
                    
                    # 如果返回记录数小于限制，说明已经是最后一页
                    if len(withdrawals) < 100:
                        break
                        
                    page += 1
                    
                except Exception as e:
                    logger.error(f"获取提现记录失败: {e}")
                    break
    
    def _convert_withdrawal(self, withdrawal: dict, account_name: str) -> TransferRecord:
        """转换提现记录为统一格式"""
        timestamp = withdrawal['applyTime']
        # Binance的applyTime是字符串格式，需要特殊处理
        try:
            dt = datetime.strptime(withdrawal['applyTime'], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            dt = datetime.utcnow()
        
        # 状态映射
        status_map = {
            0: 'pending',  # Email Sent
            1: 'pending',  # Cancelled
            2: 'pending',  # Awaiting Approval
            3: 'pending',  # Rejected
            4: 'pending',  # Processing
            5: 'pending',  # Failure
            6: 'success'   # Completed
        }
        
        return TransferRecord(
            exchange='binance_pm',
            account_name=account_name,
            source='rest',
            ingested_at=datetime.utcnow(),
            direction='withdrawal',
            currency=withdrawal['coin'],
            amount=Decimal(str(withdrawal['amount'])),
            network=withdrawal.get('network'),
            address=withdrawal.get('address'),
            tx_hash=withdrawal.get('txId'),
            status=status_map.get(withdrawal['status'], 'unknown'),
            timestamp=int(dt.timestamp() * 1000),
            datetime=format_iso8601(dt),
            fee=Decimal(str(withdrawal.get('transactionFee'))) if withdrawal.get('transactionFee') else None,
            fee_currency=withdrawal['coin'],
            raw=withdrawal
        )
    
    def _generate_time_windows(self, start_time: datetime, end_time: datetime, window_size: timedelta) -> List[tuple]:
        """生成时间窗口"""
        windows = []
        current_start = start_time
        while current_start < end_time:
            current_end = min(current_start + window_size, end_time)
            windows.append((current_start, current_end))
            current_start = current_end
        return windows