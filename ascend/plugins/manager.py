"""
ASCEND插件管理器
提供插件的加载、管理和生命周期管理功能
"""

import importlib
import pkg_resources
from typing import Dict, Any, List, Optional, Type
from pathlib import Path

from ascend.core.exceptions import PluginError, PluginNotFoundError, PluginLoadError
from ascend.core.types import Config
from .base import BasePlugin, PluginRegistry

class PluginManager:
    """插件管理器类"""
    
    def __init__(self):
        self.registry = PluginRegistry()
        self._loaded_plugins: Dict[str, BasePlugin] = {}
        self._entry_points_cache: Optional[Dict[str, Any]] = None
    
    def load_plugin(self, plugin_name: str, config: Optional[Dict[str, Any]] = None) -> BasePlugin:
        """加载插件
        
        Args:
            plugin_name: 插件名称或入口点名称
            config: 插件配置（可选）
            
        Returns:
            加载的插件实例
            
        Raises:
            PluginNotFoundError: 插件未找到
            PluginLoadError: 插件加载失败
        """
        # 检查插件是否已加载
        if plugin_name in self._loaded_plugins:
            plugin = self._loaded_plugins[plugin_name]
            if config:
                plugin.configure(config)
            return plugin
        
        try:
            # 发现插件入口点
            entry_point = self._discover_plugin_entry_point(plugin_name)
            if not entry_point:
                raise PluginNotFoundError(plugin_name)
            
            # 加载插件类
            plugin_class = entry_point.load()
            if not issubclass(plugin_class, BasePlugin):
                raise PluginLoadError(plugin_name, "Plugin must inherit from BasePlugin")
            
            # 创建插件实例
            plugin = plugin_class()
            
            # 配置插件
            if config:
                plugin.configure(config)
            
            # 注册插件
            self.registry.register_plugin(plugin)
            
            # 缓存已加载插件
            self._loaded_plugins[plugin_name] = plugin
            
            return plugin
            
        except PluginNotFoundError:
            raise
        except Exception as e:
            raise PluginLoadError(plugin_name, str(e))
    
    def load_plugins(self, plugin_names: List[str], 
                    configs: Optional[Dict[str, Dict[str, Any]]] = None) -> List[BasePlugin]:
        """批量加载插件
        
        Args:
            plugin_names: 插件名称列表
            configs: 插件配置字典（可选）
            
        Returns:
            加载的插件实例列表
            
        Raises:
            PluginError: 插件加载失败
        """
        configs = configs or {}
        loaded_plugins = []
        
        for plugin_name in plugin_names:
            plugin_config = configs.get(plugin_name, {})
            plugin = self.load_plugin(plugin_name, plugin_config)
            loaded_plugins.append(plugin)
        
        return loaded_plugins
    
    def unload_plugin(self, plugin_name: str) -> None:
        """卸载插件
        
        Args:
            plugin_name: 插件名称
            
        Raises:
            PluginNotFoundError: 插件未找到
            PluginError: 插件卸载失败
        """
        if plugin_name not in self._loaded_plugins:
            raise PluginNotFoundError(plugin_name)
        
        try:
            # 从注册表中注销
            self.registry.unregister_plugin(plugin_name)
            
            # 从缓存中移除
            del self._loaded_plugins[plugin_name]
            
        except Exception as e:
            raise PluginError(f"Failed to unload plugin: {e}", plugin_name)
    
    def reload_plugin(self, plugin_name: str, 
                     new_config: Optional[Dict[str, Any]] = None) -> BasePlugin:
        """重新加载插件
        
        Args:
            plugin_name: 插件名称
            new_config: 新配置（可选）
            
        Returns:
            重新加载的插件实例
            
        Raises:
            PluginError: 插件重载失败
        """
        try:
            # 先卸载插件
            if plugin_name in self._loaded_plugins:
                self.unload_plugin(plugin_name)
            
            # 重新加载插件
            return self.load_plugin(plugin_name, new_config)
            
        except Exception as e:
            raise PluginError(f"Failed to reload plugin: {e}", plugin_name)
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """获取已加载的插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件实例或None
        """
        return self._loaded_plugins.get(plugin_name)
    
    def get_plugin_status(self, plugin_name: str) -> Dict[str, Any]:
        """获取插件状态信息
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件状态字典
            
        Raises:
            PluginNotFoundError: 插件未找到
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise PluginNotFoundError(plugin_name)
        
        return {
            'name': plugin.get_name(),
            'version': plugin.get_version(),
            'initialized': plugin.is_initialized(),
            'config': plugin.config,
            'metadata': plugin.get_metadata()
        }
    
    def list_loaded_plugins(self) -> List[str]:
        """列出所有已加载的插件
        
        Returns:
            插件名称列表
        """
        return list(self._loaded_plugins.keys())
    
    def list_available_plugins(self) -> List[Dict[str, Any]]:
        """列出所有可用的插件（通过入口点）
        
        Returns:
            可用插件信息列表
        """
        entry_points = self._discover_all_entry_points()
        plugins_info = []
        
        for name, entry_point in entry_points.items():
            try:
                plugin_class = entry_point.load()
                plugin = plugin_class()
                plugins_info.append({
                    'name': name,
                    'entry_point': str(entry_point),
                    'metadata': plugin.get_metadata()
                })
            except Exception:
                # 忽略加载失败的插件
                continue
        
        return plugins_info
    
    def configure_plugin(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """配置已加载的插件
        
        Args:
            plugin_name: 插件名称
            config: 配置字典
            
        Raises:
            PluginNotFoundError: 插件未找到
            PluginError: 配置失败
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise PluginNotFoundError(plugin_name)
        
        try:
            plugin.configure(config)
        except Exception as e:
            raise PluginError(f"Failed to configure plugin: {e}", plugin_name)
    
    def initialize_plugin(self, plugin_name: str) -> None:
        """初始化插件
        
        Args:
            plugin_name: 插件名称
            
        Raises:
            PluginNotFoundError: 插件未找到
            PluginError: 初始化失败
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise PluginNotFoundError(plugin_name)
        
        try:
            plugin.initialize()
        except Exception as e:
            raise PluginError(f"Failed to initialize plugin: {e}", plugin_name)
    
    def cleanup_plugin(self, plugin_name: str) -> None:
        """清理插件资源
        
        Args:
            plugin_name: 插件名称
            
        Raises:
            PluginNotFoundError: 插件未找到
            PluginError: 清理失败
        """
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            raise PluginNotFoundError(plugin_name)
        
        try:
            plugin.cleanup()
        except Exception as e:
            raise PluginError(f"Failed to cleanup plugin: {e}", plugin_name)
    
    def clear_all_plugins(self) -> None:
        """清除所有已加载的插件"""
        for plugin_name in list(self._loaded_plugins.keys()):
            try:
                self.unload_plugin(plugin_name)
            except PluginError:
                # 忽略卸载错误，继续清理其他插件
                continue
    
    def _discover_plugin_entry_point(self, plugin_name: str) -> Optional[Any]:
        """发现插件入口点
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            入口点实例或None
        """
        entry_points = self._discover_all_entry_points()
        return entry_points.get(plugin_name)
    
    def _discover_all_entry_points(self) -> Dict[str, Any]:
        """发现所有插件入口点
        
        Returns:
            入口点字典
        """
        if self._entry_points_cache is not None:
            return self._entry_points_cache
        
        entry_points = {}
        try:
            for entry_point in pkg_resources.iter_entry_points('ascend.plugins'):
                entry_points[entry_point.name] = entry_point
        except Exception as e:
            # 如果pkg_resources不可用，使用备用发现机制
            entry_points = self._discover_entry_points_fallback()
        
        self._entry_points_cache = entry_points
        return entry_points
    
    def _discover_entry_points_fallback(self) -> Dict[str, Any]:
        """备用入口点发现机制
        
        Returns:
            入口点字典
        """
        # 这里可以实现自定义的插件发现逻辑
        # 例如：扫描特定目录、读取配置文件等
        return {}
    
    def __contains__(self, plugin_name: str) -> bool:
        """检查插件是否已加载
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            是否已加载
        """
        return plugin_name in self._loaded_plugins
    
    def __len__(self) -> int:
        """获取已加载插件数量
        
        Returns:
            插件数量
        """
        return len(self._loaded_plugins)
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出 - 自动清理所有插件"""
        self.clear_all_plugins()


# 创建默认插件管理器实例
default_manager = PluginManager()