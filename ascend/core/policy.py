"""
基础策略实现模块

提供了一个实现IPolicy协议的基础策略类，作为所有具体策略实现的基类。
包含了基础的动作选择和策略更新功能。
"""

from typing import List, Dict, Any
import logging
import torch
import numpy as np


from .protocols import IPolicy, State, Action, Experience

logger = logging.getLogger(__name__)

class BasePolicy(IPolicy):
    """基础策略实现
    
    实现了IPolicy协议的抽象基类，提供了策略的基础功能框架。
    具体的策略类需要继承该类并实现抽象方法。
    
    Attributes:
        name (str): 策略名称
        config (Dict[str, Any]): 配置参数
        device (torch.device): 运行设备
    """
    
    def __init__(self, name: str, config: Dict[str, Any]) -> None:
        """初始化策略
        
        Args:
            name: 策略名称
            config: 配置参数字典
        """
        self.name = name
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._init_policy()
        logger.info(f"Initialized policy {self.name} on device {self.device}")
    
    def _init_policy(self) -> None:
        """初始化策略组件
        
        可以在子类中重写以添加具体的策略初始化逻辑
        """
        pass
    
    
    def get_action(self, state: State) -> Action:
        """根据状态选择动作
        
        Args:
            state: 当前状态
            
        Returns:
            选择的动作
        """
        raise NotImplementedError
    
    
    def update(self, experiences: List[Experience]) -> Dict[str, Any]:
        """更新策略参数
        
        Args:
            experiences: 经验数据
            
        Returns:
            更新指标
        """
        raise NotImplementedError
    
    def save(self, path: str) -> None:
        """保存策略状态
        
        Args:
            path: 保存路径
        """
        # 默认实现为空，子类需要根据具体模型实现保存逻辑
        pass
    
    def load(self, path: str) -> None:
        """加载策略状态
        
        Args:
            path: 加载路径
        """
        # 默认实现为空，子类需要根据具体模型实现加载逻辑
        pass
    
    def get_config(self) -> Dict[str, Any]:
        """获取策略配置
        
        Returns:
            配置字典的深拷贝
        """
        return self.config.copy()
    
    def to_device(self, device: torch.device) -> None:
        """将策略移动到指定设备
        
        Args:
            device: 目标设备
        """
        self.device = device
        # 子类需要实现具体的模型迁移逻辑
    
    def train_mode(self) -> None:
        """切换到训练模式"""
        # 子类需要实现具体的模式切换逻辑
        pass
    
    def eval_mode(self) -> None:
        """切换到评估模式"""
        # 子类需要实现具体的模式切换逻辑
        pass
    
    def get_parameters(self) -> Dict[str, Any]:
        """获取策略参数
        
        Returns:
            参数字典
        """
        # 默认实现返回空字典，子类需要实现具体的参数获取逻辑
        return {}
    
    def set_parameters(self, parameters: Dict[str, Any]) -> None:
        """设置策略参数
        
        Args:
            parameters: 参数字典
        """
        # 默认实现为空，子类需要实现具体的参数设置逻辑
        pass