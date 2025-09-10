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

from .plugins import (
    BasePlugin,
    PluginRegistry,
    PluginManager,
    PluginDiscovery,
    default_manager,
    default_discovery,
    load_plugin,
    load_plugins,
    unload_plugin,
    get_plugin,
    list_loaded_plugins,
    list_available_plugins,
    discover_and_load_plugins,
    auto_discover_plugins,
    discover_plugins,
    resolve_plugin_dependencies,
    check_plugin_compatibility,
)

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
    'PluginRegistry',
    'PluginManager',
    'PluginDiscovery',
    'default_manager',
    'default_discovery',
    'load_plugin',
    'load_plugins',
    'unload_plugin',
    'get_plugin',
    'list_loaded_plugins',
    'list_available_plugins',
    'discover_and_load_plugins',
    'auto_discover_plugins',
    'discover_plugins',
    'resolve_plugin_dependencies',
    'check_plugin_compatibility',
    
    # 常量
    'FRAMEWORK_VERSION',
    'FRAMEWORK_NAME',
]

# 框架初始化
def initialize_framework():
    """初始化框架
    
    执行框架的初始化操作，如设置默认配置、注册内置插件等。
    """
    # 这里可以添加框架初始化逻辑
    pass


def cleanup_framework():
    """清理框架资源
    
    清理框架占用的资源，如关闭插件、清理缓存等。
    """
    # 清理所有已加载的插件
    from .plugins import default_manager
    default_manager.clear_all_plugins()


# 自动初始化框架
initialize_framework()

# 注册退出时的清理函数
import atexit
atexit.register(cleanup_framework)