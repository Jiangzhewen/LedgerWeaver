# LedgerWeaver · Crypto History Exporter

面向多交易所的数据“织造器”，用于高可靠地导出与统一加密交易所历史数据。支持成交、手续费、资金费、充值/提现等多类型数据，并提供统一的 Schema 与流式导出能力，便于后续清洗与分析。

![Python](https://img.shields.io/badge/Python-3.10%2B-blue) ![Status](https://img.shields.io/badge/Status-Active-success) ![OS](https://img.shields.io/badge/OS-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)

> 名称与仓库：本项目在仓库 `LedgerWeaver` 中实现 Crypto History Exporter 能力，以下文档已统一使用该仓库路径。

## 目录

- [功能特性](#功能特性)
- [安装](#安装)
- [配置](#配置)
- [使用方法](#使用方法)
  - [命令行](#命令行)
  - [Python API](#python-api)
- [支持的交易所](#支持的交易所)
- [导出格式](#导出格式)
- [开发](#开发)
- [运行测试](#运行测试)
- [安全性](#安全性)
- [常见错误](#常见错误)
- [许可证](#许可证)

## 功能特性

- 支持多个交易所（Binance Portfolio Margin、Hyperliquid、WhiteBIT、OKX 等）
- 覆盖多数据类型：成交、手续费、资金费、充值/提现、利息/借贷、爆仓、内部划转等
- 完整处理分页与时间切片，确保无遗漏记录
- 内置重试与节流，稳健应对限频与网络错误
- 统一 Schema 归一化，跨交易所数据可直接拼接分析
- 流式处理降低内存占用，适合长时间批量导出
- 支持增量拉取与 checkpoint 断点续传
- 可导出为标准 CSV 文件

## 安装

### 环境要求

- Python 3.10+

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/Jiangzhewen/LedgerWeaver.git
cd LedgerWeaver

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

## 配置

### API 密钥配置

在项目根目录创建 `config.yml`：

```yaml
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
  okx:
    enabled: true
    accounts:
      - name: main_spot_swap
        api_key: ${OKX_API_KEY}
        api_secret: ${OKX_API_SECRET}
        passphrase: ${OKX_PASSPHRASE}
        flag: 1      # 0: 模拟盘, 1: 实盘
```

设置环境变量：

```bash
export BINANCE_PM_API_KEY=your_binance_api_key
export BINANCE_PM_API_SECRET=your_binance_api_secret
export OKX_API_KEY=your_okx_api_key
export OKX_API_SECRET=your_okx_api_secret
export OKX_PASSPHRASE=your_okx_passphrase
```

## 使用方法

### 命令行

```bash
# 导出 Binance Portfolio Margin 子账户的交易历史
python -m crypto_history_exporter.cli \
  --exchange binance_pm \
  --data-types trades \
  --start 2024-01-01 --end 2024-12-31

# 导出多个交易所的多种数据类型
python -m crypto_history_exporter.cli \
  --exchange binance_pm okx \
  --data-types trades funding deposits \
  --start 2024-01-01 --end 2024-12-31

# 指定账户与输出目录
python -m crypto_history_exporter.cli \
  --exchange binance_pm \
  --accounts main_pm \
  --data-types trades \
  --start 2024-01-01 --end 2024-12-31 \
  --output-dir ./data

# 查看完整命令帮助
python -m crypto_history_exporter.cli --help
```

### Python API

```python
from crypto_history_exporter import get_exchange_client
from crypto_history_exporter.config import ConfigLoader

# 加载配置
config_loader = ConfigLoader('config.yml')
config = config_loader.get_exchange_config('binance_pm')

# 创建客户端
client = get_exchange_client('binance_pm', config)

# 获取数据（示例：按交易对过滤）
trades = client.fetch_trades('2024-01-01', '2024-12-31', symbols=['BTC/USDT'])

# 也可获取资金费、充值/提现等其它类型（接口因交易所而异）
```

## 支持的交易所

### 已支持

1. Binance Portfolio Margin 子账户
2. Hyperliquid（DEX）
3. WhiteBIT
4. OKX

### 计划支持

1. Kraken
2. HTX（原 Huobi）
3. Bybit
4. Crypto.com
5. Gate.io

## 导出格式

### CSV 格式

导出的 CSV 文件遵循以下规范：

- 编码：UTF-8
- 分隔符：逗号
- 小数：以字符串形式导出，保留原始精度
- 时间字段：
  - `timestamp`：整数毫秒
  - `datetime`：ISO8601 UTC（`YYYY-MM-DDTHH:MM:SS.sssZ`）
- 布尔字段统一使用 `true/false`

文件命名规范：

```
${exchange}_${account_name}_${data_type}_${startDate}_${endDate}.csv
```

例如：`binance_pm_main_pm_trades_2024-01-01_2024-12-31.csv`

目录结构：

```
${output_root}/${exchange}/${account_name}/${data_type}/
```

## 开发

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_config.py

# 运行测试并生成覆盖率报告
pytest --cov=crypto_history_exporter --cov-report=html
```

### 添加新的交易所支持

1. 在 `crypto_history_exporter/exchanges/` 目录下创建新的适配器文件
2. 继承 `ExchangeClient` 基类并实现所有抽象方法
3. 在 `get_exchange_client` 函数中添加新的交易所映射
4. 创建对应的测试文件
5. 更新 README.md 中的支持列表

## 版本兼容性

### 支持的 API 版本

- OKX V5 API
- Binance API v3
- Hyperliquid Python SDK（最新版本）
- WhiteBIT V4 API

### 第三方 SDK 验证版本

- hyperliquid-python-sdk：［版本范围］
- ccxt：［版本范围］

## 安全性

- 不在代码中硬编码任何 API 密钥
- 通过环境变量或配置文件读取密钥
- 日志不记录明文的 `api_key`、`api_secret`、`passphrase` 等敏感信息
- 请求日志对敏感字段进行脱敏处理

## 常见错误

### 限频错误

遇到 `429` 时会自动指数退避重试。如仍失败，请检查：

1. 配置文件中的限频参数是否合理
2. 是否同时运行了多个实例
3. 是否有其他程序在使用相同 API 密钥

### 时间范围错误

部分交易所对时间范围有限制（如 Binance 要求 `startTime` 与 `endTime` 间隔不超过 24 小时）。程序会自动进行时间切片，如仍遇到错误，请：

1. 检查时间范围是否符合限制
2. 查看日志中的详细错误信息

## 许可证

[待定]
