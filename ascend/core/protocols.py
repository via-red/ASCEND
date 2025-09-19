"""
ASCEND核心协议定义
基于Python Protocol的完全抽象接口设计，支持智能体原生架构。

核心组件:
- IAgent: 智能体协议，定义决策和学习行为
- IEnvironment: 环境协议，定义环境交互
- ICognition: 认知协议，定义高级推理能力
- ISafetyGuard: 安全防护协议，定义安全边界和限制
- IKnowledgeBase: 知识库协议，定义知识存储和检索
- IFeatureExtractor: 特征提取协议，定义特征工程
"""

from __future__ import annotations
from typing import Protocol, Any, Dict, List, Tuple, Optional, Union, TYPE_CHECKING, Type
from typing_extensions import TypeAlias, runtime_checkable
from dataclasses import dataclass
from pydantic import BaseModel

if TYPE_CHECKING:
    from ..plugin_manager.base import IPluginRegistry  # 仅用于类型检查

class IPluginRegistry(Protocol):
    """插件注册表协议
    
    定义插件管理器必须实现的接口。
    """
    
    def register_plugin(self, plugin_class: Type[Any]) -> None:
        """注册插件类"""
        ...
        
    def get_plugin(self, plugin_id: str) -> Any:
        """获取插件实例"""
        ...
        
    def list_plugins(self) -> List[str]:
        """列出已注册的插件"""
        ...

# 基础类型定义
# 状态类型 - 使用字典表示环境或智能体的状态信息
State: TypeAlias = Dict[str, Any]

# 动作类型 - 可以是任意类型，由具体环境定义
Action: TypeAlias = Any

# 奖励类型 - 使用浮点数表示单步奖励
Reward: TypeAlias = float

# 信息类型 - 用于传递额外的调试或监控信息
Info: TypeAlias = Dict[str, Any]

# 知识类型 - 表示结构化的领域知识
Knowledge: TypeAlias = Dict[str, Any]

# 特征类型 - 表示从原始数据提取的特征
Feature: TypeAlias = Dict[str, Any]

@dataclass
class Experience:
    """经验回放数据类
    
    包含单步交互的完整信息，支持高级特征和知识增强的学习。
    
    Attributes:
        state: 当前状态
        action: 执行的动作
        reward: 获得的奖励
        next_state: 下一个状态
        done: 是否完成
        info: 额外信息字典(可选)
        features: 提取的特征字典(可选)，用于增强学习
        knowledge: 相关的知识字典(可选)，支持知识型决策
    """
    state: State
    action: Action
    reward: Reward
    next_state: State
    done: bool
    info: Optional[Info] = None
    features: Optional[Feature] = None
    knowledge: Optional[Knowledge] = None

class ICognition(Protocol):
    """认知层协议 - 负责状态理解、动作生成和决策解释"""
    
    def process_state(self, raw_state: Any) -> State:
        """处理和理解原始状态
        
        Args:
            raw_state: 原始状态数据
            
        Returns:
            处理后的状态表示
        """
        ...
    
    def generate_actions(self, state: State) -> List[Action]:
        """生成候选动作
        
        Args:
            state: 当前状态
            
        Returns:
            候选动作列表
        """
        ...
    
    def explain_decision(self, state: State, action: Action) -> str:
        """解释决策原因
        
        Args:
            state: 当前状态
            action: 选择的动作
            
        Returns:
            决策解释
        """
        ...

class IFeatureExtractor(Protocol):
    """特征提取器协议 - 负责从原始数据中提取特征和状态表示"""
    
    def extract_features(self, raw_data: Any) -> Feature:
        """提取特征
        
        Args:
            raw_data: 原始数据
            
        Returns:
            提取的特征
        """
        ...
    
    def extract_state(self, raw_data: Any) -> State:
        """提取状态表示
        
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

class IKnowledgeBase(Protocol):
    """知识库协议 - 负责知识的存储、查询和更新"""
    
    def query(self, context: Dict[str, Any]) -> Knowledge:
        """查询知识
        
        Args:
            context: 查询上下文
            
        Returns:
            相关知识
        """
        ...
    
    def update(self, new_knowledge: Knowledge) -> None:
        """更新知识库
        
        Args:
            new_knowledge: 新知识
        """
        ...

class ISafetyGuard(Protocol):
    """安全护栏协议 - 负责验证动作的安全性"""
    
    def validate_action(self, state: State, action: Action) -> bool:
        """验证动作的安全性
        
        Args:
            state: 当前状态
            action: 待验证的动作
            
        Returns:
            是否安全
        """
        ...
    
    def get_constraints(self) -> Dict[str, Any]:
        """获取约束条件
        
        Returns:
            约束条件
        """
        ...

class IAgent(Protocol):
    """智能体协议 - 定义决策和学习行为"""
    
    def act(self, state: State, knowledge: Optional[Knowledge] = None) -> Action:
        """根据当前状态选择动作
        
        Args:
            state: 当前环境状态
            knowledge: 可选的知识支持
            
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
    
    def process_observation(self, raw_observation: Any) -> State:
        """处理原始观察数据
        
        Args:
            raw_observation: 原始观察数据
            
        Returns:
            处理后的状态
        """
        ...
    
    def explain(self, state: State, action: Action) -> str:
        """解释当前决策
        
        Args:
            state: 当前状态
            action: 选择的动作
            
        Returns:
            决策解释
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



@runtime_checkable
class IPlugin(Protocol):
    """插件协议 - 所有插件必须实现统一的执行接口"""
    
    def start(self, ascend_instance: Optional['Ascend'] = None, **kwargs) -> Any:
        """启动插件执行
        
        Args:
            ascend_instance: 可选的Ascend实例，用于获取其他插件
            **kwargs: 执行参数
            
        Returns:
            任意类型的执行结果
        """
        ...
    
    def stop(self, **kwargs) -> None:
        """停止插件执行
        
        Args:
            **kwargs: 停止参数
        """
        ...
    
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

    def get_config_schema(self) -> Optional[Type[BaseModel]]:
        """获取插件配置的Pydantic模型（可选）
        
        Returns:
            Pydantic BaseModel类或None
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