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
    
    # 实例
    'default_manager',
    
    # 协议
    'IPlugin',
    
    # 异常
    'PluginError',
    'PluginNotFoundError', 
    'PluginLoadError',
    
    # 便捷函数
    'load_plugin',
    'load_plugins',
    'unload_plugin',
    'get_plugin',
    'list_loaded_plugins',
    'list_available_plugins',
    'configure_plugin',
    'clear_all_plugins',
    'discover_plugins',
    'resolve_plugin_dependencies',
    'check_plugin_compatibility',
]

# 导出常用函数
def load_plugin(plugin_spec: str, config: Optional[Config] = None) -> BasePlugin:
    """快速加载插件的便捷函数
    
    Args:
        plugin_spec: 插件规格（名称或名称:版本约束）
        config: 插件配置（可选）
        
    Returns:
        加载的插件实例
        
    Raises:
        PluginError: 插件加载失败
    """
    plugin = default_manager.load_plugin(plugin_spec)
    if config:
        default_manager.initialize_plugin(plugin.get_name(), config)
    return plugin


def load_plugins(plugin_specs: List[str], configs: Dict[str, Config] = None) -> List[BasePlugin]:
    """批量加载插件的便捷函数
    
    Args:
        plugin_specs: 插件规格列表
        configs: 插件配置字典（可选）
        
    Returns:
        加载的插件实例列表
        
    Raises:
        PluginError: 插件加载失败
    """
    return default_manager.load_plugins(plugin_specs, configs)


def unload_plugin(plugin_name: str) -> None:
    """卸载插件的便捷函数
    
    Args:
        plugin_name: 插件名称
        
    Raises:
        PluginError: 插件卸载失败
    """
    default_manager.unload_plugin(plugin_name)


def get_plugin(plugin_name: str) -> Optional[BasePlugin]:
    """获取已加载插件的便捷函数
    
    Args:
        plugin_name: 插件名称
        
    Returns:
        插件实例或None
    """
    return default_manager.get_plugin(plugin_name)


def list_loaded_plugins() -> List[str]:
    """列出已加载插件的便捷函数
    
    Returns:
        插件名称列表
    """
    return default_manager.list_loaded_plugins()


def list_available_plugins() -> List[str]:
    """列出可用插件的便捷函数
    
    Returns:
        可用插件名称列表
    """
    return default_manager.list_available_plugins()


def configure_plugin(plugin_name: str, config: Config) -> None:
    """配置插件的便捷函数
    
    Args:
        plugin_name: 插件名称
        config: 配置字典
        
    Raises:
        PluginError: 配置失败
    """
    default_manager.initialize_plugin(plugin_name, config)


def clear_all_plugins() -> None:
    """清除所有已加载插件的便捷函数"""
    default_manager.clear_all_plugins()


def discover_plugins(refresh: bool = False) -> Dict[str, Any]:
    """发现所有可用插件的便捷函数
    
    Args:
        refresh: 是否刷新缓存
        
    Returns:
        插件信息字典
    """
    return default_manager.discover_plugins(refresh=refresh)


def resolve_plugin_dependencies(plugin_names: List[str]) -> List[str]:
    """解析插件依赖关系的便捷函数
    
    Args:
        plugin_names: 插件名称列表
        
    Returns:
        包含依赖的插件名称列表
        
    Raises:
        PluginError: 依赖解析失败
    """
    return default_manager.discovery.resolve_dependencies(plugin_names)


def check_plugin_compatibility(plugin_names: List[str]) -> Tuple[bool, List[str]]:
    """检查插件兼容性的便捷函数
    
    Args:
        plugin_names: 插件名称列表
        
    Returns:
        (是否兼容, 不兼容的插件列表)
    """
    return default_manager.discovery.check_compatibility(plugin_names)


# 创建默认插件管理器实例
default_manager = PluginManager()