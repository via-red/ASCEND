"""
ASCEND核心类型定义
提供框架中使用的基础数据类型和类型别名
"""

from typing import Any, Dict, List, Tuple, Union, Optional, Callable
from typing_extensions import TypeAlias
from dataclasses import dataclass
from enum import Enum

# 策略类型定义
class PolicyType(Enum):
    """策略类型枚举"""
    RANDOM = "random"  # 随机策略
    DETERMINISTIC = "deterministic"  # 确定性策略
    STOCHASTIC = "stochastic"  # 随机性策略
    HYBRID = "hybrid"  # 混合策略

# 基础类型别名
State: TypeAlias = Dict[str, Any]
Action: TypeAlias = Any
Reward: TypeAlias = float
Info: TypeAlias = Dict[str, Any]
Config: TypeAlias = Dict[str, Any]

@dataclass
class Experience:
    """经验回放数据类"""
    state: State
    action: Action
    reward: Reward
    next_state: State
    done: bool
    info: Optional[Info] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'state': self.state,
            'action': self.action,
            'reward': self.reward,
            'next_state': self.next_state,
            'done': self.done,
            'info': self.info or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Experience':
        """从字典创建实例"""
        return cls(
            state=data['state'],
            action=data['action'],
            reward=data['reward'],
            next_state=data['next_state'],
            done=data['done'],
            info=data.get('info')
        )


@dataclass
class TrainingMetrics:
    """训练指标数据类"""
    episode: int
    total_reward: float
    episode_length: int
    avg_reward: float
    loss: Optional[float] = None
    learning_rate: Optional[float] = None
    exploration_rate: Optional[float] = None
    custom_metrics: Optional[Dict[str, Any]] = None


@dataclass  
class ModelCheckpoint:
    """模型检查点数据类"""
    step: int
    episode: int
    total_reward: float
    model_state: Dict[str, Any]
    optimizer_state: Optional[Dict[str, Any]] = None
    metrics: Optional[TrainingMetrics] = None


class ComponentType(Enum):
    """组件类型枚举"""
    AGENT = "agent"
    ENVIRONMENT = "environment"
    POLICY = "policy"
    MODEL = "model"
    REWARD = "reward"
    FEATURE_EXTRACTOR = "feature_extractor"
    MONITOR = "monitor"
    PLUGIN = "plugin"


class LogLevel(Enum):
    """日志级别枚举"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class PluginMetadata:
    """插件元数据类"""
    name: str
    version: str
    description: str
    author: str
    license: str
    requires: List[str]  # 依赖的其他插件
    provides: List[str]  # 提供的功能组件
    compatible_with: List[str]  # 兼容的框架版本
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'license': self.license,
            'requires': self.requires,
            'provides': self.provides,
            'compatible_with': self.compatible_with
        }


@dataclass
class TrainingConfig:
    """训练配置数据类"""
    total_timesteps: int = 1000000
    learning_starts: int = 10000
    batch_size: int = 64
    gamma: float = 0.99
    train_freq: int = 4
    target_update_freq: int = 10000
    exploration_fraction: float = 0.1
    exploration_initial_eps: float = 1.0
    exploration_final_eps: float = 0.01
    eval_freq: int = 10000
    n_eval_episodes: int = 5
    save_freq: int = 50000
    log_dir: str = "./logs"
    checkpoint_dir: str = "./checkpoints"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'total_timesteps': self.total_timesteps,
            'learning_starts': self.learning_starts,
            'batch_size': self.batch_size,
            'gamma': self.gamma,
            'train_freq': self.train_freq,
            'target_update_freq': self.target_update_freq,
            'exploration_fraction': self.exploration_fraction,
            'exploration_initial_eps': self.exploration_initial_eps,
            'exploration_final_eps': self.exploration_final_eps,
            'eval_freq': self.eval_freq,
            'n_eval_episodes': self.n_eval_episodes,
            'save_freq': self.save_freq,
            'log_dir': self.log_dir,
            'checkpoint_dir': self.checkpoint_dir
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrainingConfig':
        """从字典创建实例"""
        return cls(**data)


# 框架常量
FRAMEWORK_VERSION = "0.1.0"
FRAMEWORK_NAME = "ASCEND"
DEFAULT_CONFIG_PATH = "config.yaml"
DEFAULT_LOG_LEVEL = LogLevel.INFO