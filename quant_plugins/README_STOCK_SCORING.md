# 策略评分选股工具

基于 ASCEND quant_plugins 的多因子评分模型对股票进行评分和筛选的工具。

## 🎯 功能特点

- **多因子评分**: 动量、成交量、波动率、趋势、RSI 五个因子综合评分
- **批量处理**: 支持多股票批量评分和筛选
- **灵活配置**: 可调整因子权重、评分阈值等参数
- **详细输出**: 显示每只股票的详细得分和交易信号
- **示例数据**: 内置示例数据生成功能，便于测试
- **真实数据**: 支持Tushare API获取真实股票数据
- **数据存储**: 使用warehouse存储插件避免重复拉取数据
- **指数成分股**: 自动获取和存储指数成分股名单

## 📦 安装依赖

```bash
pip install pandas numpy python-dotenv
```

**可选安装（使用真实数据时需要）**:
```bash
pip install tushare
```

## 🚀 快速开始

### 1. 使用示例数据运行

```bash
# 运行默认选股（使用示例数据）
python quant_plugins/run_stock_scoring.py

# 自定义参数运行
python quant_plugins/run_stock_scoring.py --min-score 65 --max-stocks 5

# 使用真实数据运行
python quant_plugins/run_stock_scoring.py --use-real-data --tushare-token YOUR_TOKEN --start-date 2024-01-01 --end-date 2024-12-31

# 指定数据存储路径
python quant_plugins/run_stock_scoring.py --use-real-data --tushare-token YOUR_TOKEN --storage-path ./my_data
```

### 2. 环境变量配置

创建 `.env` 文件来保护敏感信息：

```bash
# 复制示例文件
cp .env.example .env

# 编辑 .env 文件，填写实际值
# 注意：.env 文件应添加到 .gitignore 中
```

`.env` 文件内容示例：
```ini
# Tushare API Token (从 https://tushare.pro 获取)
TUSHARE_TOKEN=your_actual_tushare_token_here

# 日志级别配置
LOG_LEVEL=INFO
DEBUG_MODE=false
```

### 3. 使用真实数据

```bash
# 安装Tushare依赖
pip install tushare

# 使用真实数据运行（需要提供Tushare token）
python quant_plugins/run_stock_scoring.py \
    --use-real-data \
    --tushare-token YOUR_TUSHARE_TOKEN \
    --start-date 2024-01-01 \
    --end-date 2024-12-31 \
    --min-score 70 \
    --max-stocks 8
```

**数据缓存特性**:
- 自动检查本地存储，避免重复拉取相同数据
- 支持通过日期范围差异判断是否需要重新拉取
- 数据存储在本地warehouse中，支持多种格式

**Token安全**:
- 支持通过环境变量 `.env` 文件配置Tushare token
- 避免在命令行或代码中硬编码敏感信息
- 多种配置方式优先级：命令行参数 > 环境变量 > 配置文件

## 📊 评分因子说明

| 因子 | 权重 | 说明 |
|------|------|------|
| 动量因子 | 35% | 价格变化率，反映短期和长期动量 |
| 成交量因子 | 15% | 成交量相对强度，反映市场活跃度 |
| 波动率因子 | 15% | 历史波动率，低波动率得分高 |
| 趋势因子 | 25% | 移动平均线趋势强度 |
| RSI相对强弱 | 10% | RSI指标，50-70区间最佳 |

## ⚙️ 配置参数

### 命令行参数

```bash
--symbols         股票代码列表（默认包含12只沪深股票）
--min-score       最低评分阈值（默认65，0-100分范围）
--max-stocks      最大股票数量（默认10）
--output          结果输出文件
--use-real-data   使用真实数据（需要配置Tushare token）
--tushare-token   Tushare API token
--start-date      数据开始日期（YYYY-MM-DD）
--end-date        数据结束日期（YYYY-MM-DD）
--storage-path    数据存储路径（默认./data/warehouse）
--config          JSON配置文件路径
--use-real-data   使用真实数据
--tushare-token   Tushare API token（可选，优先使用环境变量）
--start-date      数据开始日期（YYYY-MM-DD）
--end-date        数据结束日期（YYYY-MM-DD）
```

### 配置文件

#### 1. 代码配置

可以在代码中修改默认配置：

