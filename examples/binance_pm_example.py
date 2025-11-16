"""
Binance Portfolio Margin 子账户示例脚本
"""
import os
import sys
from datetime import datetime, timezone

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from crypto_history_exporter.config import ConfigLoader
from crypto_history_exporter.exchanges.base import get_exchange_client
from crypto_history_exporter.exporters.csv_exporter import CSVExporter
from crypto_history_exporter.utils.time import parse_time


def main():
    """主函数"""
    print("Binance Portfolio Margin 子账户数据导出示例")
    print("=" * 50)
    
    # 创建示例配置文件
    config_content = """
global:
  retry_times: 3
  timeout: 30

exchanges:
  binance_pm:
    enabled: true
    accounts:
      - name: main_pm
        api_key: ${BINANCE_PM_API_KEY}
        api_secret: ${BINANCE_PM_API_SECRET}
        account_type: portfolio_margin
    rate_limit:
      max_requests_per_minute: 1100
      max_weight_per_minute: 5500
"""
    
    # 写入配置文件
    with open('config.yml', 'w', encoding='utf-8') as f:
        f.write(config_content.strip())
    
    print("已创建示例配置文件 config.yml")
    print("请设置环境变量 BINANCE_PM_API_KEY 和 BINANCE_PM_API_SECRET")
    print()
    
    # 检查环境变量
    api_key = os.environ.get('BINANCE_PM_API_KEY')
    api_secret = os.environ.get('BINANCE_PM_API_SECRET')
    
    if not api_key or not api_secret:
        print("警告: 未设置 BINANCE_PM_API_KEY 或 BINANCE_PM_API_SECRET 环境变量")
        print("请执行以下命令设置环境变量:")
        print("  export BINANCE_PM_API_KEY=your_api_key")
        print("  export BINANCE_PM_API_SECRET=your_api_secret")
        print()
        # return
    
    # 加载配置
    config_loader = ConfigLoader('config.yml')
    exchange_config = config_loader.get_exchange_config('binance_pm')
    
    # 创建交易所客户端
    client = get_exchange_client('binance_pm', exchange_config)
    
    # 设置时间范围（最近30天）
    end_time = datetime.now(timezone.utc)
    start_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
    start_time = start_time.replace(day=1)  # 本月第一天
    
    print(f"时间范围: {start_time} 到 {end_time}")
    print()
    
    # 初始化导出器
    exporter = CSVExporter('./output')
    
    # 获取账户列表
    accounts = exchange_config.accounts
    print(f"找到 {len(accounts)} 个账户:")
    for account in accounts:
        print(f"  - {account.name} ({account.account_type})")
    print()
    
    # 遍历账户获取数据
    for account in accounts:
        account_name = account.name
        print(f"处理账户: {account_name}")
        
        try:
            # 获取交易历史
            print("  获取交易历史...")
            trades = client.iter_trades(start_time, end_time)
            exporter.export_trades(trades, 'binance_pm', account_name, 
                                 start_time.strftime("%Y-%m-%d"), end_time.strftime("%Y-%m-%d"))
            print("  交易历史导出完成")
            
            # 获取资金费历史
            print("  获取资金费历史...")
            funding = client.iter_funding(start_time, end_time)
            exporter.export_funding(funding, 'binance_pm', account_name,
                                  start_time.strftime("%Y-%m-%d"), end_time.strftime("%Y-%m-%d"))
            print("  资金费历史导出完成")
            
            # 获取充值记录
            print("  获取充值记录...")
            deposits = client.iter_deposits(start_time, end_time)
            exporter.export_transfers(deposits, 'binance_pm', account_name, 'deposits',
                                    start_time.strftime("%Y-%m-%d"), end_time.strftime("%Y-%m-%d"))
            print("  充值记录导出完成")
            
            # 获取提现记录
            print("  获取提现记录...")
            withdrawals = client.iter_withdrawals(start_time, end_time)
            exporter.export_transfers(withdrawals, 'binance_pm', account_name, 'withdrawals',
                                    start_time.strftime("%Y-%m-%d"), end_time.strftime("%Y-%m-%d"))
            print("  提现记录导出完成")
            
            print(f"账户 {account_name} 数据导出完成")
            print()
            
        except Exception as e:
            print(f"账户 {account_name} 数据获取失败: {e}")
            print()
    
    print("所有账户数据导出完成!")
    print("导出文件位于 ./output 目录中")


if __name__ == "__main__":
    main()