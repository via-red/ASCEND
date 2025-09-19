"""
ASCEND插件发现机制
提供插件的自动发现、加载和依赖解析功能。支持以下特性：
- 自动扫描并发现插件
- 加载插件模块并实例化
- 管理插件之间的依赖关系
- 验证插件的兼容性
"""

import importlib
import importlib.util
import logging
import os
import pkg_resources
import sys
from typing import Dict, List, Optional, Set, Any, Tuple, Type, TYPE_CHECKING

from ascend.plugin_manager.env_utils import get_env_var
from ascend.plugin_manager.version_utils import parse_version_constraint, validate_plugin_version

from pathlib import Path
from dataclasses import dataclass
from pydantic import BaseModel, Field, ValidationError

from ascend.plugin_manager.base import IPlugin, BasePlugin
from ascend.plugin_manager.types import PluginInfo
from ascend.core.exceptions import PluginError
from ascend.core.types import Config

logger = logging.getLogger(__name__)

class PluginDiscovery:
    """插件发现器
    
    负责扫描、发现和加载插件。
    
    Attributes:
        plugin_paths: 插件搜索路径
        discovered_plugins: 已发现的插件信息
        loaded_plugins: 已加载的插件实例
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """初始化插件发现器
        
        Args:
            config: 配置字典，用于获取plugin_paths配置
        """
        self.config = config or {}
        self._discovered_plugins: Dict[str, PluginInfo] = {}
        self._loaded_plugins: Dict[str, IPlugin] = {}
        self._dependency_graph: Dict[str, Set[str]] = {}

    @property
    def discovered_plugins(self) -> Dict[str, PluginInfo]:
        """已发现的插件信息"""
        return self._discovered_plugins
    
    @property
    def loaded_plugins(self) -> Dict[str, IPlugin]:
        """已加载的插件实例"""
        return self._loaded_plugins

    @property
    def plugin_paths(self) -> List[str]:
        """插件搜索路径"""
        # 从配置中获取插件路径，如果没有配置则使用默认路径
        config_paths = self.config.get('plugin_paths', [])
        if config_paths:
            return config_paths
        
        # 默认插件路径
        return [
            "./plugins",
            "./quant_plugins",
            str(Path.home() / ".ascend" / "plugins"),
            "/opt/ascend/plugins"
        ]

    def _register_builtin_plugins(self) -> None:
        """注册内置插件"""
        from .base import get_builtin_plugins
        
        builtin_plugins = get_builtin_plugins()
        
        for plugin_name, plugin_class in builtin_plugins.items():
            # 延迟实例化，避免循环引用
            # 使用类名作为插件名称，实例化推迟到实际加载时
            self._discovered_plugins[plugin_name] = PluginInfo(
                name=plugin_name,
                version="1.0.0",  # 默认版本，实际版本在实例化时获取
                description=f"Builtin plugin: {plugin_name}",
                module_path=plugin_class.__module__,
                dependencies=[],  # 默认无依赖，实际依赖在实例化时获取
                plugin_class=plugin_class,
                config_schema=None  # 配置模型在实例化时获取
            )
            logger.info(f"Registered builtin plugin class: {plugin_name}")
    
    def discover_plugins(self) -> Dict[str, PluginInfo]:
        """发现所有可用的插件
        
        Returns:
            已发现的插件信息字典
        """
        logger.info("Starting plugin discovery...")
        
        # 注册内置插件
        self._register_builtin_plugins()
        logger.info(f"After registering builtin plugins: {list(self._discovered_plugins.keys())}")
        
        # 扫描所有插件路径
        for path in self.plugin_paths:
            plugin_path = Path(path)
            logger.info(f"Scanning plugin path: {plugin_path}")
            if not plugin_path.exists():
                continue
                
            # 扫描路径下的所有Python文件，排除插件管理器自身的文件
            for file_path in plugin_path.glob("*.py"):
                if (file_path.name.startswith("_") or
                    file_path.name in ['base.py', 'discovery.py', 'manager.py', 'types.py', 'env_utils.py']):
                    continue
                    
                try:
                    plugin_info = self._load_plugin_info(file_path)
                    if plugin_info:
                        self.discovered_plugins[plugin_info.name] = plugin_info
                        logger.info(f"Discovered plugin: {plugin_info.name} v{plugin_info.version}")
                except Exception as e:
                    logger.warning(f"Failed to load plugin from {file_path}: {e}")
        
        # 构建依赖图
        self._build_dependency_graph()
        
        return self.discovered_plugins
    
    def _load_plugin_info(self, file_path: Path) -> Optional[PluginInfo]:
        """加载插件信息
        
        Args:
            file_path: 插件文件路径
            
        Returns:
            插件信息，如果不是有效插件则返回None
        """
        module_name = file_path.stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if not spec or not spec.loader:
            return None
            
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            logger.warning(f"Failed to execute module {module_name}: {e}")
            return None
        
        # 查找插件类
        plugin_class = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                attr != IPlugin and 
                hasattr(attr, "__bases__") and 
                any(base.__name__ == "IPlugin" for base in attr.__bases__)):
                plugin_class = attr
                break
        
        if not plugin_class:
            return None
        
        try:
            return PluginInfo(
                name=plugin_class.__name__,
                version="1.0.0",  # 默认版本，实际版本在实例化时获取
                description=f"Plugin: {plugin_class.__name__}",
                module_path=str(file_path),
                dependencies=[],  # 默认无依赖，实际依赖在实例化时获取
                plugin_class=plugin_class,
                config_schema=None  # 配置模型在实例化时获取
            )
        except Exception as e:
            logger.warning(f"Failed to create plugin info for {module_name}: {e}")
            return None
    
    def load_plugin(self, name: str) -> IPlugin:
        """加载指定的插件
        
        Args:
            name: 插件名称
            
        Returns:
            插件实例
            
        Raises:
            PluginError: 当插件加载失败时
        """
        if name in self._loaded_plugins:
            return self._loaded_plugins[name]
            
        plugin_info = self._discovered_plugins.get(name)
        if not plugin_info:
            raise PluginError(f"Plugin {name} not found")
            
        try:
            # 确保依赖已加载
            for dep in plugin_info.dependencies:
                if dep not in self.loaded_plugins:
                    self.load_plugin(dep)
            
            # 实例化插件
            plugin = plugin_info.plugin_class()
            self.loaded_plugins[name] = plugin
            logger.info(f"Loaded plugin: {name} v{plugin_info.version}")
            return plugin
            
        except Exception as e:
            raise PluginError(f"Failed to load plugin {name}: {e}")
    
    def unload_plugin(self, name: str) -> None:
        """卸载指定的插件
        
        Args:
            name: 插件名称
        """
        if name in self.loaded_plugins:
            del self.loaded_plugins[name]
            logger.info(f"Unloaded plugin: {name}")
    
    def get_plugin_info(self, name: str) -> Optional[PluginInfo]:
        """获取插件信息
        
        Args:
            name: 插件名称
            
        Returns:
            插件信息，如果不存在则返回None
        """
        return self.discovered_plugins.get(name)
    
    def list_available_plugins(self) -> List[str]:
        """列出所有可用的插件
        
        Returns:
            插件名称列表
        """
        return list(self.discovered_plugins.keys())
    
    def list_loaded_plugins(self) -> List[str]:
        """列出所有已加载的插件
        
        Returns:
            已加载的插件名称列表
        """
        return list(self.loaded_plugins.keys())
    
    def _build_dependency_graph(self) -> None:
        """构建插件依赖图"""
        self._dependency_graph.clear()
        
        for name, info in self._discovered_plugins.items():
            self._dependency_graph[name] = set(info.dependencies)
    
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
        if not self._discovered_plugins:
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
        if not self._discovered_plugins:
            self.discover_plugins()
        
        incompatible = []
        
        for plugin_name in plugin_names:
            if plugin_name not in self._discovered_plugins:
                incompatible.append(plugin_name)
                continue
            
            # 这里可以添加更复杂的兼容性检查逻辑
            # 目前简化实现：假设所有已发现的插件都兼容
            pass
        
        return (len(incompatible) == 0, incompatible)
    
    def clear_cache(self) -> None:
        """清除发现缓存"""
        self._discovered_plugins.clear()
        self._dependency_graph.clear()


