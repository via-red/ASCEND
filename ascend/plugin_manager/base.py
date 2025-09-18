"""
ASCEND插件基础类
提供插件系统的核心抽象和基础实现
"""

from typing import Dict, Any, Optional, List, Type, TYPE_CHECKING

from pydantic import BaseModel, ValidationError as PydanticValidationError

from ascend.core.protocols import IPlugin
from ascend.core.types import PluginMetadata
from ascend.core.exceptions import PluginError

if TYPE_CHECKING:
    from ascend.plugin_manager.manager import IPluginRegistry

class BasePlugin(IPlugin):
    """插件基础实现类"""
    
    def __init__(self, name: str, version: str, description: str = "",
                 author: str = "", license: str = "Apache 2.0"):
        """
        初始化插件
        
        Args:
            name: 插件名称
            version: 插件版本
            description: 插件描述
            author: 作者
            license: 许可证
        """
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.license = license
        self.config: Optional[Dict[str, Any]] = None
        self._initialized = False
    
    def register(self, registry: 'IPluginRegistry') -> None:
        """注册插件到框架
        
        Args:
            registry: 插件注册表实例
            
        Raises:
            PluginError: 注册失败
        """
        # 基础实现，子类可以重写
        registry.register_plugin(self.name, self)
    
    def configure(self, config: Dict[str, Any]) -> None:
        """配置插件参数
        
        Args:
            config: 配置字典
            
        Raises:
            PluginError: 配置失败
        """
        self.config = config
        self._validate_config(config)
    
    def get_name(self) -> str:
        """获取插件名称
        
        Returns:
            插件名称
        """
        return self.name
    
    def get_version(self) -> str:
        """获取插件版本
        
        Returns:
            插件版本
        """
        return self.version
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取插件元数据
        
        Returns:
            元数据字典
        """
        return PluginMetadata(
            name=self.name,
            version=self.version,
            description=self.description,
            author=self.author,
            license=self.license,
            requires=self._get_required_plugins(),
            provides=self._get_provided_components(),
            compatible_with=self._get_compatible_versions()
        ).to_dict()

    def get_config_schema(self) -> Optional[Type[BaseModel]]:
        """获取插件配置的Pydantic模型（子类可重写）
        
        Returns:
            Pydantic BaseModel类或None
        """
        return None

    def initialize(self) -> None:
        """初始化插件
        
        Raises:
            PluginError: 初始化失败
        """
        if self._initialized:
            return
        
        try:
            self._initialize()
            self._initialized = True
        except Exception as e:
            raise PluginError(f"Failed to initialize plugin: {e}", self.name)
    
    def cleanup(self) -> None:
        """清理插件资源
        
        Raises:
            PluginError: 清理失败
        """
        if not self._initialized:
            return
        
        try:
            self._cleanup()
            self._initialized = False
        except Exception as e:
            raise PluginError(f"Failed to cleanup plugin: {e}", self.name)
    
    def is_initialized(self) -> bool:
        """检查插件是否已初始化
        
        Returns:
            是否已初始化
        """
        return self._initialized
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """验证插件配置
        
        Args:
            config: 配置字典
            
        Raises:
            PluginError: 配置验证失败
        """
        # 基础配置验证
        if not isinstance(config, dict):
            raise PluginError("Plugin config must be a dictionary", self.name)
        
        # 使用Pydantic模型进行验证
        schema = self.get_config_schema()
        if schema:
            try:
                schema.model_validate(config)
            except PydanticValidationError as e:
                raise PluginError(f"Configuration validation failed: {e}", self.name)

        # 子类可以重写此方法实现额外的自定义验证
        self._validate_custom_config(config)
    
    def _validate_custom_config(self, config: Dict[str, Any]) -> None:
        """验证自定义配置（子类重写）
        
        Args:
            config: 配置字典
        """
        pass
    
    def _initialize(self) -> None:
        """插件初始化逻辑（子类重写）"""
        pass
    
    def _cleanup(self) -> None:
        """插件清理逻辑（子类重写）"""
        pass
    
    def _get_required_plugins(self) -> List[str]:
        """获取依赖的插件列表（子类重写）
        
        Returns:
            依赖插件名称列表
        """
        return []
    
    def _get_provided_components(self) -> List[str]:
        """获取提供的组件列表（子类重写）
        
        Returns:
            提供的组件类型列表
        """
        return []
    
    def _get_compatible_versions(self) -> List[str]:
        """获取兼容的框架版本列表（子类重写）
        
        Returns:
            兼容版本列表
        """
        return ["0.1.0+"]  # 默认兼容0.1.0及以上版本
    
    def __str__(self) -> str:
        return f"Plugin(name={self.name}, version={self.version})"
    
    def __repr__(self) -> str:
        return f"BasePlugin(name={self.name}, version={self.version})"


class PluginRegistry:
    """插件注册表"""
    
    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}
        self._components: Dict[str, Dict[str, Any]] = {
            'agents': {},
            'environments': {},
            'policies': {},
            'models': {},
            'reward_functions': {},
            'feature_extractors': {},
            'monitors': {},
        }
    
    def register_plugin(self, plugin: BasePlugin) -> None:
        """注册插件
        
        Args:
            plugin: 插件实例
            
        Raises:
            PluginError: 插件已注册或注册失败
        """
        plugin_name = plugin.get_name()
        
        if plugin_name in self._plugins:
            raise PluginError(f"Plugin already registered", plugin_name)
        
        try:
            # 初始化插件
            plugin.initialize()
            
            # 注册插件
            self._plugins[plugin_name] = plugin
            
            # 注册插件提供的组件
            plugin.register(self)
            
        except Exception as e:
            raise PluginError(f"Failed to register plugin: {e}", plugin_name)
    
    def register_agent(self, name: str, agent_class: Any) -> None:
        """注册智能体组件
        
        Args:
            name: 组件名称
            agent_class: 智能体类
        """
        self._components['agents'][name] = agent_class
    
    def register_environment(self, name: str, env_class: Any) -> None:
        """注册环境组件
        
        Args:
            name: 组件名称
            env_class: 环境类
        """
        self._components['environments'][name] = env_class
    
    def register_policy(self, name: str, policy_class: Any) -> None:
        """注册策略组件
        
        Args:
            name: 组件名称
            policy_class: 策略类
        """
        self._components['policies'][name] = policy_class
    
    def register_model(self, name: str, model_class: Any) -> None:
        """注册模型组件
        
        Args:
            name: 组件名称
            model_class: 模型类
        """
        self._components['models'][name] = model_class
    
    def register_reward_function(self, name: str, reward_class: Any) -> None:
        """注册奖励函数组件
        
        Args:
            name: 组件名称
            reward_class: 奖励函数类
        """
        self._components['reward_functions'][name] = reward_class
    
    def register_feature_extractor(self, name: str, feature_class: Any) -> None:
        """注册特征提取器组件
        
        Args:
            name: 组件名称
            feature_class: 特征提取器类
        """
        self._components['feature_extractors'][name] = feature_class
    
    def register_monitor(self, name: str, monitor_class: Any) -> None:
        """注册监控器组件
        
        Args:
            name: 组件名称
            monitor_class: 监控器类
        """
        self._components['monitors'][name] = monitor_class
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """获取插件
        
        Args:
            name: 插件名称
            
        Returns:
            插件实例或None
        """
        return self._plugins.get(name)
    
    def get_component(self, component_type: str, name: str) -> Optional[Any]:
        """获取组件
        
        Args:
            component_type: 组件类型
            name: 组件名称
            
        Returns:
            组件类或None
        """
        return self._components.get(component_type, {}).get(name)
    
    def list_plugins(self) -> List[str]:
        """列出所有已注册的插件
        
        Returns:
            插件名称列表
        """
        return list(self._plugins.keys())
    
    def list_components(self, component_type: str) -> List[str]:
        """列出指定类型的所有组件
        
        Args:
            component_type: 组件类型
            
        Returns:
            组件名称列表
        """
        return list(self._components.get(component_type, {}).keys())
    
    def unregister_plugin(self, name: str) -> None:
        """注销插件
        
        Args:
            name: 插件名称
            
        Raises:
            PluginError: 插件未找到或注销失败
        """
        if name not in self._plugins:
            raise PluginError(f"Plugin not found", name)
        
        try:
            plugin = self._plugins[name]
            plugin.cleanup()
            del self._plugins[name]
        except Exception as e:
            raise PluginError(f"Failed to unregister plugin: {e}", name)
    
    def clear(self) -> None:
        """清除所有插件"""
        for plugin_name in list(self._plugins.keys()):
            try:
                self.unregister_plugin(plugin_name)
            except PluginError:
                # 忽略注销错误，继续清理其他插件
                pass
        
        # 清除所有组件
        for component_type in self._components:
            self._components[component_type].clear()
    
    def __contains__(self, name: str) -> bool:
        """检查插件是否已注册
        
        Args:
            name: 插件名称
            
        Returns:
            是否已注册
        """
        return name in self._plugins
    
    def __len__(self) -> int:
        """获取已注册插件数量
        
        Returns:
            插件数量
        """
        return len(self._plugins)


# 内置插件注册表
_builtin_plugins_registry: Dict[str, Type['BasePlugin']] = {}


def register_builtin_plugin(plugin_class: Type['BasePlugin']) -> Type['BasePlugin']:
    """装饰器：注册内置插件类
    
    Args:
        plugin_class: 插件类
        
    Returns:
        装饰后的插件类
    """
    # 创建实例以获取元数据 - 延迟实例化，避免循环引用
    # 这里不能直接实例化，因为插件类可能还没有完全初始化
    # 将插件类注册到内置插件注册表，实例化推迟到实际使用时
    _builtin_plugins_registry[plugin_class.__name__] = plugin_class
    return plugin_class


def get_builtin_plugins() -> Dict[str, Type['BasePlugin']]:
    """获取所有已注册的内置插件
    
    Returns:
        内置插件类字典
    """
    return _builtin_plugins_registry.copy()