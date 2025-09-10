"""
ASCEND插件发现机制
提供插件的自动发现、加载和依赖解析功能
"""

import importlib
import pkg_resources
import sys
from typing import Dict, List, Optional, Set, Any, Tuple
from pathlib import Path

from ascend.core.exceptions import PluginError, PluginNotFoundError
from ascend.core.types import Config
from .base import BasePlugin
from .manager import PluginManager

class PluginDiscovery:
    """插件发现类"""
    
    def __init__(self, plugin_dirs: Optional[List[str]] = None):
        """
        初始化插件发现器
        
        Args:
            plugin_dirs: 额外的插件目录列表
        """
        self.plugin_dirs = plugin_dirs or []
        self._discovered_plugins: Dict[str, Any] = {}
        self._dependency_graph: Dict[str, Set[str]] = {}
    
    def discover_plugins(self, refresh: bool = False) -> Dict[str, Any]:
        """发现所有可用插件
        
        Args:
            refresh: 是否刷新缓存
            
        Returns:
            插件信息字典
        """
        if not refresh and self._discovered_plugins:
            return self._discovered_plugins.copy()
        
        plugins = {}
        
        # 1. 通过entry points发现插件
        plugins.update(self._discover_via_entry_points())
        
        # 2. 通过文件系统发现插件
        plugins.update(self._discover_via_filesystem())
        
        # 3. 构建依赖图
        self._build_dependency_graph(plugins)
        
        self._discovered_plugins = plugins
        return plugins.copy()
    
    def _discover_via_entry_points(self) -> Dict[str, Any]:
        """通过Python entry points发现插件"""
        plugins = {}
        
        try:
            for entry_point in pkg_resources.iter_entry_points('ascend.plugins'):
                try:
                    plugin_class = entry_point.load()
                    if issubclass(plugin_class, BasePlugin):
                        plugin_instance = plugin_class()
                        plugins[entry_point.name] = {
                            'type': 'entry_point',
                            'entry_point': entry_point,
                            'class': plugin_class,
                            'instance': plugin_instance,
                            'metadata': plugin_instance.get_metadata()
                        }
                except Exception as e:
                    # 忽略加载失败的插件
                    print(f"Warning: Failed to load plugin {entry_point.name}: {e}")
                    continue
        except Exception as e:
            print(f"Warning: Failed to discover plugins via entry points: {e}")
        
        return plugins
    
    def _discover_via_filesystem(self) -> Dict[str, Any]:
        """通过文件系统发现插件"""
        plugins = {}
        
        # 这里可以实现自定义的文件系统插件发现逻辑
        # 例如：扫描特定目录下的Python模块
        
        return plugins
    
    def _build_dependency_graph(self, plugins: Dict[str, Any]) -> None:
        """构建插件依赖图"""
        self._dependency_graph.clear()
        
        for plugin_name, plugin_info in plugins.items():
            metadata = plugin_info['metadata']
            requires = set(metadata.get('requires', []))
            self._dependency_graph[plugin_name] = requires
    
    def resolve_dependencies(self, plugin_names: List[str]) -> List[str]:
        """解析插件依赖关系
        
        Args:
            plugin_names: 请求的插件名称列表
            
        Returns:
            包含所有依赖的插件名称列表（拓扑排序）
            
        Raises:
            PluginError: 依赖解析失败
        """
        # 确保插件信息已发现
        self.discover_plugins()
        
        # 收集所有需要的插件（包括依赖）
        all_plugins = set(plugin_names)
        to_process = set(plugin_names)
        
        while to_process:
            current_plugin = to_process.pop()
            
            if current_plugin not in self._dependency_graph:
                raise PluginError(f"Unknown plugin: {current_plugin}")
            
            # 添加依赖
            dependencies = self._dependency_graph[current_plugin]
            new_dependencies = dependencies - all_plugins
            
            all_plugins.update(new_dependencies)
            to_process.update(new_dependencies)
        
        # 拓扑排序
        return self._topological_sort(list(all_plugins))
    
    def _topological_sort(self, plugins: List[str]) -> List[str]:
        """对插件进行拓扑排序
        
        Args:
            plugins: 插件名称列表
            
        Returns:
            拓扑排序后的插件列表
            
        Raises:
            PluginError: 循环依赖检测
        """
        # 构建入度表
        in_degree = {plugin: 0 for plugin in plugins}
        graph = {plugin: set() for plugin in plugins}
        
        for plugin in plugins:
            if plugin in self._dependency_graph:
                for dep in self._dependency_graph[plugin]:
                    if dep in plugins:
                        graph[dep].add(plugin)
                        in_degree[plugin] += 1
        
        # 找到所有入度为0的节点
        queue = [plugin for plugin in plugins if in_degree[plugin] == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 检查是否有循环依赖
        if len(result) != len(plugins):
            raise PluginError("Circular dependency detected among plugins")
        
        return result
    
    def check_compatibility(self, plugin_names: List[str]) -> Tuple[bool, List[str]]:
        """检查插件兼容性
        
        Args:
            plugin_names: 插件名称列表
            
        Returns:
            (是否兼容, 不兼容的插件列表)
        """
        self.discover_plugins()
        
        incompatible = []
        
        for plugin_name in plugin_names:
            if plugin_name not in self._discovered_plugins:
                incompatible.append(plugin_name)
                continue
            
            plugin_info = self._discovered_plugins[plugin_name]
            metadata = plugin_info['metadata']
            
            # 检查框架版本兼容性
            compatible_versions = metadata.get('compatible_with', [])
            if not self._is_version_compatible(compatible_versions):
                incompatible.append(plugin_name)
        
        return (len(incompatible) == 0, incompatible)
    
    def _is_version_compatible(self, compatible_versions: List[str]) -> bool:
        """检查版本兼容性
        
        Args:
            compatible_versions: 兼容的版本列表
            
        Returns:
            是否兼容
        """
        # 这里实现版本兼容性检查逻辑
        # 简化实现：假设所有版本都兼容
        return True
    
    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """获取插件详细信息
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件信息字典或None
        """
        self.discover_plugins()
        return self._discovered_plugins.get(plugin_name)
    
    def find_plugins_by_type(self, component_type: str) -> List[str]:
        """根据组件类型查找插件
        
        Args:
            component_type: 组件类型
            
        Returns:
            提供该类型组件的插件名称列表
        """
        self.discover_plugins()
        
        matching_plugins = []
        
        for plugin_name, plugin_info in self._discovered_plugins.items():
            metadata = plugin_info['metadata']
            provides = metadata.get('provides', [])
            
            if component_type in provides:
                matching_plugins.append(plugin_name)
        
        return matching_plugins
    
    def find_plugins_by_capability(self, capability: str) -> List[str]:
        """根据能力查找插件
        
        Args:
            capability: 能力关键词
            
        Returns:
            提供该能力的插件名称列表
        """
        self.discover_plugins()
        
        matching_plugins = []
        
        for plugin_name, plugin_info in self._discovered_plugins.items():
            metadata = plugin_info['metadata']
            description = metadata.get('description', '').lower()
            provides = [p.lower() for p in metadata.get('provides', [])]
            
            if (capability.lower() in description or
                capability.lower() in provides):
                matching_plugins.append(plugin_name)
        
        return matching_plugins
    
    def clear_cache(self) -> None:
        """清除发现缓存"""
        self._discovered_plugins.clear()
        self._dependency_graph.clear()


# 创建默认插件发现器实例
default_discovery = PluginDiscovery()


def discover_and_load_plugins(plugin_names: List[str], 
                             configs: Optional[Dict[str, Config]] = None,
                             manager: Optional[PluginManager] = None) -> List[BasePlugin]:
    """发现并加载插件（便捷函数）
    
    Args:
        plugin_names: 插件名称列表
        configs: 插件配置字典
        manager: 插件管理器实例（可选）
        
    Returns:
        加载的插件实例列表
        
    Raises:
        PluginError: 插件加载失败
    """
    manager = manager or default_manager
    configs = configs or {}
    
    # 解析依赖关系
    resolved_plugins = default_discovery.resolve_dependencies(plugin_names)
    
    # 检查兼容性
    compatible, incompatible = default_discovery.check_compatibility(resolved_plugins)
    if not compatible:
        raise PluginError(f"Incompatible plugins: {incompatible}")
    
    # 加载插件
    return manager.load_plugins(resolved_plugins, configs)


def auto_discover_plugins(config: Config, 
                         manager: Optional[PluginManager] = None) -> List[BasePlugin]:
    """自动发现并加载配置中指定的插件
    
    Args:
        config: 配置字典
        manager: 插件管理器实例（可选）
        
    Returns:
        加载的插件实例列表
        
    Raises:
        PluginError: 插件加载失败
    """
    manager = manager or default_manager
    
    plugin_names = config.get('plugins', [])
    plugin_configs = config.get('plugin_configs', {})
    
    return discover_and_load_plugins(plugin_names, plugin_configs, manager)