"""
基础认知实现模块

提供了一个实现ICognition协议的基础认知类，作为所有具体认知实现的基类。
包含了基础的状态处理、动作生成和决策解释等功能。
"""

from typing import List, Dict, Any
import logging

from .protocols import ICognition, State, Action


logger = logging.getLogger(__name__)

class BaseCognition(ICognition):
    """基础认知实现
    
    实现了ICognition协议的抽象基类，提供了认知处理的基础功能框架。
    具体的认知类需要继承该类并实现抽象方法。
    
    Attributes:
        name (str): 认知模块名称
        config (Dict[str, Any]): 配置参数
    """
    
    def __init__(self, name: str, config: Dict[str, Any]) -> None:
        """初始化认知模块
        
        Args:
            name: 认知模块名称
            config: 配置参数字典
        """
        self.name = name
        self.config = config
        self._init_processors()
        logger.info(f"Initialized cognition module {self.name}")
    
    def _init_processors(self) -> None:
        """初始化处理器
        
        可以在子类中重写以添加额外的处理器初始化
        """
        pass
    
    
    def process_state(self, raw_state: Any) -> State:
        """处理和理解原始状态
        
        Args:
            raw_state: 原始状态数据
            
        Returns:
            处理后的状态表示
        """
        raise NotImplementedError
    
    
    def generate_actions(self, state: State) -> List[Action]:
        """生成候选动作
        
        Args:
            state: 当前状态
            
        Returns:
            候选动作列表
        """
        raise NotImplementedError
    
    
    def explain_decision(self, state: State, action: Action) -> str:
        """解释决策原因
        
        Args:
            state: 当前状态
            action: 选择的动作
            
        Returns:
            决策解释
        """
        raise NotImplementedError
    
    def get_config(self) -> Dict[str, Any]:
        """获取认知模块配置
        
        Returns:
            配置字典的深拷贝
        """
        return self.config.copy()
    
    def validate_state(self, state: State) -> bool:
        """验证状态是否有效
        
        Args:
            state: 待验证的状态
            
        Returns:
            状态是否有效
        """
        # 子类可以重写以实现具体的状态验证逻辑
        return True
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """更新配置参数
        
        Args:
            new_config: 新的配置参数
        """
        self.config.update(new_config)
        logger.info(f"Updated cognition module {self.name} config")