```python
config = {
    'factor_weights': {
        'momentum': 0.35,
        'volume': 0.15,
        'volatility': 0.15,
        'trend': 0.25,
        'rsi_strength': 0.10
    },
    'scoring_threshold': 65.0,  # 0-100分范围
    'min_data_points': 20,
    'tushare_token': '',        # Tushare API token
    'storage_path': './data/warehouse',  # 数据存储路径
    'index_constituents': {     # 指数成分股配置
        '000300.SH': '沪深300',
        '000905.SH': '中证500',
        '000852.SH': '中证1000'
    }
}
```

#### 2. JSON配置文件

支持通过JSON文件进行配置：

```json
{
  "scoring_threshold": 70.0,
  "tushare_token": "your_tushare_token_here",
  "storage_path": "./data/warehouse",
  "factor_weights": {
    "momentum": 0.35,
    "volume": 0.15,
    "volatility": 0.15,
    "trend": 0.25,
    "rsi_strength": 0.10
  },
  "index_constituents": {
    "000300.SH": "沪深300",
    "000905.SH": "中证500",
    "000852.SH": "中证1000"
  }
}
```

使用配置文件运行：

```bash
python quant_plugins/run_stock_scoring.py --config quant_plugins/config/stock_scoring_config.json
```

配置文件优先级高于命令行参数。

## 📋 输出说明

### 评分结果格式

```json
{
  "selected_stocks": [
    {
      "symbol": "601288.SH",
      "total_score": 65.1,  # 0-100分范围
      "factor_scores": {
        "momentum": 0.238,
        "volume": 0.077,
        "volatility": 0.089,
        "trend": 0.174,
        "rsi_strength": 0.073
      },
      "signal": "BUY"
    }
  ],
  "all_scores": {
    "601288.SH": {
      "total_score": 65.1,  # 0-100分范围
      "signal": "BUY"
    }
  }
}
```

### 交易信号说明

- **BUY**: 评分 >= 阈值（默认65分），建议买入
- **HOLD**: 评分接近阈值（阈值*0.8），建议持有
- **SELL**: 评分低于阈值，建议卖出

**评分范围**: 0-100分（原为0-1分）

## 🧪 测试验证

### 运行测试

```bash
# 运行直接测试
python quant_plugins/direct_scoring_test.py

# 运行完整测试
python quant_plugins/test_stock_scoring.py
```

### 测试结果

测试脚本会：
1. 生成示例股票数据
2. 对多只股票进行评分
3. 筛选符合条件的股票
4. 输出详细的评分结果

## 🔧 扩展开发

### 添加新的评分因子

1. 在 `DailyKlineScoringPlugin` 中添加因子计算方法
2. 更新因子权重配置
3. 修改标准化逻辑（如果需要）

### 集成真实数据源

已集成Tushare数据源，支持：
1. 自动数据获取和缓存
2. 避免重复拉取相同数据
3. 指数成分股自动存储
4. 数据持久化到本地warehouse

### 数据存储功能

使用warehouse存储插件提供：
1. 多种存储格式支持（parquet, csv, pickle, feather）
2. 数据压缩和索引
3. 自动清理和版本管理
4. 避免重复拉取相同时间段的数据

## 📝 使用示例

### 基本使用

```python
from quant_plugins.strategy_plugins.daily_kline_scoring_plugin import DailyKlineScoringPlugin

# 创建评分插件
scorer = DailyKlineScoringPlugin()
scorer.configure(config)
scorer.initialize()

# 对单只股票评分
result = scorer.execute(stock_data)
score = result['scores']['total_score']
signal = result['signals']['signal']
```

### 批量评分

```python
# 对多只股票批量评分
results = {}
for symbol, data in stock_data.items():
    result = scorer.execute(data)
    results[symbol] = {
        'score': result['scores']['total_score'],
        'signal': result['signals']['signal']
    }
```

## 🎯 性能优化建议

1. **数据缓存**: 对重复使用的数据进行缓存
2. **并行处理**: 对多股票评分使用多线程/多进程
3. **增量更新**: 只对发生变化的数据重新评分
4. **结果持久化**: 将评分结果保存到数据库

## 📞 技术支持

如遇问题请检查：
1. 依赖包是否安装完整
2. 数据格式是否正确
3. 配置参数是否合理

## 📄 许可证

Apache 2.0 License