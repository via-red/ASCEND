"""
ASCEND插件系统类型定义
包含插件系统中使用的所有共享类型定义
"""

from typing import List, Optional, Type
from dataclasses import dataclass
from pydantic import BaseModel
from enum import Enum, auto
from .base import IPlugin

class PluginState(Enum):
    """插件状态枚举
    
    - DISCOVERED: 已发现但未加载
    - LOADED: 已加载但未初始化
    - INITIALIZED: 已初始化但未启动
    - RUNNING: 正在运行
    - STOPPED: 已停止
    - ERROR: 错误状态
    """
    DISCOVERED = auto()
    LOADED = auto()
    INITIALIZED = auto()
    RUNNING = auto()
    STOPPED = auto()
    ERROR = auto()

@dataclass
class PluginInfo:
    """插件信息数据类
    
    Attributes:
        name: 插件名称
        version: 插件版本
        description: 插件描述
        module_path: 模块路径
        dependencies: 依赖的其他插件
        plugin_class: 插件类型
        config_schema: 配置模式
    """
    name: str
    version: str
    description: str
    module_path: str
    dependencies: List[str]
    plugin_class: Type[IPlugin]
    config_schema: Optional[Type[BaseModel]] = None

@dataclass
class PluginStatus:
    """插件状态信息
    
    Attributes:
        state: 当前状态
        error: 错误信息（如果有）
        config: 当前配置
        dependencies: 依赖状态
    """
    state: PluginState
    error: Optional[str] = None
    config: Optional[dict] = None
    dependencies: Optional[dict] = None