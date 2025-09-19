"""
ASCEND配置加载器
提供配置文件的加载、解析和验证功能。支持以下特性：
- YAML 配置文件的加载和解析
- 配置模式验证
- 环境变量替换
- 默认值处理
- 配置合并
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional, List, Union, Type
from pathlib import Path
from pydantic import BaseModel

from ..core.exceptions import ConfigError, ValidationError

logger = logging.getLogger(__name__)

class BaseConfigLoader:
    """配置加载器
    
    负责加载、解析和验证配置文件。
    
    Attributes:
        config_paths: 配置文件搜索路径
        default_config: 默认配置
        env_prefix: 环境变量前缀
    """
    
    def __init__(
        self, 
        config_paths: Optional[List[str]] = None,
        default_config: Optional[Dict[str, Any]] = None,
        env_prefix: str = "ASCEND_"
    ) -> None:
        """初始化配置加载器
        
        Args:
            config_paths: 配置文件搜索路径列表
            default_config: 默认配置字典
            env_prefix: 环境变量前缀
        """
        self.config_paths = config_paths or []
        self.default_config = default_config or {}
        self.env_prefix = env_prefix
        self._add_default_paths()
    
    def _add_default_paths(self) -> None:
        """添加默认的配置文件搜索路径"""
        # 添加当前目录
        self.config_paths.append(os.getcwd())
        
        # 添加用户配置目录
        user_config = Path.home() / ".ascend" / "config"
        if user_config.exists():
            self.config_paths.append(str(user_config))
        
        # 添加系统配置目录
        if os.name == "posix":
            if Path("/etc/ascend").exists():
                self.config_paths.append("/etc/ascend")
    
    def load_config(
        self,
        config_file: Optional[str] = None,
        schema: Optional[Type[BaseModel]] = None
    ) -> Dict[str, Any]:
        """加载配置文件
        
        Args:
            config_file: 配置文件路径，如果为None则搜索默认路径
            schema: 配置模式类
            
        Returns:
            配置字典
            
        Raises:
            ConfigError: 配置加载或验证失败
        """
        # 查找配置文件
        config_path = self._find_config_file(config_file)
        logger.debug(f"Searching for config file: {config_file}")
        logger.debug(f"Search paths: {self.config_paths}")
        if not config_path:
            raise ConfigError(f"Config file {config_file} not found in search paths: {self.config_paths}")
        
        try:
            # 加载YAML文件
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 合并默认配置
            config = self._merge_configs(self.default_config, config)
            
            # 处理环境变量
            config = self._process_env_vars(config)
            
            # 验证配置
            if schema:
                try:
                    validated = schema(**config)
                    config = validated.dict()
                except ValidationError as e:
                    raise ConfigError(f"Config validation failed: {str(e)}", config_path=str(config_path))
            
            return config
            
        except Exception as e:
            raise ConfigError(f"Failed to load config file {config_path}: {e}")
    
    def _find_config_file(self, config_file: Optional[str] = None) -> Optional[Path]:
        """查找配置文件
        
        Args:
            config_file: 配置文件路径
            
        Returns:
            配置文件路径，如果未找到则返回None
        """
        if config_file:
            # 首先尝试将config_file作为绝对路径
            path = Path(config_file)
            if path.exists():
                return path
                
            # 然后在每个搜索路径中查找
            for search_path in self.config_paths:
                path = Path(search_path) / config_file
                if path.exists():
                    return path
        else:
            # 在搜索路径中查找默认配置文件
            for path in self.config_paths:
                for name in ["config.yaml", "config.yml"]:
                    config_path = Path(path) / name
                    if config_path.exists():
                        return config_path
        
        return None
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """合并配置字典
        
        Args:
            base: 基础配置
            override: 覆盖配置
            
        Returns:
            合并后的配置
        """
        result = base.copy()
        for key, value in override.items():
            # 如果两个都是字典则递归合并
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _process_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理环境变量
        
        将配置中的环境变量引用替换为实际值。
        支持的格式: ${ENV_VAR} 或 ${ENV_VAR:default}
        
        Args:
            config: 配置字典
            
        Returns:
            处理后的配置
        """
        def _process_value(value: Any) -> Any:
            if isinstance(value, str):
                # 处理环境变量引用
                if value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    if ":" in env_var:
                        env_var, default = env_var.split(":", 1)
                    else:
                        default = None
                    
                    env_var = self.env_prefix + env_var
                    return os.environ.get(env_var, default)
                return value
            elif isinstance(value, dict):
                return {k: _process_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_process_value(v) for v in value]
            return value
        
        return _process_value(config)
    
    def save_config(self, config: Dict[str, Any], file_path: str) -> None:
        """保存配置到文件
        
        Args:
            config: 配置字典
            file_path: 保存路径
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config, f, default_flow_style=False)
                
            logger.info(f"Saved config to {file_path}")
            
        except Exception as e:
            raise ConfigError(f"Failed to save config to {file_path}: {e}")
    
    def validate_config(
        self, 
        config: Dict[str, Any],
        schema: Type[BaseModel]
    ) -> Dict[str, Any]:
        """验证配置
        
        Args:
            config: 配置字典
            schema: 配置模式类
            
        Returns:
            验证后的配置
            
        Raises:
            ConfigError: 验证失败
        """
        try:
            validated = schema(**config)
            return validated.dict()
        except ValidationError as e:
            raise ConfigError(f"Config validation failed: {e}")
from ascend.core.types import Config
from .parser import ConfigParser, default_parser
from .validator import ConfigValidator, default_validator

class ConfigLoader(BaseConfigLoader):
    """配置加载器类"""
    
    def __init__(self, config_paths: Optional[List[str]] = None, 
                 parser: Optional[ConfigParser] = None,
                 validator: Optional[ConfigValidator] = None):
        """
        初始化配置加载器
        
        Args:
            config_paths: 配置文件搜索路径列表
            parser: 配置解析器实例（可选）
            validator: 配置验证器实例（可选）
        """
        super().__init__(config_paths=config_paths)
        self.parser = parser or default_parser
        self.validator = validator or default_validator
        self._config_cache: Dict[str, Config] = {}
    
    def load(self, config_path: str, validate: bool = True, 
             cache: bool = True) -> Config:
        """加载配置文件
        
        Args:
            config_path: 配置文件路径
            validate: 是否验证配置
            cache: 是否缓存配置
            
        Returns:
            加载的配置字典
            
        Raises:
            ConfigError: 配置加载或验证失败
        """
        config_path = os.path.abspath(config_path)
        
        # 检查缓存
        if cache and config_path in self._config_cache:
            return self._config_cache[config_path].copy()
        
        try:
            # 加载配置
            config = self.parser.load(config_path)
            
            # 处理配置继承
            config = self._process_inheritance(config, config_path)
            
            # 验证配置
            if validate:
                self.validate(config, config_path)
            
            # 缓存配置
            if cache:
                self._config_cache[config_path] = config.copy()
            
            return config
            
        except Exception as e:
            raise ConfigError(f"Failed to load config: {e}", config_path)
    
    def _process_inheritance(self, config: Config, config_path: str) -> Config:
        """处理配置继承
        
        Args:
            config: 原始配置
            config_path: 配置文件路径
            
        Returns:
            处理继承后的配置
        """
        if '_extends' in config:
            base_config_path = config['_extends']
            
            # 解析基础配置文件路径
            if not os.path.isabs(base_config_path):
                base_config_path = os.path.join(
                    os.path.dirname(config_path), base_config_path
                )
            
            # 加载基础配置
            base_config = self.load(base_config_path, validate=False, cache=True)
            
            # 合并配置（当前配置覆盖基础配置）
            merged_config = self.parser.merge(base_config, config)
            
            # 移除继承标记
            if '_extends' in merged_config:
                del merged_config['_extends']
            
            return merged_config
        
        return config
    
    def validate(self, config: Config, config_path: Optional[str] = None) -> bool:
        """验证配置
        
        Args:
            config: 配置字典
            config_path: 配置文件路径（用于错误信息）
            
        Returns:
            是否验证通过
            
        Raises:
            ValidationError: 配置验证失败
        """
        is_valid = self.validator.validate(config, strict=False)
        
        if not is_valid:
            errors = self.validator.get_errors()
            warnings = self.validator.get_warnings()
            
            error_msg = f"Config validation failed"
            if config_path:
                error_msg += f" for {config_path}"
            
            error_msg += f"\nErrors: {len(errors)}, Warnings: {len(warnings)}"
            
            if errors:
                error_msg += "\n\nErrors:\n- " + "\n- ".join(errors)
            if warnings:
                error_msg += "\n\nWarnings:\n- " + "\n- ".join(warnings)
            
            raise ValidationError(error_msg, "configuration")
        
        return True
    
    def load_from_string(self, config_str: str, format: str = 'yaml', 
                        validate: bool = True) -> Config:
        """从字符串加载配置
        
        Args:
            config_str: 配置字符串
            format: 格式类型 ('yaml' 或 'json')
            validate: 是否验证配置
            
        Returns:
            加载的配置字典
            
        Raises:
            ConfigError: 配置加载或验证失败
        """
        try:
            config = self.parser.load_from_string(config_str, format)
            
            if validate:
                self.validate(config)
            
            return config
            
        except Exception as e:
            raise ConfigError(f"Failed to load config from string: {e}")
    
    def create_default_config(self) -> Config:
        """创建默认配置
        
        Returns:
            默认配置字典
        """
        return {
            'version': '1.0.0',
            'framework': 'ascend',
            'plugin_paths': [
                './plugins',
                '${HOME}/.ascend/plugins',
                '/opt/ascend/plugins'
            ],
            'agent': {
                'type': 'base_agent',
                'config': {
                    'learning_rate': 0.001,
                    'batch_size': 64
                }
            },
            'environment': {
                'type': 'base_environment',
                'config': {
                    'max_steps': 1000
                }
            },
            'training': {
                'total_timesteps': 100000,
                'eval_freq': 10000,
                'save_freq': 50000,
                'log_dir': './logs',
                'checkpoint_dir': './checkpoints'
            },
            'plugins': []
        }
    
    def save_default_config(self, config_path: str) -> None:
        """保存默认配置到文件
        
        Args:
            config_path: 保存路径
            
        Raises:
            ConfigError: 保存失败
        """
        default_config = self.create_default_config()
        self.parser.save(default_config, config_path)
    
    def clear_cache(self) -> None:
        """清除配置缓存"""
        self._config_cache.clear()
    
    def get_cached_configs(self) -> Dict[str, Config]:
        """获取所有缓存的配置
        
        Returns:
            缓存配置字典
        """
        return self._config_cache.copy()
    
    def get_validation_results(self) -> Dict[str, List[str]]:
        """获取最后一次验证的结果
        
        Returns:
            包含错误和警告的字典
        """
        return {
            'errors': self.validator.get_errors(),
            'warnings': self.validator.get_warnings()
        }
    
    def reload(self, config_path: str, validate: bool = True) -> Config:
        """重新加载配置文件（忽略缓存）
        
        Args:
            config_path: 配置文件路径
            validate: 是否验证配置
            
        Returns:
            重新加载的配置字典
            
        Raises:
            ConfigError: 配置加载或验证失败
        """
        # 从缓存中移除（如果存在）
        if config_path in self._config_cache:
            del self._config_cache[config_path]
        
        return self.load(config_path, validate=validate, cache=True)


# 创建默认配置加载器实例
default_loader = ConfigLoader()