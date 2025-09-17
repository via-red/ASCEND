"""
策略插件层
提供日K线评分策略和多因子模型的插件集合

包含以下插件:
- 日K线评分策略: DailyKlineScoringPlugin
- 多因子模型: MultiFactorModelPlugin

协议接口:
- IStrategyPlugin: 策略插件协议
- IScoringStrategy: 评分策略协议
- IFactorModel: 因子模型协议
"""

from typing import Protocol, Any, Dict, List, Optional, Tuple
from pydantic import BaseModel
import pandas as pd
import numpy as np

# 策略插件协议接口
class IStrategyPlugin(Protocol):
    """策略插件协议 - 定义策略执行接口"""
    
    def execute(self, data: Any, **kwargs) -> Any:
        """执行策略
        
        Args:
            data: 输入数据
            **kwargs: 额外参数
            
        Returns:
            策略执行结果
        """
        ...
    
    def get_strategy_type(self) -> str:
        """获取策略类型
        
        Returns:
            策略类型标识
        """
        ...
    
    def get_required_data_types(self) -> List[str]:
        """获取所需的数据类型
        
        Returns:
            所需的数据类型列表
        """
        ...


class IScoringStrategy(Protocol):
    """评分策略协议 - 定义评分计算接口"""
    
    def calculate_score(self, data: Any, **kwargs) -> Dict[str, float]:
        """计算股票评分
        
        Args:
            data: 输入数据
            **kwargs: 额外参数
            
        Returns:
            股票评分字典 {股票代码: 评分}
        """
        ...
    
    def get_factor_weights(self) -> Dict[str, float]:
        """获取因子权重配置
        
        Returns:
            因子权重字典
        """
        ...
    
    def generate_signals(self, scores: Dict[str, float], **kwargs) -> Dict[str, str]:
        """生成交易信号
        
        Args:
            scores: 股票评分字典
            **kwargs: 额外参数
            
        Returns:
            交易信号字典 {股票代码: 信号}
        """
        ...


class IFactorModel(Protocol):
    """因子模型协议 - 定义因子计算接口"""
    
    def calculate_factors(self, data: Any, **kwargs) -> Dict[str, Any]:
        """计算因子值
        
        Args:
            data: 输入数据
            **kwargs: 额外参数
            
        Returns:
            因子值字典 {因子名称: 因子值}
        """
        ...
    
    def get_available_factors(self) -> List[str]:
        """获取可用的因子列表
        
        Returns:
            因子名称列表
        """
        ...
    
    def validate_factors(self, factors: Dict[str, Any]) -> bool:
        """验证因子数据
        
        Args:
            factors: 因子数据
            
        Returns:
            是否验证通过
        """
        ...


# 导出插件类 (将在具体实现文件中定义)
from .daily_kline_scoring_plugin import DailyKlineScoringPlugin
from .multi_factor_model_plugin import MultiFactorModelPlugin

__all__ = [
    # 协议接口
    'IStrategyPlugin',
    'IScoringStrategy', 
    'IFactorModel',
    
    # 具体插件
    'DailyKlineScoringPlugin',
    'MultiFactorModelPlugin'
]