"""
执行插件层
提供交易执行和实时监控功能的插件集合

包含以下插件:
- 模拟交易器: SimTraderPlugin
- 实时监控: RealtimeMonitorPlugin

协议接口:
- ITrader: 交易执行协议
- IMonitor: 实时监控协议
- IRiskController: 风险控制器协议
"""

from typing import Protocol, Any, Dict, List, Optional, Tuple
from pydantic import BaseModel
import pandas as pd
import numpy as np
from datetime import datetime

# 执行插件协议接口
class ITrader(Protocol):
    """交易执行协议 - 定义交易执行接口"""
    
    def execute_order(self, order: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """执行交易订单
        
        Args:
            order: 订单信息
            **kwargs: 额外参数
            
        Returns:
            执行结果
        """
        ...
    
    def get_position(self, symbol: str, **kwargs) -> Dict[str, Any]:
        """获取持仓信息
        
        Args:
            symbol: 股票代码
            **kwargs: 额外参数
            
        Returns:
            持仓信息
        """
        ...
    
    def get_account_info(self, **kwargs) -> Dict[str, Any]:
        """获取账户信息
        
        Args:
            **kwargs: 额外参数
            
        Returns:
            账户信息
        """
        ...


class IMonitor(Protocol):
    """实时监控协议 - 定义监控接口"""
    
    def monitor_performance(self, metrics: Dict[str, Any], **kwargs) -> None:
        """监控性能指标
        
        Args:
            metrics: 性能指标
            **kwargs: 额外参数
        """
        ...
    
    def detect_anomalies(self, data: Any, **kwargs) -> List[Dict[str, Any]]:
        """检测异常情况
        
        Args:
            data: 监控数据
            **kwargs: 额外参数
            
        Returns:
            异常情况列表
        """
        ...
    
    def generate_alerts(self, anomalies: List[Dict[str, Any]], **kwargs) -> List[Dict[str, Any]]:
        """生成警报
        
        Args:
            anomalies: 异常情况
            **kwargs: 额外参数
            
        Returns:
            警报列表
        """
        ...


class IRiskController(Protocol):
    """风险控制器协议 - 定义风险控制接口"""
    
    def check_risk_limits(self, portfolio: Dict[str, Any], **kwargs) -> Dict[str, bool]:
        """检查风险限制
        
        Args:
            portfolio: 持仓信息
            **kwargs: 额外参数
            
        Returns:
            风险检查结果
        """
        ...
    
    def enforce_risk_rules(self, portfolio: Dict[str, Any], **kwargs) -> List[Dict[str, Any]]:
        """执行风险规则
        
        Args:
            portfolio: 持仓信息
            **kwargs: 额外参数
            
        Returns:
            需要执行的调整操作
        """
        ...
    
    def get_risk_status(self, **kwargs) -> Dict[str, Any]:
        """获取风险状态
        
        Args:
            **kwargs: 额外参数
            
        Returns:
            风险状态信息
        """
        ...


# 导出插件类 (将在具体实现文件中定义)
from .sim_trader_plugin import SimTraderPlugin
from .realtime_monitor_plugin import RealtimeMonitorPlugin

__all__ = [
    # 协议接口
    'ITrader',
    'IMonitor', 
    'IRiskController',
    
    # 具体插件
    'SimTraderPlugin',
    'RealtimeMonitorPlugin'
]