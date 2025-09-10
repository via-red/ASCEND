"""
ASCEND配置加载器
提供配置文件的加载、解析和验证功能
"""

import os
from typing import Dict, Any, Optional, List
from pathlib import Path

from ascend.core.exceptions import ConfigError, ValidationError
from ascend.core.types import Config
from .parser import ConfigParser, default_parser
from .validator import ConfigValidator, default_validator

class ConfigLoader:
    """配置加载器类"""
    
    def __init__(self, parser: Optional[ConfigParser] = None, 
                 validator: Optional[ConfigValidator] = None):
        """
        初始化配置加载器
        
        Args:
            parser: 配置解析器实例（可选）
            validator: 配置验证器实例（可选）
        """
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
            
            raise ValidationError(error_msg)
        
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