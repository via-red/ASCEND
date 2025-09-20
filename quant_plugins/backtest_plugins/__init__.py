"""
回测插件层
提供回测引擎和性能评估功能的插件集合

包含以下插件:
- 回测引擎: DailyBacktestEnginePlugin

协议接口:
- IBacktestEngine: 回测引擎协议
- IPerformanceEvaluator: 性能评估协议
- IRiskManager: 风险管理协议
"""

from typing import Protocol, Any, Dict, List, Optional, Tuple
from pydantic import BaseModel
import pandas as pd
import numpy as np
from datetime import datetime

# 回测插件协议接口
class IBacktestEngine(Protocol):
    """回测引擎协议 - 定义回测执行接口"""
    
    def run_backtest(self, strategy: Any, data: Any, **kwargs) -> Dict[str, Any]:
        """运行回测
        
        Args:
            strategy: 策略实例
            data: 回测数据
            **kwargs: 额外参数
            
        Returns:
            回测结果
        """
        ...
    
    def get_backtest_parameters(self) -> Dict[str, Any]:
        """获取回测参数
        
        Returns:
            回测参数配置
        """
        ...
    
    def generate_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成回测报告
        
        Args:
            results: 回测结果
            
        Returns:
            回测报告
        """
        ...


class IPerformanceEvaluator(Protocol):
    """性能评估协议 - 定义性能指标计算接口"""
    
    def calculate_metrics(self, equity_curve: pd.Series,
                         trades: List[Dict], **kwargs) -> Dict[str, float]:
        """计算性能指标
        
        Args:
            equity_curve: 净值曲线
            trades: 交易记录列表
            **kwargs: 额外参数
            
        Returns:
            性能指标字典
        """
        ...
    
    def get_available_metrics(self) -> List[str]:
        """获取可用的性能指标
        
        Returns:
            指标名称列表
        """
        ...
    
    def compare_with_benchmark(self, equity_curve: pd.Series,
                              benchmark: pd.Series, **kwargs) -> Dict[str, Any]:
        """与基准对比
        
        Args:
            equity_curve: 策略净值曲线
            benchmark: 基准净值曲线
            **kwargs: 额外参数
            
        Returns:
            对比结果
        """
        ...


class IRiskManager(Protocol):
    """风险管理协议 - 定义风险控制接口"""
    
    def validate_trade(self, trade: Dict, portfolio: Dict, **kwargs) -> bool:
        """验证交易是否合规
        
        Args:
            trade: 交易信息
            portfolio: 当前持仓
            **kwargs: 额外参数
            
        Returns:
            是否允许交易
        """
        ...
    
    def get_risk_limits(self) -> Dict[str, float]:
        """获取风险限制
        
        Returns:
            风险限制配置
        """
        ...
    
    def calculate_risk_metrics(self, portfolio: Dict, **kwargs) -> Dict[str, float]:
        """计算风险指标
        
        Args:
            portfolio: 持仓信息
            **kwargs: 额外参数
            
        Returns:
            风险指标
        """
        ...


# 导出插件类 (将在具体实现文件中定义)
from .daily_backtest_engine_plugin import DailyBacktestEnginePlugin
# 性能评估器已移动到 evaluator_plugins 目录

__all__ = [
    # 协议接口
    'IBacktestEngine',
    'IPerformanceEvaluator',
    'IRiskManager',
    
    # 具体插件
    'DailyBacktestEnginePlugin',
    
]