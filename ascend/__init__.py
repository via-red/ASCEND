"""
ASCEND Framework - Agent-Native System with Cognitive Embedding for Decision-Making

一个基于强化学习的主动式智能体通用框架，采用完全抽象、协议驱动的设计，
支持插件化架构和配置驱动的工作流。
"""

from .core import (
    # 协议
    IAgent,
    IEnvironment,
    IPolicy,
    IModel,
    IRewardFunction,
    IFeatureExtractor,
    IPlugin,
    IMonitor,
    Experience,
    
    # 类型
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
    
    # 异常
    AscendError,
    ConfigError,
    ValidationError,
    PluginError,
    PluginNotFoundError,
    PluginLoadError,
    ComponentError,
    TrainingError,
    EnvironmentError,
    ModelError,
    
    # 常量
    FRAMEWORK_VERSION,
    FRAMEWORK_NAME,
)

from .config import (
    ConfigParser,
    ConfigValidator,
    ConfigLoader,
    default_parser,
    default_validator,
    default_loader,
    load_config,
    validate_config,
    create_default_config,
    save_config,
)

from .plugin_manager import (
    BasePlugin,
    PluginManager,
    PluginDiscovery
)

# 导入统一的ASCEND实例
from .ascend import Ascend

# 框架元数据
__version__ = FRAMEWORK_VERSION
__author__ = "ASCEND Team"
__license__ = "Apache 2.0"
__description__ = "Agent-Native System with Cognitive Embedding for Decision-Making"

__all__ = [
    # 框架元数据
    '__version__',
    '__author__',
    '__license__',
    '__description__',
    
    # 核心协议
    'IAgent',
    'IEnvironment',
    'IPolicy',
    'IModel',
    'IRewardFunction',
    'IFeatureExtractor',
    'IPlugin',
    'IMonitor',
    'Experience',
    
    # 核心类型
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
    
    # 核心异常
    'AscendError',
    'ConfigError',
    'ValidationError',
    'PluginError',
    'PluginNotFoundError',
    'PluginLoadError',
    'ComponentError',
    'TrainingError',
    'EnvironmentError',
    'ModelError',
    
    # 配置模块
    'ConfigParser',
    'ConfigValidator',
    'ConfigLoader',
    'default_parser',
    'default_validator',
    'default_loader',
    'load_config',
    'validate_config',
    'create_default_config',
    'save_config',
    
    # 插件模块
    'BasePlugin',
    'PluginManager',
    'PluginDiscovery',

    # 统一入口
    'Ascend',

    # 常量
    'FRAMEWORK_VERSION',
    'FRAMEWORK_NAME',
]

