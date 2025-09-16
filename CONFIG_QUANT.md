# 量化工具配置文件设计

## 📋 配置文件结构

### 主配置文件 (`quant_config.yaml`)

```yaml
# 框架配置
version: "1.0.0"
framework: "ascend"
project: "quant_trading_system"
description: "基于ASCEND框架的日K线量化交易系统"

# 插件配置
plugins:
  - "tushare_data"
  - "mysql_storage" 
  - "data_preprocessor"
  - "daily_kline_scoring"
  - "daily_backtest_engine"
  - "sim_trader"
  - "realtime_monitor"

# 数据源配置
data_sources:
  tushare:
    enabled: true
    token: "${TUSHARE_TOKEN}"  # 从环境变量读取
    symbols_file: "./config/symbols.txt"
    start_date: "2023-01-01"
    end_date: "2023-12-31"
    fields:
      - "ts_code"
      - "trade_date" 
      - "open"
      - "high"
      - "low"
      - "close"
      - "vol"
      - "amount"
      - "pct_chg"

# 数据存储配置
data_storage:
  mysql:
    enabled: true
    host: "localhost"
    port: 3306
    database: "quant_data"
    username: "quant_user"
    password: "${DB_PASSWORD}"
    tables:
      daily: "stock_daily"
      fundamentals: "stock_fundamentals"
      trades: "trade_records"
  
  parquet:
    enabled: false
    path: "./data/parquet/"
    compression: "snappy"

# 策略配置
strategy:
  name: "daily_kline_scoring"
  type: "scoring"
  enabled: true
  
  # 因子权重配置
  factor_weights:
    momentum: 0.35
    volume: 0.15  
    volatility: 0.15
    trend: 0.25
    rsi_strength: 0.10
  
  # 评分阈值
  scoring_threshold: 0.65
  sell_threshold: 0.30
  min_data_days: 30
  
  # 技术参数
  technical_parameters:
    momentum_periods: [5, 20]
    volume_lookback: 20
    volatility_period: 20
    rsi_period: 14
    ma_periods: [5, 20, 60]

# 回测配置
backtest:
  initial_capital: 1000000.0
  commission_rate: 0.0003
  slippage_rate: 0.0001
  min_trade_amount: 100.0
  max_position_per_stock: 0.2
  stop_loss: -0.1
  take_profit: 0.2
  
  # 回测周期
  test_periods:
    - name: "full_period"
      start_date: "2023-01-01"
      end_date: "2023-12-31"
    - name: "first_half" 
      start_date: "2023-01-01"
      end_date: "2023-06-30"
    - name: "second_half"
      start_date: "2023-07-01"
      end_date: "2023-12-31"

# 交易执行配置
execution:
  mode: "simulation"  # simulation / paper_trading / live_trading
  sim_trader:
    trade_time: "14:55:00"
    order_validity: "day"
    min_trade_volume: 100
  
  # 实盘交易配置（预留）
  live_trading:
    broker: "none"
    account_id: ""
    api_key: "${BROKER_API_KEY}"
    secret_key: "${BROKER_SECRET_KEY}"

# 监控配置
monitoring:
  enabled: true
  alert_rules:
    max_drawdown: -0.15
    position_concentration: 0.3
    trade_frequency: 20
    connection_timeout: 60
  
  # 报警通知
  notifications:
    email:
      enabled: false
      smtp_server: "smtp.example.com"
      sender: "quant@example.com"
      receivers: ["admin@example.com"]
    slack:
      enabled: false
      webhook_url: "${SLACK_WEBHOOK}"
    wechat:
      enabled: false
      app_id: "${WECHAT_APP_ID}"
      app_secret: "${WECHAT_SECRET}"

# 日志配置
logging:
  level: "INFO"
  file_path: "./logs/quant_trading.log"
  max_file_size: 10485760  # 10MB
  backup_count: 5
  console_output: true

# 性能优化配置
performance:
  data_cache: true
  cache_dir: "./cache/"
  max_cache_size: 1073741824  # 1GB
  parallel_processing: true
  max_workers: 4

# 环境变量配置
env_vars:
  TUSHARE_TOKEN: "required"
  DB_PASSWORD: "required"
  BROKER_API_KEY: "optional"
  BROKER_SECRET_KEY: "optional"
  SLACK_WEBHOOK: "optional"
  WECHAT_APP_ID: "optional"
  WECHAT_SECRET: "optional"
```

