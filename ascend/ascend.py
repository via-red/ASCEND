"""
ASCEND框架统一入口类
提供统一的接口来管理配置、插件和框架功能
"""

import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from ascend.core.protocols import IPlugin
from ascend.plugin_manager.types import PluginInfo



from .core.types import Config
from .core.exceptions import ConfigError, PluginError
from .config import load_config as config_load_config
from .plugin_manager import PluginManager
from .plugin_manager.version_utils import parse_version_constraint

logger = logging.getLogger(__name__)


class Ascend:
    """ASCEND框架统一入口类
    
    提供统一的接口来管理配置、插件和框架功能
    
    Attributes:
        config: 当前加载的配置
        plugin_manager: 插件管理器实例
    """
    
    def __init__(self, config_path: Optional[str] = None, config: Optional[Config] = None):
        """初始化ASCEND实例
        
        Args:
            config_path: 配置文件路径，如果为None则使用空配置
            config: 直接传入的配置字典，优先级高于config_path
        """
        self.config: Config = {}
        
        # 优先使用直接传入的配置
        if config is not None:
            self.config = config
        elif config_path:
            self.config = config_load_config(config_path)
        
        # 创建插件管理器实例，传入配置
        self.plugin_manager = PluginManager(config=self.config)
        
        # 向后兼容的属性
        self.loaded_plugins = self.plugin_manager.plugins
        
        logger.info("ASCEND实例初始化完成")
        
        # 初始化插件
        self._initialize_plugins()
    
    
    def scan_and_load_plugins(self, plugin_names: Optional[List[str]] = None) -> List[str]:
        """扫描并加载插件
        
        Args:
            plugin_names: 要加载的插件名称列表，如果为None则加载配置中的所有插件
            
        Returns:
            成功加载的插件名称列表
            
        Raises:
            PluginError: 插件加载失败
        """
        if plugin_names is None:
            # 从配置中获取插件列表
            plugin_names = self.config.get('plugins', [])
        
        loaded = []
        for plugin_spec in plugin_names:
            try:
                # 加载插件
                plugin = self.plugin_manager.load_plugin(plugin_spec)
                
                # 获取插件配置
                plugin_name, _ = parse_version_constraint(plugin_spec)
                plugin_config = self.config.get(plugin_name, {})
                
                # 使用插件管理器的initialize_plugin方法来确保状态一致性
                if plugin_config:
                    self.plugin_manager.initialize_plugin(plugin_name, plugin_config)
                else:
                    # 如果没有配置，也要确保状态正确
                    self.plugin_manager.initialize_plugin(plugin_name, {})
                
                loaded.append(plugin_name)
                logger.info(f"插件加载成功: {plugin_name}")
                
            except Exception as e:
                logger.error(f"插件加载失败 {plugin_spec}: {e}")
                raise PluginError(f"插件加载失败 {plugin_spec}: {e}") from e
        
        return loaded
    
    def get_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """获取插件实例
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            插件实例
            
        Raises:
            PluginError: 插件未找到
        """
        plugin = self.plugin_manager.get_plugin(plugin_name)
        if plugin is None:
            raise PluginError(f"插件未找到: {plugin_name}")
        return plugin
    
    def print_plugin_info(self, plugin_name: Optional[str] = None):
        """打印插件信息
        
        Args:
            plugin_name: 要打印信息的插件名称，如果为None则打印所有插件信息
        """
        if plugin_name:
            plugin = self.get_plugin(plugin_name)
            status = self.plugin_manager.get_plugin_status(plugin_name)
            print(f"插件名称: {plugin_name}")
            print(f"插件类型: {type(plugin).__name__}")
            print(f"插件状态: {status.state.name if status else 'unknown'}")
            if hasattr(plugin, 'get_info'):
                info = plugin.get_info()
                print(f"插件信息: {info}")
            print("-" * 50)
        else:
            print("已加载的插件:")
            print("=" * 50)
            for name in self.plugin_manager.list_loaded_plugins():
                plugin = self.get_plugin(name)
                status = self.plugin_manager.get_plugin_status(name)
                print(f"插件名称: {name}")
                print(f"插件类型: {type(plugin).__name__}")
                print(f"插件状态: {status.state.name if status else 'unknown'}")
                if hasattr(plugin, 'get_info'):
                    info = plugin.get_info()
                    print(f"插件信息: {info}")
                print("-" * 30)
    
    def execute_plugin_function(self, plugin_name: str, function_name: str, *args, **kwargs) -> Any:
        """执行插件功能
        
        Args:
            plugin_name: 插件名称
            function_name: 要执行的函数名称
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数执行结果
            
        Raises:
            PluginError: 插件功能执行失败
        """
        plugin = self.get_plugin(plugin_name)
        
        if not hasattr(plugin, function_name):
            raise PluginError(f"插件 {plugin_name} 没有函数 {function_name}")
        
        try:
            func = getattr(plugin, function_name)
            result = func(*args, **kwargs)
            logger.info(f"插件 {plugin_name} 函数 {function_name} 执行成功")
            return result
        except Exception as e:
            logger.error(f"插件 {plugin_name} 函数 {function_name} 执行失败: {e}")
            raise PluginError(f"插件功能执行失败: {e}") from e
    
    def destroy_plugin(self, plugin_name: str):
        """销毁插件实例
        
        Args:
            plugin_name: 要销毁的插件名称
        """
        self.plugin_manager.unload_plugin(plugin_name)
        logger.info(f"插件销毁成功: {plugin_name}")
    
    def destroy_all_plugins(self):
        """销毁所有插件实例"""
        self.plugin_manager.clear_all_plugins()
        logger.info("所有插件已销毁")
    
    def discover_available_plugins(self, refresh: bool = False) -> Dict[str, PluginInfo]:
        """发现可用插件
        
        Args:
            refresh: 是否刷新缓存
            
        Returns:
            可用插件信息字典
        """
        return self.plugin_manager.discover_plugins(refresh=refresh)

    def _initialize_plugins(self):
        """从配置初始化插件"""
        if not self.config:
            logger.info("无配置文件，跳过插件初始化")
            return
            
        plugins_config = self.config.get('plugins', [])
        auto_discover = self.config.get('auto_discover', True)
        
        if auto_discover and plugins_config:
            logger.info("自动发现并加载插件")
            self.scan_and_load_plugins()
        else:
            logger.info("自动发现插件已禁用或未配置插件")
    
    def execute_pipeline(self, plugin_sequence: List[str], **kwargs) -> Dict[str, Any]:
        """执行插件流水线
        
        Args:
            plugin_sequence: 插件执行顺序列表
            **kwargs: 执行参数
            
        Returns:
            各插件执行结果字典
        """
        results = {}
        current_context = kwargs.copy()
        
        for plugin_name in plugin_sequence:
            try:
                plugin = self.get_plugin(plugin_name)
                # 直接调用插件的start方法
                plugin_result = plugin.start(self, **current_context)
                results[plugin_name] = plugin_result
                
                # 将结果作为后续插件的输入上下文
                if isinstance(plugin_result, dict):
                    current_context.update(plugin_result)
                    
            except Exception as e:
                results[plugin_name] = {"error": str(e)}
                logger.error(f"插件 {plugin_name} 执行失败: {e}")
                # 可以选择继续执行或中断
                break
        
        return results
    
    def start_all_plugins(self, **kwargs) -> Dict[str, Any]:
        """启动所有已加载的插件
        
        Args:
            **kwargs: 执行参数
            
        Returns:
            所有插件执行结果
        """
        results = {}
        for plugin_name in self.list_loaded_plugins():
            try:
                plugin = self.get_plugin(plugin_name)
                plugin_result = plugin.start(self, **kwargs)
                results[plugin_name] = plugin_result
            except Exception as e:
                results[plugin_name] = {"error": str(e)}
                logger.error(f"插件 {plugin_name} 启动失败: {e}")
        
        return results
    
    def stop_all_plugins(self, **kwargs) -> None:
        """停止所有已加载的插件
        
        Args:
            **kwargs: 停止参数
        """
        for plugin_name in self.list_loaded_plugins():
            try:
                plugin = self.get_plugin(plugin_name)
                plugin.stop(**kwargs)
            except Exception as e:
                logger.error(f"插件 {plugin_name} 停止失败: {e}")
