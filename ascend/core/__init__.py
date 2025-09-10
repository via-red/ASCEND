"""
ASCEND核心模块
提供框架的基础抽象、协议和类型定义
"""

from .protocols import (
    IAgent,
    IEnvironment,
    IPolicy,
    IModel,
    IRewardFunction,
    IFeatureExtractor,
    IPlugin,
    IMonitor,
    Experience,
)

from .types import (
    State,
    Action,
    Reward,
    Info,
    Config,
    TrainingMetrics,
    ModelCheckpoint,
    TrainingConfig,
    PluginMetadata,
    ComponentType,
    LogLevel,
    FRAMEWORK_VERSION,
    FRAMEWORK_NAME,
)

from .exceptions import (
    AscendError,
    ConfigError,
    ValidationError,
    PluginError,
    PluginNotFoundError,
    PluginLoadError,
    PluginCompatibilityError,
    ComponentError,
    ComponentNotFoundError,
    ComponentInitializationError,
    TrainingError,
    EnvironmentError,
    ModelError,
    SerializationError,
    NetworkError,
    TimeoutError,
    ResourceExhaustedError,
    NotImplementedError,
    DeprecationWarningError,
)

__all__ = [
    # 协议
    'IAgent',
    'IEnvironment',
    'IPolicy',
    'IModel',
    'IRewardFunction',
    'IFeatureExtractor',
    'IPlugin',
    'IMonitor',
    'Experience',
    
    # 类型
    'State',
    'Action',
    'Reward',
    'Info',
    'Config',
    'TrainingMetrics',
    'ModelCheckpoint',
    'TrainingConfig',
    'PluginMetadata',
    'ComponentType',
    'LogLevel',
    'FRAMEWORK_VERSION',
    'FRAMEWORK_NAME',
    
    # 异常
    'AscendError',
    'ConfigError',
    'ValidationError',
    'PluginError',
    'PluginNotFoundError',
    'PluginLoadError',
    'PluginCompatibilityError',
    'ComponentError',
    'ComponentNotFoundError',
    'ComponentInitializationError',
    'TrainingError',
    'EnvironmentError',
    'ModelError',
    'SerializationError',
    'NetworkError',
    'TimeoutError',
    'ResourceExhaustedError',
    'NotImplementedError',
    'DeprecationWarningError',
]

# 框架元数据
__version__ = FRAMEWORK_VERSION
__author__ = "ASCEND Team"
__license__ = "Apache 2.0"
__description__ = "Agent-Native System with Cognitive Embedding for Decision-Making"