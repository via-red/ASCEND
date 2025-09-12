"""
基础环境实现模块

提供了一个实现IEnvironment协议的基础环境类，作为所有具体环境实现的基类。
包含了基础的状态重置、动作执行、状态渲染等功能。
"""

from typing import Any, Dict, Tuple, Optional
import logging
from abc import ABC, abstractmethod
import numpy as np

from .protocols import IEnvironment, State, Action, Reward, Info

logger = logging.getLogger(__name__)

class BaseEnvironment(ABC):
    """基础环境实现
    
    实现了IEnvironment协议的抽象基类，提供了环境的基础功能框架。
    具体的环境类需要继承该类并实现抽象方法。
    
    Attributes:
        name (str): 环境名称
        config (Dict[str, Any]): 配置参数
        state (Optional[State]): 当前环境状态
    """
    
    def __init__(self, name: str, config: Dict[str, Any]) -> None:
        """初始化环境
        
        Args:
            name: 环境名称
            config: 配置参数字典
        """
        self.name = name
        self.config = config
        self.state: Optional[State] = None
        self._setup()
        logger.info(f"Initialized environment {self.name}")
    
    def _setup(self) -> None:
        """设置环境
        
        可以在子类中重写以添加额外的设置逻辑
        """
        pass
    
    @abstractmethod
    def reset(self) -> State:
        """重置环境到初始状态
        
        Returns:
            初始状态
        """
        raise NotImplementedError
    
    @abstractmethod
    def step(self, action: Action) -> Tuple[State, Reward, bool, Info]:
        """执行动作并返回结果
        
        Args:
            action: 要执行的动作
            
        Returns:
            tuple: (next_state, reward, done, info)
        """
        raise NotImplementedError
    
    def render(self) -> Any:
        """渲染环境状态
        
        Returns:
            渲染结果
            
        Note:
            默认实现返回None，子类可以重写以提供可视化功能
        """
        return None
    
    def close(self) -> None:
        """关闭环境资源
        
        Note:
            默认实现不做任何操作，子类可以重写以清理资源
        """
        pass
    
    @property
    @abstractmethod
    def observation_space(self) -> Any:
        """获取观察空间定义
        
        Returns:
            观察空间
        """
        raise NotImplementedError
    
    @property
    @abstractmethod
    def action_space(self) -> Any:
        """获取动作空间定义
        
        Returns:
            动作空间
        """
        raise NotImplementedError
    
    def seed(self, seed: Optional[int] = None) -> None:
        """设置环境的随机种子
        
        Args:
            seed: 随机种子值
        """
        np.random.seed(seed)
    
    def get_config(self) -> Dict[str, Any]:
        """获取环境配置
        
        Returns:
            配置字典的深拷贝
        """
        return self.config.copy()
    
    def validate_action(self, action: Action) -> bool:
        """验证动作是否合法
        
        Args:
            action: 待验证的动作
            
        Returns:
            动作是否合法
        """
        try:
            return action in self.action_space
        except Exception:
            return False