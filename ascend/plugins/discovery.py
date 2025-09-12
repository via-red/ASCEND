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
import pkg_resources
import sys
from typing import Dict, List, Optional, Set, Any, Tuple, Type
from pathlib import Path
from dataclasses import dataclass
from pydantic import BaseModel, Field, ValidationError

from .base import IPlugin
from ..core.exceptions import PluginError

logger = logging.getLogger(__name__)

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

class PluginDiscovery:
    """插件发现器
    
    负责扫描、发现和加载插件。
    
    Attributes:
        plugin_paths: 插件搜索路径
        discovered_plugins: 已发现的插件信息
        loaded_plugins: 已加载的插件实例
    """
    
    def __init__(self, plugin_paths: Optional[List[str]] = None) -> None:
        """初始化插件发现器
        
        Args:
            plugin_paths: 插件搜索路径列表
        """
        self.plugin_paths = plugin_paths or []
        self.discovered_plugins: Dict[str, PluginInfo] = {}
        self.loaded_plugins: Dict[str, IPlugin] = {}
        self._add_default_paths()
        
    def _add_default_paths(self) -> None:
        """添加默认的插件搜索路径"""
        # 添加当前包的plugins目录
        current_dir = Path(__file__).parent
        self.plugin_paths.append(str(current_dir))
        
        # 添加用户级的插件目录
        user_plugins = Path.home() / ".ascend" / "plugins"
        if user_plugins.exists():
            self.plugin_paths.append(str(user_plugins))
    
    def discover_plugins(self) -> Dict[str, PluginInfo]:
        """发现所有可用的插件
        
        Returns:
            已发现的插件信息字典
        """
        self.discovered_plugins.clear()
        
        # 扫描所有插件路径
        for path in self.plugin_paths:
            plugin_path = Path(path)
            if not plugin_path.exists():
                continue
                
            # 扫描路径下的所有Python文件
            for file_path in plugin_path.glob("*.py"):
                if file_path.name.startswith("_"):
                    continue
                    
                try:
                    plugin_info = self._load_plugin_info(file_path)
                    if plugin_info:
                        self.discovered_plugins[plugin_info.name] = plugin_info
                        logger.info(f"Discovered plugin: {plugin_info.name} v{plugin_info.version}")
                except Exception as e:
                    logger.warning(f"Failed to load plugin from {file_path}: {e}")
        
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
        
        # 创建临时实例以获取元数据
        try:
            temp_instance = plugin_class()
            return PluginInfo(
                name=temp_instance.get_name(),
                version=temp_instance.get_version(),
                description=temp_instance.get_metadata().get("description", ""),
                module_path=str(file_path),
                dependencies=temp_instance.get_metadata().get("dependencies", []),
                plugin_class=plugin_class,
                config_schema=temp_instance.get_config_schema()
            )
        except Exception as e:
            logger.warning(f"Failed to instantiate plugin {module_name}: {e}")
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
        if name in self.loaded_plugins:
            return self.loaded_plugins[name]
            
        plugin_info = self.discovered_plugins.get(name)
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