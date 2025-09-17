# Ashare 数据插件使用指南

## 概述

Ashare 数据插件是基于 [mpquant/Ashare](https://github.com/mpquant/Ashare) 的股票数据获取插件，为 ASCEND 量化框架提供免费、开源的股票数据源支持。

## 特性

- ✅ **免费使用**: 无需 API token 或付费订阅
- ✅ **多频率支持**: 日线(1d)、周线(1w)、月线(1M)数据
- ✅ **实时数据**: 支持获取最新行情数据
- ✅ **自动复权**: 自动处理前复权数据
- ✅ **缓存机制**: 内置数据缓存，减少重复请求
- ✅ **兼容性**: 与现有 Tushare 插件接口完全兼容

## 安装依赖

Ashare 插件使用本地 Ashare.py 模块，无需额外安装：

```bash
# 项目已包含 Ashare.py，无需额外安装
```

## 配置使用

### 1. 在配置文件中使用 Ashare 数据源

```yaml
# quant_config.yaml
data_source:
  plugin: ashare_data  # 使用 Ashare 数据插件
  config:
    timeout: 30
    max_retries: 3
    cache_enabled: true
    cache_duration: 3600
```

### 2. 与 Tushare 对比使用

```yaml
# 使用 Tushare (需要 token)
data_source:
  plugin: tushare_data
  config:
    token: "your_tushare_token"
    timeout: 30

# 使用 Ashare (免费)
data_source:
  plugin: ashare_data
  config:
    timeout: 30
```

### 3. 代码中使用示例

```python
from quant_plugins.data_plugins import AshareDataPlugin, AshareDataPluginConfig

# 创建插件实例
plugin = AshareDataPlugin()

# 配置插件
config = AshareDataPluginConfig(
    timeout=30,
    max_retries=3,
    cache_enabled=True,
    cache_duration=3600
)

# 初始化和使用
plugin.configure(config.model_dump())
plugin.initialize()

# 获取股票数据
data = plugin.fetch_data(
    symbol='000001.XSHE',  # 平安银行
    start_date='2024-01-01',
    end_date='2024-12-31',
    data_type='daily',
    frequency='1d'
)

print(f"获取到 {len(data)} 条数据")
```

## 股票代码格式

Ashare 插件支持以下股票代码格式：

- **带交易所后缀**: `000001.XSHE` (深交所), `600000.XSHG` (上交所)
- **仅代码**: `000001` (自动识别交易所)
- **指数**: `000001.XSHG` (上证指数), `399001.XSHE` (深证成指)

## 支持的数据类型

- `daily` - 日线数据 (频率: '1d')
- `weekly` - 周线数据 (频率: '1w') 
- `monthly` - 月线数据 (频率: '1M')

## 性能特点

1. **网络请求**: Ashare 使用腾讯和新浪的公开接口，速度较快
2. **数据质量**: 提供前复权数据，适合量化分析
3. **稳定性**: 双数据源备份（腾讯+新浪），提高可靠性
4. **限制**: 无调用频率限制，适合高频测试

## 注意事项

1. **数据延迟**: 免费接口可能有15分钟延迟
2. **历史数据**: 支持获取较长历史数据
3. **错误处理**: 内置重试机制，网络异常自动重试
4. **缓存**: 默认启用缓存，相同请求1小时内不重复获取

## 故障排除

### 常见问题

1. **数据获取失败**: 检查网络连接，Ashare 需要访问腾讯和新浪接口
2. **符号格式错误**: 确保使用正确的股票代码格式
3. **日期范围无效**: 确保开始日期不晚于结束日期

### 调试模式

启用详细日志输出：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 与 Tushare 对比

| 特性 | Ashare | Tushare |
|------|--------|---------|
| 费用 | 免费 | 需要 token (可能收费) |
| 数据延迟 | 15分钟左右 | 实时(Pro版) |
| 接口稳定性 | 较高(双备份) | 高 |
| 数据完整性 | 良好 | 优秀 |
| 使用复杂度 | 简单 | 需要配置token |

## 版本历史

- v1.0.0 (2024-09-16): 初始版本发布
  - 支持日线、周线、月线数据
  - 实现完整 IDataSourcePlugin 接口
  - 内置缓存机制
  - 兼容现有量化框架

## 技术支持

如有问题，请参考：
- [Ashare GitHub](https://github.com/mpquant/Ashare)
- ASCEND 项目文档
- 在项目 Issues 中提问