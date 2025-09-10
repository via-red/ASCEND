"""
ASCEND框架异常类定义
提供框架中使用的自定义异常类型
"""

from typing import Optional

class AscendError(Exception):
    """ASCEND框架基础异常类"""
    
    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code
        super().__init__(message)
    
    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message


class ConfigError(AscendError):
    """配置相关异常"""
    
    def __init__(self, message: str, config_path: Optional[str] = None):
        self.config_path = config_path
        code = "CONFIG_ERROR"
        if config_path:
            message = f"{message} (config: {config_path})"
        super().__init__(message, code)


class ValidationError(AscendError):
    """数据验证异常"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        code = "VALIDATION_ERROR"
        if field:
            message = f"Field '{field}': {message}"
        super().__init__(message, code)


class PluginError(AscendError):
    """插件相关异常"""
    
    def __init__(self, message: str, plugin_name: Optional[str] = None):
        self.plugin_name = plugin_name
        code = "PLUGIN_ERROR"
        if plugin_name:
            message = f"Plugin '{plugin_name}': {message}"
        super().__init__(message, code)


class PluginNotFoundError(PluginError):
    """插件未找到异常"""
    
    def __init__(self, plugin_name: str):
        message = f"Plugin not found"
        super().__init__(message, plugin_name)
        self.code = "PLUGIN_NOT_FOUND"


class PluginLoadError(PluginError):
    """插件加载异常"""
    
    def __init__(self, plugin_name: str, reason: str):
        message = f"Failed to load plugin: {reason}"
        super().__init__(message, plugin_name)
        self.code = "PLUGIN_LOAD_ERROR"


class PluginCompatibilityError(PluginError):
    """插件兼容性异常"""
    
    def __init__(self, plugin_name: str, required_version: str, actual_version: str):
        message = f"Version compatibility error: requires {required_version}, got {actual_version}"
        super().__init__(message, plugin_name)
        self.code = "PLUGIN_COMPATIBILITY_ERROR"


class ComponentError(AscendError):
    """组件相关异常"""
    
    def __init__(self, message: str, component_type: Optional[str] = None, 
                 component_name: Optional[str] = None):
        self.component_type = component_type
        self.component_name = component_name
        code = "COMPONENT_ERROR"
        
        parts = []
        if component_type:
            parts.append(f"type: {component_type}")
        if component_name:
            parts.append(f"name: {component_name}")
        
        if parts:
            message = f"{message} ({', '.join(parts)})"
        
        super().__init__(message, code)


class ComponentNotFoundError(ComponentError):
    """组件未找到异常"""
    
    def __init__(self, component_type: str, component_name: str):
        message = f"Component not found"
        super().__init__(message, component_type, component_name)
        self.code = "COMPONENT_NOT_FOUND"


class ComponentInitializationError(ComponentError):
    """组件初始化异常"""
    
    def __init__(self, component_type: str, component_name: str, reason: str):
        message = f"Failed to initialize component: {reason}"
        super().__init__(message, component_type, component_name)
        self.code = "COMPONENT_INIT_ERROR"


class TrainingError(AscendError):
    """训练相关异常"""
    
    def __init__(self, message: str, step: Optional[int] = None, 
                 episode: Optional[int] = None):
        self.step = step
        self.episode = episode
        code = "TRAINING_ERROR"
        
        parts = []
        if step is not None:
            parts.append(f"step: {step}")
        if episode is not None:
            parts.append(f"episode: {episode}")
        
        if parts:
            message = f"{message} ({', '.join(parts)})"
        
        super().__init__(message, code)


class EnvironmentError(AscendError):
    """环境相关异常"""
    
    def __init__(self, message: str, env_name: Optional[str] = None):
        self.env_name = env_name
        code = "ENVIRONMENT_ERROR"
        if env_name:
            message = f"Environment '{env_name}': {message}"
        super().__init__(message, code)


class ModelError(AscendError):
    """模型相关异常"""
    
    def __init__(self, message: str, model_name: Optional[str] = None):
        self.model_name = model_name
        code = "MODEL_ERROR"
        if model_name:
            message = f"Model '{model_name}': {message}"
        super().__init__(message, code)


class SerializationError(AscendError):
    """序列化相关异常"""
    
    def __init__(self, message: str, file_path: Optional[str] = None):
        self.file_path = file_path
        code = "SERIALIZATION_ERROR"
        if file_path:
            message = f"{message} (file: {file_path})"
        super().__init__(message, code)


class NetworkError(AscendError):
    """网络相关异常"""
    
    def __init__(self, message: str, url: Optional[str] = None):
        self.url = url
        code = "NETWORK_ERROR"
        if url:
            message = f"{message} (url: {url})"
        super().__init__(message, code)


class TimeoutError(AscendError):
    """超时异常"""
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None):
        self.timeout_seconds = timeout_seconds
        code = "TIMEOUT_ERROR"
        if timeout_seconds:
            message = f"{message} (timeout: {timeout_seconds}s)"
        super().__init__(message, code)


class ResourceExhaustedError(AscendError):
    """资源耗尽异常"""
    
    def __init__(self, message: str, resource_type: Optional[str] = None):
        self.resource_type = resource_type
        code = "RESOURCE_EXHAUSTED"
        if resource_type:
            message = f"{resource_type} resource exhausted: {message}"
        super().__init__(message, code)


class NotImplementedError(AscendError):
    """功能未实现异常"""
    
    def __init__(self, feature: str):
        message = f"Feature '{feature}' is not implemented yet"
        super().__init__(message, "NOT_IMPLEMENTED")
        self.feature = feature


class DeprecationWarningError(AscendError):
    """功能已弃用警告"""
    
    def __init__(self, feature: str, alternative: Optional[str] = None):
        message = f"Feature '{feature}' is deprecated"
        if alternative:
            message += f", use '{alternative}' instead"
        super().__init__(message, "DEPRECATION_WARNING")
        self.feature = feature
        self.alternative = alternative