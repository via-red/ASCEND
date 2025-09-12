"""
ASCEND核心协议定义
基于Python Protocol的完全抽象接口设计，支持智能体原生架构
"""

from typing import Protocol, Any, Dict, List, Tuple, Optional, Union
from typing_extensions import TypeAlias
from dataclasses import dataclass
from abc import ABC, abstractmethod

# 基础类型定义
State: TypeAlias = Dict[str, Any]
Action: TypeAlias = Any
Reward: TypeAlias = float
Info: TypeAlias = Dict[str, Any]
Knowledge: TypeAlias = Dict[str, Any]
Feature: TypeAlias = Dict[str, Any]

@dataclass
class Experience:
    """经验回放数据类"""
    state: State
    action: Action
    reward: Reward
    next_state: State
    done: bool
    info: Optional[Info] = None

class IAgent(Protocol):
    """智能体协议 - 定义决策和学习行为"""
    
    def act(self, state: State) -> Action:
        """根据当前状态选择动作
        
        Args:
            state: 当前环境状态
            
        Returns:
            选择的动作
        """
        ...
    
    def learn(self, experiences: List[Experience]) -> Dict[str, Any]:
        """从经验中学习
        
        Args:
            experiences: 经验回放数据列表
            
        Returns:
            学习指标字典
        """
        ...
    
    def save(self, path: str) -> None:
        """保存智能体状态到文件
        
        Args:
            path: 保存路径
        """
        ...
    
    def load(self, path: str) -> None:
        """从文件加载智能体状态
        
        Args:
            path: 加载路径
        """
        ...
    
    def get_config(self) -> Dict[str, Any]:
        """获取智能体配置
        
        Returns:
            配置字典
        """
        ...


class IEnvironment(Protocol):
    """环境协议 - 定义RL环境接口"""
    
    def reset(self) -> State:
        """重置环境到初始状态
        
        Returns:
            初始状态
        """
        ...
    
    def step(self, action: Action) -> Tuple[State, Reward, bool, Info]:
        """执行动作并返回结果
        
        Args:
            action: 要执行的动作
            
        Returns:
            tuple: (next_state, reward, done, info)
        """
        ...
    
    def render(self) -> Any:
        """渲染环境状态
        
        Returns:
            渲染结果
        """
        ...
    
    def close(self) -> None:
        """关闭环境资源"""
        ...
    
    @property
    def observation_space(self) -> Any:
        """获取观察空间定义
        
        Returns:
            观察空间
        """
        ...
    
    @property
    def action_space(self) -> Any:
        """获取动作空间定义
        
        Returns:
            动作空间
        """
        ...


class IPolicy(Protocol):
    """策略协议 - 定义决策逻辑"""
    
    def get_action(self, state: State) -> Action:
        """根据状态选择动作
        
        Args:
            state: 当前状态
            
        Returns:
            选择的动作
        """
        ...
    
    def update(self, experiences: List[Experience]) -> Dict[str, Any]:
        """更新策略参数
        
        Args:
            experiences: 经验数据
            
        Returns:
            更新指标
        """
        ...
    
    def save(self, path: str) -> None:
        """保存策略状态
        
        Args:
            path: 保存路径
        """
        ...
    
    def load(self, path: str) -> None:
        """加载策略状态
        
        Args:
            path: 加载路径
        """
        ...


class IModel(Protocol):
    """模型协议 - 通用AI模型接口"""
    
    def predict(self, inputs: Any, **kwargs) -> Any:
        """模型预测
        
        Args:
            inputs: 输入数据
            **kwargs: 额外参数
            
        Returns:
            预测结果
        """
        ...
    
    def train(self, data: Any, **kwargs) -> Dict[str, Any]:
        """模型训练
        
        Args:
            data: 训练数据
            **kwargs: 额外参数
            
        Returns:
            训练指标
        """
        ...
    
    def save(self, path: str) -> None:
        """保存模型
        
        Args:
            path: 保存路径
        """
        ...
    
    def load(self, path: str) -> None:
        """加载模型
        
        Args:
            path: 加载路径
        """
        ...


class IRewardFunction(Protocol):
    """奖励函数协议 - 定义奖励计算逻辑"""
    
    def calculate(self, state: State, action: Action, 
                 next_state: State, done: bool) -> Reward:
        """计算奖励值
        
        Args:
            state: 当前状态
            action: 执行的动作
            next_state: 下一个状态
            done: 是否结束
            
        Returns:
            奖励值
        """
        ...
    
    def reset(self) -> None:
        """重置奖励函数状态"""
        ...


class IFeatureExtractor(Protocol):
    """特征提取协议 - 将原始数据转换为状态表示"""
    
    def extract(self, raw_data: Any) -> State:
        """提取特征
        
        Args:
            raw_data: 原始数据
            
        Returns:
            状态表示
        """
        ...
    
    def get_feature_dim(self) -> int:
        """获取特征维度
        
        Returns:
            特征维度
        """
        ...


class IPlugin(Protocol):
    """插件协议 - 定义扩展组件接口"""
    
    def register(self, registry: 'IPluginRegistry') -> None:
        """注册插件到框架
        
        Args:
            registry: 插件注册表
        """
        ...
    
    def configure(self, config: Dict[str, Any]) -> None:
        """配置插件参数
        
        Args:
            config: 配置字典
        """
        ...
    
    def get_name(self) -> str:
        """获取插件名称
        
        Returns:
            插件名称
        """
        ...
    
    def get_version(self) -> str:
        """获取插件版本
        
        Returns:
            插件版本
        """
        ...
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取插件元数据
        
        Returns:
            元数据字典
        """
        ...


class IMonitor(Protocol):
    """监控协议 - 定义训练过程监控"""
    
    def on_step_start(self, step: int, state: State) -> None:
        """步骤开始回调
        
        Args:
            step: 步骤数
            state: 当前状态
        """
        ...
    
    def on_step_end(self, step: int, state: State, action: Action, 
                   reward: Reward, next_state: State, done: bool) -> None:
        """步骤结束回调
        
        Args:
            step: 步骤数
            state: 当前状态
            action: 执行的动作
            reward: 获得的奖励
            next_state: 下一个状态
            done: 是否结束
        """
        ...
    
    def on_episode_start(self, episode: int) -> None:
        """回合开始回调
        
        Args:
            episode: 回合数
        """
        ...
    
    def on_episode_end(self, episode: int, total_reward: Reward) -> None:
        """回合结束回调
        
        Args:
            episode: 回合数
            total_reward: 总奖励
        """
        ...