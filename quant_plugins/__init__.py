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
    PerformanceEvaluatorPlugin
)

# 导出执行插件
from .execution_plugins import (
    SimTraderPlugin,
    RealtimeMonitorPlugin
)

# 导出工具插件
from .tools import (
    PerformanceEvaluatorPlugin,
    IPerformanceTools
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
    'RealtimeMonitorPlugin',
    
    # 工具插件
    'PerformanceEvaluatorPlugin',
    'IPerformanceTools'
]

# 便捷函数
def get_available_plugins() -> Dict[str, List[str]]:
    """获取所有可用的插件列表
    
    Returns:
        按类型分类的插件名称字典
    """
    return {
        'data_plugins': [
            'tushare_data',
            'ashare_data',
            'data_preprocessing',
            'warehouse_storage'
        ],
        'strategy_plugins': [
            'daily_kline_scoring',
            'multi_factor_model'
        ],
        'backtest_plugins': [
            'daily_backtest_engine',
            'performance_evaluator'
        ],
        'execution_plugins': [
            'sim_trader',
            'realtime_monitor'
        ],
        'tools': [
            # 性能工具已移动到 evaluator_plugins 目录
        ]
    }

def get_plugin_class(plugin_name: str) -> Optional[Type]:
    """根据插件名称获取插件类
    
    Args:
        plugin_name: 插件名称
        
    Returns:
        插件类或None
    """
    plugin_map = {
        'tushare_data': TushareDataPlugin,
        'ashare_data': AshareDataPlugin,
        'data_preprocessing': DataPreprocessingPlugin,
        'warehouse_storage': WarehouseStoragePlugin,
        'daily_kline_scoring': DailyKlineScoringPlugin,
        'multi_factor_model': MultiFactorModelPlugin,
        'daily_backtest_engine': DailyBacktestEnginePlugin,
        'performance_evaluator': PerformanceEvaluatorPlugin,
        'sim_trader': SimTraderPlugin,
        'realtime_monitor': RealtimeMonitorPlugin,
        # 'performance_tools': PerformanceEvaluatorPlugin  # 已移动到 evaluator_plugins
    }
    
    return plugin_map.get(plugin_name)