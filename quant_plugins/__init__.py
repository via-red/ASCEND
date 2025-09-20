"""
ASCEND 量化插件包
基于 ASCEND 框架的金融量化工具插件集合

包含以下插件类型:
- 数据插件 (data_plugins): 数据获取、预处理和存储
- 策略插件 (strategy_plugins): 日K线评分策略和多因子模型
- 回测插件 (backtest_plugins): 回测引擎和性能评估
- 执行插件 (execution_plugins): 交易执行和实时监控
"""

from typing import Dict, List, Optional, Type
from pydantic import BaseModel

# 导出数据插件
from .data_plugins import (
    TushareDataPlugin,
    AshareDataPlugin,
    DataPreprocessingPlugin,
    WarehouseStoragePlugin,
    IDataSourcePlugin,
    IDataProcessorPlugin,
    IDataStoragePlugin
)

# 导出策略插件
from .strategy_plugins import (
    DailyKlineScoringPlugin,
    MultiFactorModelPlugin
)

# 导出回测插件
from .backtest_plugins import (
    DailyBacktestEnginePlugin,
)

# 导出执行插件
from .execution_plugins import (
    SimTraderPlugin,
    RealtimeMonitorPlugin
)


__all__ = [
    # 数据插件
    'TushareDataPlugin',
    'AshareDataPlugin',
    'DataPreprocessingPlugin',
    'WarehouseStoragePlugin',
    'IDataSourcePlugin',
    'IDataProcessorPlugin',
    'IDataStoragePlugin',
    
    # 策略插件
    'DailyKlineScoringPlugin',
    'MultiFactorModelPlugin',
    
    # 回测插件
    'DailyBacktestEnginePlugin',
    'PerformanceEvaluatorPlugin',
    
    # 执行插件
    'SimTraderPlugin',
    'RealtimeMonitorPlugin'
]

