"""
命令行接口
"""
import argparse
import sys
import os
import logging
from datetime import datetime
from typing import List, Dict

from .config import ConfigLoader
from .exchanges.base import get_exchange_client
from .exporters.csv_exporter import CSVExporter
from .utils.time import parse_time, format_iso8601


def setup_logging(debug: bool = False):
    """设置日志"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Crypto History Exporter - 交易所历史数据导出工具')
    parser.add_argument('--exchange', '-e', nargs='+', required=True, 
                        help='一个或多个交易所标识（如 binance_pm,okx）')
    parser.add_argument('--accounts', nargs='+', 
                        help='可选，只拉取指定账号名列表')
    parser.add_argument('--data-types', nargs='+', required=True,
                        choices=['trades', 'funding', 'deposits', 'withdrawals', 'interest', 'earn_interest', 'liquidation', 'rebate'],
                        help='数据类型')
    parser.add_argument('--start', required=True, help='开始时间，支持 ISO8601 字符串')
    parser.add_argument('--end', required=True, help='结束时间，支持 ISO8601 字符串')
    parser.add_argument('--output-dir', default='./output', help='导出根目录')
    parser.add_argument('--format', choices=['csv'], default='csv', help='导出格式')
    parser.add_argument('--checkpoint', action='store_true', help='是否使用及更新 checkpoint')
    parser.add_argument('--debug', action='store_true', help='打开 DEBUG 日志')
    parser.add_argument('--config', default='config.yml', help='配置文件路径')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    # 解析时间
    try:
        start_time = parse_time(args.start)
        end_time = parse_time(args.end)
    except Exception as e:
        logger.error(f"时间解析失败: {e}")
        sys.exit(1)
    
    # 格式化日期用于文件名
    start_date = start_time.strftime("%Y-%m-%d")
    end_date = end_time.strftime("%Y-%m-%d")
    
    # 加载配置
    try:
        config_loader = ConfigLoader(args.config)
        global_config = config_loader.get_global_config()
    except Exception as e:
        logger.error(f"配置加载失败: {e}")
        sys.exit(1)
    
    # 初始化导出器
    exporter = CSVExporter(args.output_dir)
    
    # 记录成功和失败的交易所
    success_exchanges = []
    failed_exchanges = []
    
    # 遍历交易所
    for exchange_name in args.exchange:
        try:
            logger.info(f"开始处理交易所: {exchange_name}")
            
            # 获取交易所配置
            try:
                exchange_config = config_loader.get_exchange_config(exchange_name)
                if not exchange_config.enabled:
                    logger.info(f"交易所 {exchange_name} 未启用，跳过")
                    continue
            except Exception as e:
                logger.error(f"获取交易所 {exchange_name} 配置失败: {e}")
                failed_exchanges.append((exchange_name, "config", str(e)))
                continue
            
            # 获取交易所客户端
            try:
                client = get_exchange_client(exchange_name, exchange_config)
            except Exception as e:
                logger.error(f"创建交易所 {exchange_name} 客户端失败: {e}")
                failed_exchanges.append((exchange_name, "client", str(e)))
                continue
            
            # 筛选账户
            accounts = exchange_config.accounts
            if args.accounts:
                accounts = [acc for acc in accounts if acc.name in args.accounts]
                if not accounts:
                    logger.warning(f"交易所 {exchange_name} 没有匹配的账户，跳过")
                    continue
            
            # 遍历账户
            for account in accounts:
                account_name = account.name
                logger.info(f"处理账户: {account_name}")
                
                # 获取数据
                try:
                    if 'trades' in args.data_types:
                        logger.info(f"获取交易历史: {account_name}")
                        trades = client.iter_trades(start_time, end_time)
                        exporter.export_trades(trades, exchange_name, account_name, start_date, end_date)
                    
                    if 'funding' in args.data_types:
                        logger.info(f"获取资金费历史: {account_name}")
                        funding = client.iter_funding(start_time, end_time)
                        exporter.export_funding(funding, exchange_name, account_name, start_date, end_date)
                    
                    if 'deposits' in args.data_types:
                        logger.info(f"获取充值记录: {account_name}")
                        deposits = client.iter_deposits(start_time, end_time)
                        exporter.export_transfers(deposits, exchange_name, account_name, 'deposits', start_date, end_date)
                    
                    if 'withdrawals' in args.data_types:
                        logger.info(f"获取提现记录: {account_name}")
                        withdrawals = client.iter_withdrawals(start_time, end_time)
                        exporter.export_transfers(withdrawals, exchange_name, account_name, 'withdrawals', start_date, end_date)
                    
                    # 扩展类型
                    if 'interest' in args.data_types:
                        logger.info(f"获取利息记录: {account_name}")
                        interest = client.fetch_interest(start_time, end_time)
                        # 注意：这里需要转换为迭代器
                        exporter.export_fees(iter(interest), exchange_name, account_name, start_date, end_date)
                    
                    if 'earn_interest' in args.data_types:
                        logger.info(f"获取理财利息记录: {account_name}")
                        earn_interest = client.fetch_earn_interest(start_time, end_time)
                        exporter.export_fees(iter(earn_interest), exchange_name, account_name, start_date, end_date)
                    
                    if 'liquidation' in args.data_types:
                        logger.info(f"获取清算记录: {account_name}")
                        liquidation = client.fetch_liquidation(start_time, end_time)
                        exporter.export_fees(iter(liquidation), exchange_name, account_name, start_date, end_date)
                    
                    if 'rebate' in args.data_types:
                        logger.info(f"获取返佣记录: {account_name}")
                        rebate = client.fetch_rebate(start_time, end_time)
                        exporter.export_fees(iter(rebate), exchange_name, account_name, start_date, end_date)
                    
                    success_exchanges.append((exchange_name, account_name))
                    logger.info(f"账户 {account_name} 数据导出完成")
                    
                except Exception as e:
                    logger.error(f"账户 {account_name} 数据获取失败: {e}")
                    failed_exchanges.append((exchange_name, account_name, str(e)))
        
        except Exception as e:
            logger.error(f"处理交易所 {exchange_name} 失败: {e}")
            failed_exchanges.append((exchange_name, "general", str(e)))
    
    # 输出结果
    print("\n" + "="*50)
    print("执行结果:")
    print("="*50)
    
    if success_exchanges:
        print("成功:")
        for exchange, account in success_exchanges:
            print(f"  - {exchange}::{account}")
    
    if failed_exchanges:
        print("失败:")
        for exchange, account, error in failed_exchanges:
            print(f"  - {exchange}::{account}: {error}")
    
    # 退出码
    if failed_exchanges and not success_exchanges:
        # 全部失败
        sys.exit(2)
    elif failed_exchanges:
        # 部分失败
        sys.exit(1)
    else:
        # 全部成功
        sys.exit(0)


if __name__ == "__main__":
    main()