### 股票列表文件 (`symbols.txt`)

```
# 沪深300成分股示例
000001.SZ  # 平安银行
000002.SZ  # 万科A
000063.SZ  # 中兴通讯
000066.SZ  # 中国长城
000333.SZ  # 美的集团
000338.SZ  # 潍柴动力
000568.SZ  # 泸州老窖
000625.SZ  # 长安汽车
000651.SZ  # 格力电器
000725.SZ  # 京东方A
000858.SZ  # 五粮液
000876.SZ  # 新希望
000895.SZ  # 双汇发展
000938.SZ  # 紫光股份
000977.SZ  # 浪潮信息
002007.SZ  # 华兰生物
002008.SZ  # 大族激光
002024.SZ  # 苏宁易购
002027.SZ  # 分众传媒
002032.SZ  # 苏泊尔

# 创业板示例
300001.SZ  # 特锐德
300002.SZ  # 神州泰岳
300003.SZ  # 乐普医疗
300015.SZ  # 爱尔眼科
300017.SZ  # 网宿科技
300024.SZ  # 机器人
300033.SZ  # 同花顺
300059.SZ  # 东方财富
300122.SZ  # 智飞生物
300124.SZ  # 汇川技术

# 上证示例
600000.SH  # 浦发银行
600009.SH  # 上海机场
600010.SH  # 包钢股份
600016.SH  # 民生银行
600028.SH  # 中国石化
600030.SH  # 中信证券
600036.SH  # 招商银行
600048.SH  # 保利发展
600050.SH  # 中国联通
600104.SH  # 上汽集团
```

### 环境变量文件 (`.env`)

```bash
# Tushare数据源配置
TUSHARE_TOKEN=your_tushare_token_here

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_NAME=quant_data
DB_USER=quant_user
DB_PASSWORD=your_db_password_here

# 监控通知配置（可选）
SLACK_WEBHOOK=https://hooks.slack.com/services/xxx
WECHAT_APP_ID=your_wechat_app_id
WECHAT_SECRET=your_wechat_secret

# 交易API配置（预留）
BROKER_API_KEY=your_broker_api_key
BROKER_SECRET_KEY=your_broker_secret_key
```

## 🔧 配置加载机制

### 配置优先级
1. 环境变量 (最高优先级)
2. 配置文件参数
3. 默认值 (最低优先级)

### 配置验证规则
```yaml
validation_rules:
  data_sources.tushare.token: 
    required: true
    type: string
    min_length: 32
  
  backtest.initial_capital:
    required: true  
    type: number
    min: 10000
    max: 100000000
  
  strategy.scoring_threshold:
    required: true
    type: number
    min: 0.1
    max: 0.9
  
  execution.mode:
    required: true
    type: string
    allowed: ["simulation", "paper_trading", "live_trading"]
```

## 🎯 配置使用示例

### 基本使用
```python
from ascend import load_config, validate_config

# 加载配置
config = load_config("config/quant_config.yaml")

# 验证配置
is_valid = validate_config(config)
if not is_valid:
    raise ValueError("配置验证失败")

# 使用配置初始化插件
from ascend import load_plugins
plugins = load_plugins(config['plugins'], config)
```

### 环境变量覆盖
```bash
# 启动时覆盖配置
export TUSHARE_TOKEN="new_token_123"
export DB_PASSWORD="new_password_456"
python quant_main.py
```

### 多环境配置
```yaml
# 开发环境
environment: "development"
logging:
  level: "DEBUG"
  
# 生产环境  
environment: "production"
logging:
  level: "INFO"
  file_path: "/var/log/quant_trading.log"
```

这个配置文件设计提供了完整的量化系统配置方案，支持灵活的插件配置、多环境部署和安全的敏感信息管理。