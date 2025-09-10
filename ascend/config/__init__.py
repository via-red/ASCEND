"""
ASCEND配置模块
提供配置文件的加载、解析、验证和管理功能
"""

from .parser import ConfigParser, default_parser
from .validator import ConfigValidator, default_validator
from .loader import ConfigLoader, default_loader

from ascend.core.types import Config
from ascend.core.exceptions import ConfigError, ValidationError

__all__ = [
    # 类
    'ConfigParser',
    'ConfigValidator',
    'ConfigLoader',
    
    # 实例
    'default_parser',
    'default_validator',
    'default_loader',
    
    # 类型
    'Config',
    
    # 异常
    'ConfigError',
    'ValidationError',
]

# 导出常用函数
def load_config(config_path: str, validate: bool = True) -> Config:
    """快速加载配置文件的便捷函数
    
    Args:
        config_path: 配置文件路径
        validate: 是否验证配置
        
    Returns:
        加载的配置字典
        
    Raises:
        ConfigError: 配置加载失败
        ValidationError: 配置验证失败
    """
    return default_loader.load(config_path, validate=validate)


def validate_config(config: Config) -> bool:
    """快速验证配置的便捷函数
    
    Args:
        config: 配置字典
        
    Returns:
        是否验证通过
        
    Raises:
        ValidationError: 配置验证失败
    """
    return default_validator.validate(config, strict=True)


def create_default_config() -> Config:
    """创建默认配置的便捷函数
    
    Returns:
        默认配置字典
    """
    return default_loader.create_default_config()


def save_config(config: Config, config_path: str) -> None:
    """保存配置到文件的便捷函数
    
    Args:
        config: 配置字典
        config_path: 保存路径
        
    Raises:
        ConfigError: 保存失败
    """
    default_parser.save(config, config_path)