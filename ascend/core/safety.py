"""
基础安全防护实现模块

提供了一个实现ISafetyGuard协议的基础安全防护类，作为所有具体安全防护实现的基类。
包含了基础的动作验证和约束管理功能。
"""

from typing import Dict, Any
import logging
from abc import ABC, abstractmethod

from .protocols import ISafetyGuard, State, Action

logger = logging.getLogger(__name__)

class BaseSafetyGuard(ABC):
    """基础安全防护实现
    
    实现了ISafetyGuard协议的抽象基类，提供了安全防护的基础功能框架。
    具体的安全防护类需要继承该类并实现抽象方法。
    
    Attributes:
        name (str): 安全防护模块名称
        config (Dict[str, Any]): 配置参数
        constraints (Dict[str, Any]): 安全约束条件
    """
    
    def __init__(self, name: str, config: Dict[str, Any]) -> None:
        """初始化安全防护模块
        
        Args:
            name: 安全防护模块名称
            config: 配置参数字典
        """
        self.name = name
        self.config = config
        self.constraints = {}
        self._init_constraints()
        logger.info(f"Initialized safety guard {self.name}")
    
    def _init_constraints(self) -> None:
        """初始化安全约束
        
        可以在子类中重写以添加具体的约束条件
        """
        pass
    
    @abstractmethod
    def validate_action(self, state: State, action: Action) -> bool:
        """验证动作的安全性
        
        Args:
            state: 当前状态
            action: 待验证的动作
            
        Returns:
            是否安全
        """
        raise NotImplementedError
    
    def get_constraints(self) -> Dict[str, Any]:
        """获取约束条件
        
        Returns:
            约束条件字典的深拷贝
        """
        return self.constraints.copy()
    
    def add_constraint(self, name: str, constraint: Any) -> None:
        """添加新的约束条件
        
        Args:
            name: 约束名称
            constraint: 约束条件
        """
        self.constraints[name] = constraint
        logger.info(f"Added constraint {name} to safety guard {self.name}")
    
    def remove_constraint(self, name: str) -> None:
        """移除约束条件
        
        Args:
            name: 约束名称
        """
        if name in self.constraints:
            del self.constraints[name]
            logger.info(f"Removed constraint {name} from safety guard {self.name}")
    
    def clear_constraints(self) -> None:
        """清除所有约束条件"""
        self.constraints.clear()
        logger.info(f"Cleared all constraints from safety guard {self.name}")
    
    def get_config(self) -> Dict[str, Any]:
        """获取安全防护模块配置
        
        Returns:
            配置字典的深拷贝
        """
        return self.config.copy()
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """更新配置参数
        
        Args:
            new_config: 新的配置参数
        """
        self.config.update(new_config)
        logger.info(f"Updated safety guard {self.name} config")