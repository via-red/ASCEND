"""
ASCEND Plugin Manager
提供插件加载、管理和生命周期管理功能。支持以下特性：
- 插件生命周期管理（加载、初始化、启动、停止、卸载）
- 插件配置管理
- 插件依赖管理
- 插件状态监控
"""

import logging
from typing import Dict, Any, List, Optional, Type
from pathlib import Path

from ascend.plugin_manager.base import IPlugin, BasePlugin
from ascend.plugin_manager.discovery import PluginDiscovery
from ascend.plugin_manager.types import PluginInfo, PluginState, PluginStatus
from ascend.plugin_manager.version_utils import parse_version_constraint, validate_plugin_version
from ascend.core.exceptions import PluginError, PluginNotFoundError, PluginLoadError
from ascend.core.types import Config

logger = logging.getLogger(__name__)


class PluginManager:
    """插件管理器
    
    负责插件的生命周期管理和状态维护。
    
    Attributes:
        discovery: 插件发现器
        plugins: 已加载的插件实例
        plugin_status: 插件状态信息
        config: 配置字典
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        """初始化插件管理器
        
        Args:
            config: 配置字典（可选）
        """
        self.config = config or {}
        self.discovery = PluginDiscovery(config=config)
        self.plugins: Dict[str, IPlugin] = {}
        self.plugin_status: Dict[str, PluginStatus] = {}
        
        # 自动发现插件
        self.discover_plugins()
        
    def discover_plugins(self, refresh: bool = False) -> Dict[str, PluginInfo]:
        """发现可用插件
        
        Args:
            refresh: 是否刷新缓存
            
        Returns:
            插件信息字典
        """
        if refresh:
            self.discovery.clear_cache()
            
        discovered = self.discovery.discover_plugins()
        logger.info(f"发现插件: {list(discovered.keys())}")
        
        # 更新每个插件的状态
        for name, info in discovered.items():
            if name not in self.plugin_status:
                dependencies = getattr(info, 'dependencies', [])
                self.plugin_status[name] = PluginStatus(
                    state=PluginState.DISCOVERED,
                    dependencies={dep: False for dep in dependencies}
                )
                
        return discovered
    
    def load_plugin(self, plugin_spec: str) -> IPlugin:
        """加载插件
        
        Args:
            plugin_spec: 插件规格（名称或名称:版本约束）
            
        Returns:
            插件实例
            
        Raises:
            PluginError: 插件加载失败
        """
        try:
            # 解析插件名称和版本约束
            plugin_name, version_constraint = parse_version_constraint(plugin_spec)
            
            logger.info(f"正在加载插件: {plugin_spec}")
            
            # 检查插件是否已经加载
            if plugin_name in self.plugins:
                logger.info(f"插件已加载，返回现有实例: {plugin_name}")
                return self.plugins[plugin_name]
            
            # 检查插件信息
            info = self.discovery.get_plugin_info(plugin_name)
            if not info:
                raise PluginError(f"插件未找到: {plugin_name}")
            
            # 先加载依赖
            for dep in info.dependencies:
                if dep not in self.plugins:
                    self.load_plugin(dep)
            
            # 加载插件
            plugin_class = info.plugin_class
            if not plugin_class:
                raise PluginError(f"插件类未找到: {plugin_name}")
                
            plugin = plugin_class()
            
            # 验证版本约束
            if version_constraint:
                plugin_version = getattr(plugin, 'version', '0.0.0')
                if not validate_plugin_version({'version': plugin_version}, version_constraint):
                    raise PluginError(f"插件 {plugin_name} 版本 {plugin_version} "
                                    f"不满足约束: {version_constraint}")
            
            self.plugins[plugin_name] = plugin
            
            # 更新状态
            status = self.plugin_status.get(plugin_name)
            if status:
                status.state = PluginState.LOADED
                for dep in info.dependencies:
                    status.dependencies[dep] = True
            else:
                # 如果状态不存在，创建新的状态
                dependencies = getattr(info, 'dependencies', [])
                self.plugin_status[plugin_name] = PluginStatus(
                    state=PluginState.LOADED,
                    dependencies={dep: True for dep in dependencies}
                )
            
            logger.info(f"插件加载成功: {plugin_name}")
            return plugin
            
        except Exception as e:
            if plugin_name in self.plugin_status:
                self.plugin_status[plugin_name].state = PluginState.ERROR
                self.plugin_status[plugin_name].error = str(e)
            raise PluginError(f"插件加载失败 {plugin_spec}: {e}")
    
    def initialize_plugin(self, plugin_name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """初始化插件
        
        Args:
            plugin_name: 插件名称
            config: 插件配置
        """
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            raise PluginError(f"插件未加载: {plugin_name}")
            
        try:
            if config:
                plugin.configure(config)
                
            status = self.plugin_status[plugin_name]
            status.state = PluginState.INITIALIZED
            status.config = config
            
        except Exception as e:
            self.plugin_status[plugin_name].state = PluginState.ERROR
            self.plugin_status[plugin_name].error = str(e)
            raise PluginError(f"插件初始化失败 {plugin_name}: {e}")
    
    def start_plugin(self, plugin_name: str) -> None:
        """启动插件
        
        Args:
            plugin_name: 插件名称
        """
        status = self.plugin_status.get(plugin_name)
        if not status or status.state != PluginState.INITIALIZED:
            raise PluginError(f"插件未初始化: {plugin_name}")
        
        try:
            plugin = self.plugins[plugin_name]
            if hasattr(plugin, 'start') and callable(getattr(plugin, 'start')):
                plugin.start()
            
            status.state = PluginState.RUNNING
            
        except Exception as e:
            status.state = PluginState.ERROR
            status.error = str(e)
            raise PluginError(f"插件启动失败 {plugin_name}: {e}")
    
    def stop_plugin(self, plugin_name: str) -> None:
        """停止插件
        
        Args:
            plugin_name: 插件名称
        """
        status = self.plugin_status.get(plugin_name)
        if not status or status.state != PluginState.RUNNING:
            raise PluginError(f"插件未运行: {plugin_name}")
        
        try:
            plugin = self.plugins[plugin_name]
            if hasattr(plugin, 'stop') and callable(getattr(plugin, 'stop')):
                plugin.stop()
            
            status.state = PluginState.STOPPED
            
        except Exception as e:
            status.state = PluginState.ERROR
            status.error = str(e)
            raise PluginError(f"插件停止失败 {plugin_name}: {e}")
    
    def unload_plugin(self, plugin_name: str) -> None:
        """卸载插件
        
        Args:
            plugin_name: 插件名称
        """
        if plugin_name not in self.plugins:
            return
            
        # 先停止插件
        status = self.plugin_status.get(plugin_name)
        if status and status.state == PluginState.RUNNING:
            self.stop_plugin(plugin_name)
        
        # 卸载插件
        self.discovery.unload_plugin(plugin_name)
        del self.plugins[plugin_name]
        if plugin_name in self.plugin_status:
            del self.plugin_status[plugin_name]
    
    def get_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """获取插件实例
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件实例或None
        """
        return self.plugins.get(plugin_name)
    
    def get_plugin_status(self, plugin_name: str) -> Optional[PluginStatus]:
        """获取插件状态
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件状态或None
        """
        return self.plugin_status.get(plugin_name)
    
    def list_loaded_plugins(self) -> List[str]:
        """列出所有已加载的插件
        
        Returns:
            插件名称列表
        """
        return list(self.plugins.keys())
    
    def list_available_plugins(self) -> List[str]:
        """列出所有可用插件（已发现但未必加载）
        
        Returns:
            可用插件名称列表
        """
        return list(self.discovery.discovered_plugins.keys())
    
    def load_plugins(self, plugin_specs: List[str], configs: Dict[str, Config] = None) -> List[BasePlugin]:
        """批量加载插件
        
        Args:
            plugin_specs: 插件规格列表
            configs: 插件配置字典（可选）
            
        Returns:
            加载的插件实例列表
            
        Raises:
            PluginError: 插件加载失败
        """
        loaded_plugins = []
        failed_plugins = []
        
        for plugin_spec in plugin_specs:
            try:
                plugin = self.load_plugin(plugin_spec)
                
                # 初始化插件配置
                plugin_name, _ = parse_version_constraint(plugin_spec)
                if configs and plugin_name in configs:
                    self.initialize_plugin(plugin_name, configs[plugin_name])
                
                loaded_plugins.append(plugin)
                logger.info(f"成功加载插件: {plugin_spec}")
                
            except Exception as e:
                logger.error(f"插件加载失败 {plugin_spec}: {e}")
                failed_plugins.append(plugin_spec)
                continue
        
        if failed_plugins:
            raise PluginError(f"插件加载失败: {', '.join(failed_plugins)}")
        
        return loaded_plugins
    
    def clear_all_plugins(self) -> None:
        """清除所有已加载的插件"""
        for plugin_name in list(self.plugins.keys()):
            try:
                self.unload_plugin(plugin_name)
            except PluginError:
                # 忽略卸载错误，继续处理其他插件
                continue
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出 - 清理所有插件"""
        self.clear_all_plugins()

