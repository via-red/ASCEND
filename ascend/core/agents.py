"""
基础智能体实现模块

提供了一个实现IAgent协议的基础智能体类，作为所有具体智能体实现的基类。
包含了基础的状态处理、动作选择、学习更新等功能。
"""

from typing import List, Dict, Any, Optional
import json
import os
import logging

from .protocols import IAgent, State, Action, Knowledge, Experience
from .types import PolicyType

logger = logging.getLogger(__name__)

class BaseAgent(IAgent):
    """基础智能体实现
    
    实现了IAgent协议的抽象基类，提供了智能体的基础功能框架。
    具体的智能体类需要继承该类并实现抽象方法。
    
    Attributes:
        name (str): 智能体名称
        policy (PolicyType): 决策策略
        config (Dict[str, Any]): 配置参数
    """
    
    def __init__(self, name: str, policy: PolicyType, config: Dict[str, Any]) -> None:
        """初始化智能体
        
        Args:
            name: 智能体名称
            policy: 决策策略实例
            config: 配置参数字典
        """
        self.name = name
        self.policy = policy
        self.config = config
        self._init_components()
        logger.info(f"Initialized agent {self.name}")
        
    def _init_components(self) -> None:
        """初始化智能体组件
        
        可以在子类中重写以添加额外的组件初始化
        """
        pass

    def act(self, state: State, knowledge: Optional[Knowledge] = None) -> Action:
        """根据当前状态选择动作
        
        Args:
            state: 当前环境状态
            knowledge: 可选的知识支持
            
        Returns:
            选择的动作
        """
        # 使用策略选择动作
        action = self.policy.get_action(state)
        return action
    
    def learn(self, experiences: List[Experience]) -> Dict[str, Any]:
        """从经验中学习
        
        Args:
            experiences: 经验回放数据列表
            
        Returns:
            学习指标字典
        """
        # 更新策略
        metrics = self.policy.update(experiences)
        return metrics
    
    def process_observation(self, raw_observation: Any) -> State:
        """处理原始观察数据
        
        Args:
            raw_observation: 原始观察数据
            
        Returns:
            处理后的状态
        """
        raise NotImplementedError
    
    def explain(self, state: State, action: Action) -> str:
        """解释当前决策
        
        Args:
            state: 当前状态
            action: 选择的动作
            
        Returns:
            决策解释
        """
        raise NotImplementedError
    
    def save(self, path: str) -> None:
        """保存智能体状态到文件
        
        Args:
            path: 保存路径
        """
        # 确保目录存在
        dir_path = os.path.dirname(path)
        if dir_path:  # 只有当目录路径不为空时才创建
            os.makedirs(dir_path, exist_ok=True)
        
        # 保存策略
        policy_path = os.path.join(path, "policy.pt")
        self.policy.save(policy_path)
        
        # 保存配置
        config_path = os.path.join(path, "config.json")
        with open(config_path, "w") as f:
            json.dump(self.config, f)
            
        logger.info(f"Saved agent state to {path}")
    
    def load(self, path: str) -> None:
        """从文件加载智能体状态
        
        Args:
            path: 加载路径
        """
        # 加载策略
        policy_path = os.path.join(path, "policy.pt")
        self.policy.load(policy_path)
        
        # 加载配置
        config_path = os.path.join(path, "config.json")
        with open(config_path, "r") as f:
            self.config = json.load(f)
            
        logger.info(f"Loaded agent state from {path}")
    
    def get_config(self) -> Dict[str, Any]:
        """获取智能体配置
        
        Returns:
            配置字典的深拷贝
        """
        return self.config.copy()