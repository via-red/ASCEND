"""
ASCEND插件模块
提供插件系统的核心功能，包括插件管理、发现和生命周期管理
"""

from typing import Any, Dict, List, Optional, Tuple

# 导入协议和异常
from ascend.core.protocols import IPlugin
from ascend.core.exceptions import PluginError, PluginNotFoundError, PluginLoadError
from ascend.core.types import Config

# 导入基础类
from .base import BasePlugin
from .manager import PluginManager
from .discovery import PluginDiscovery


__all__ = [
    # 基础类
    'BasePlugin',
    'PluginManager', 
    'PluginDiscovery',
    
    # 协议
    'IPlugin',
    
    # 异常
    'PluginError',
    'PluginNotFoundError', 
    'PluginLoadError'
]