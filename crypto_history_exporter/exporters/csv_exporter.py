"""
CSV导出器
"""
import csv
import os
from typing import List, Iterator
from decimal import Decimal
from datetime import datetime

from ..models import TradeRecord, FundingRecord, TransferRecord, FeeRecord


class CSVExporter:
    """CSV导出器"""
    
    def __init__(self, output_dir: str = "./output"):
        self.output_dir = output_dir
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
    
    def export_trades(self, trades: Iterator[TradeRecord], exchange: str, account_name: str, start_date: str, end_date: str):
        """导出交易记录到CSV"""
        filename = f"{exchange}_{account_name}_trades_{start_date}_{end_date}.csv"
        filepath = os.path.join(self.output_dir, exchange, account_name, "trades", filename)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'exchange', 'account_name', 'source', 'ingested_at',
                'symbol', 'side', 'order_type', 'price', 'amount', 'cost',
                'fee', 'fee_currency', 'trade_id', 'order_id',
                'timestamp', 'datetime', 'position_side', 'liquidity',
                'fee_rate', 'realized_pnl'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for trade in trades:
                writer.writerow({
                    'exchange': trade.exchange,
                    'account_name': trade.account_name,
                    'source': trade.source,
                    'ingested_at': trade.ingested_at.isoformat() if trade.ingested_at else '',
                    'symbol': trade.symbol,
                    'side': trade.side,
                    'order_type': trade.order_type,
                    'price': str(trade.price) if trade.price else '',
                    'amount': str(trade.amount) if trade.amount else '',
                    'cost': str(trade.cost) if trade.cost else '',
                    'fee': str(trade.fee) if trade.fee else '',
                    'fee_currency': trade.fee_currency,
                    'trade_id': trade.trade_id,
                    'order_id': trade.order_id,
                    'timestamp': trade.timestamp,
                    'datetime': trade.datetime,
                    'position_side': trade.position_side or '',
                    'liquidity': trade.liquidity or '',
                    'fee_rate': str(trade.fee_rate) if trade.fee_rate else '',
                    'realized_pnl': str(trade.realized_pnl) if trade.realized_pnl else '',
                })
    
    def export_funding(self, funding: Iterator[FundingRecord], exchange: str, account_name: str, start_date: str, end_date: str):
        """导出资金费记录到CSV"""
        filename = f"{exchange}_{account_name}_funding_{start_date}_{end_date}.csv"
        filepath = os.path.join(self.output_dir, exchange, account_name, "funding", filename)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'exchange', 'account_name', 'source', 'ingested_at',
                'symbol', 'funding_rate', 'funding_fee', 'position_size',
                'timestamp', 'datetime', 'settlement_period', 'funding_index', 'cycle'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for fund in funding:
                writer.writerow({
                    'exchange': fund.exchange,
                    'account_name': fund.account_name,
                    'source': fund.source,
                    'ingested_at': fund.ingested_at.isoformat() if fund.ingested_at else '',
                    'symbol': fund.symbol,
                    'funding_rate': str(fund.funding_rate) if fund.funding_rate else '',
                    'funding_fee': str(fund.funding_fee) if fund.funding_fee else '',
                    'position_size': str(fund.position_size) if fund.position_size else '',
                    'timestamp': fund.timestamp,
                    'datetime': fund.datetime,
                    'settlement_period': fund.settlement_period or '',
                    'funding_index': fund.funding_index or '',
                    'cycle': fund.cycle or ''
                })
    
    def export_transfers(self, transfers: Iterator[TransferRecord], exchange: str, account_name: str, transfer_type: str, start_date: str, end_date: str):
        """导出充提记录到CSV"""
        filename = f"{exchange}_{account_name}_{transfer_type}_{start_date}_{end_date}.csv"
        filepath = os.path.join(self.output_dir, exchange, account_name, "transfers", filename)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'exchange', 'account_name', 'source', 'ingested_at',
                'direction', 'currency', 'amount', 'network', 'address',
                'tx_hash', 'status', 'timestamp', 'datetime',
                'fee', 'fee_currency', 'internal_transfer', 'tag', 'memo'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for transfer in transfers:
                writer.writerow({
                    'exchange': transfer.exchange,
                    'account_name': transfer.account_name,
                    'source': transfer.source,
                    'ingested_at': transfer.ingested_at.isoformat() if transfer.ingested_at else '',
                    'direction': transfer.direction,
                    'currency': transfer.currency,
                    'amount': str(transfer.amount) if transfer.amount else '',
                    'network': transfer.network or '',
                    'address': transfer.address or '',
                    'tx_hash': transfer.tx_hash or '',
                    'status': transfer.status,
                    'timestamp': transfer.timestamp,
                    'datetime': transfer.datetime,
                    'fee': str(transfer.fee) if transfer.fee else '',
                    'fee_currency': transfer.fee_currency or '',
                    'internal_transfer': str(transfer.internal_transfer).lower() if transfer.internal_transfer is not None else '',
                    'tag': transfer.tag or '',
                    'memo': transfer.memo or ''
                })
    
    def export_fees(self, fees: Iterator[FeeRecord], exchange: str, account_name: str, start_date: str, end_date: str):
        """导出费用记录到CSV"""
        filename = f"{exchange}_{account_name}_fees_{start_date}_{end_date}.csv"
        filepath = os.path.join(self.output_dir, exchange, account_name, "fees", filename)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'exchange', 'account_name', 'source', 'ingested_at',
                'fee_type', 'currency', 'amount', 'trade_id', 'order_id',
                'funding_id', 'timestamp', 'datetime'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for fee in fees:
                writer.writerow({
                    'exchange': fee.exchange,
                    'account_name': fee.account_name,
                    'source': fee.source,
                    'ingested_at': fee.ingested_at.isoformat() if fee.ingested_at else '',
                    'fee_type': fee.fee_type,
                    'currency': fee.currency,
                    'amount': str(fee.amount) if fee.amount else '',
                    'trade_id': fee.trade_id or '',
                    'order_id': fee.order_id or '',
                    'funding_id': fee.funding_id or '',
                    'timestamp': fee.timestamp,
                    'datetime': fee.datetime
                })