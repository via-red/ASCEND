"""
ASCEND配置解析器
支持YAML、JSON格式配置，环境变量解析和配置验证
"""

import yaml
import json
import os
import re
from typing import Dict, Any, Optional
from pathlib import Path

from ascend.core.exceptions import ConfigError, ValidationError
from ascend.core.types import Config

class ConfigParser:
    """配置解析器类"""
    
    def __init__(self):
        self.supported_formats = {'.yaml', '.yml', '.json'}
        self.env_var_pattern = re.compile(r'\$\{([^}]+)\}')
    
    def load(self, config_path: str) -> Config:
        """加载并解析配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            解析后的配置字典
            
        Raises:
            ConfigError: 配置文件格式不支持或解析失败
        """
        path = Path(config_path)
        
        # 检查文件格式支持
        if path.suffix not in self.supported_formats:
            raise ConfigError(
                f"Unsupported config format: {path.suffix}. "
                f"Supported formats: {', '.join(self.supported_formats)}",
                config_path=str(path)
            )
        
        # 检查文件是否存在
        if not path.exists():
            raise ConfigError(f"Config file not found", config_path=str(path))
        
        try:
            # 读取文件内容
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix in {'.yaml', '.yml'}:
                    config = yaml.safe_load(f)
                else:
                    config = json.load(f)
            
            # 解析环境变量
            config = self._resolve_env_vars(config)
            
            # 验证配置基础结构
            self._validate_basic_structure(config)
            
            return config
            
        except yaml.YAMLError as e:
            raise ConfigError(f"YAML parsing error: {e}", config_path=str(path))
        except json.JSONDecodeError as e:
            raise ConfigError(f"JSON parsing error: {e}", config_path=str(path))
        except Exception as e:
            raise ConfigError(f"Failed to load config: {e}", config_path=str(path))
    
    def _resolve_env_vars(self, config: Any) -> Any:
        """递归解析配置中的环境变量
        
        Args:
            config: 配置数据
            
        Returns:
            解析环境变量后的配置数据
        """
        if isinstance(config, dict):
            return {k: self._resolve_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._resolve_env_vars(item) for item in config]
        elif isinstance(config, str):
            return self._resolve_env_var_string(config)
        else:
            return config
    
    def _resolve_env_var_string(self, value: str) -> Any:
        """解析字符串中的环境变量
        
        Args:
            value: 可能包含环境变量的字符串
            
        Returns:
            解析后的值
        """
        # 检查是否是环境变量引用格式 ${VAR_NAME}
        match = self.env_var_pattern.search(value)
        if not match:
            return value
        
        env_var_name = match.group(1)
        
        # 获取环境变量值
        env_value = os.environ.get(env_var_name)
        
        if env_value is None:
            # 如果环境变量不存在，保持原样（可能是可选变量）
            return value
        
        # 替换环境变量引用
        resolved_value = self.env_var_pattern.sub(env_value, value)
        
        # 尝试转换为适当的数据类型
        try:
            # 尝试转换为数字
            if resolved_value.isdigit():
                return int(resolved_value)
            elif resolved_value.replace('.', '', 1).isdigit():
                return float(resolved_value)
            # 尝试转换为布尔值
            elif resolved_value.lower() in ('true', 'false'):
                return resolved_value.lower() == 'true'
            # 尝试转换为None
            elif resolved_value.lower() == 'null':
                return None
            else:
                return resolved_value
        except (ValueError, AttributeError):
            return resolved_value
    
    def _validate_basic_structure(self, config: Config) -> None:
        """验证配置基础结构
        
        Args:
            config: 配置字典
            
        Raises:
            ValidationError: 配置结构验证失败
        """
        if not isinstance(config, dict):
            raise ValidationError("Config must be a dictionary")
        
        # 检查必需的基础字段（支持嵌套在ascend层级下）
        if 'version' not in config and ('ascend' not in config or 'version' not in config.get('ascend', {})):
            raise ValidationError("Missing required field: version", "version")
        
        if 'framework' not in config and ('ascend' not in config or 'framework' not in config.get('ascend', {})):
            raise ValidationError("Missing required field: framework", "framework")
        
        # 验证版本格式
        version = config.get('version')
        if version is None and 'ascend' in config:
            version = config['ascend'].get('version')
        
        if not isinstance(version, str) or not version:
            raise ValidationError("Version must be a non-empty string", "version")
    
    def merge(self, base_config: Config, override_config: Config) -> Config:
        """深度合并两个配置字典
        
        Args:
            base_config: 基础配置
            override_config: 覆盖配置
            
        Returns:
            合并后的配置字典
        """
        result = base_config.copy()
        
        for key, value in override_config.items():
            if (key in result and 
                isinstance(result[key], dict) and 
                isinstance(value, dict)):
                # 递归合并字典
                result[key] = self.merge(result[key], value)
            else:
                # 直接覆盖或添加新字段
                result[key] = value
        
        return result
    
    def save(self, config: Config, config_path: str) -> None:
        """保存配置到文件
        
        Args:
            config: 配置字典
            config_path: 保存路径
            
        Raises:
            ConfigError: 保存失败
        """
        path = Path(config_path)
        
        try:
            # 确保目录存在
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                if path.suffix in {'.yaml', '.yml'}:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            raise ConfigError(f"Failed to save config: {e}", config_path=str(path))
    
    def validate(self, config: Config, schema: Optional[Dict] = None) -> bool:
        """验证配置是否符合模式
        
        Args:
            config: 配置字典
            schema: 验证模式（可选）
            
        Returns:
            是否验证通过
            
        Note:
            完整的模式验证将在后续版本实现
        """
        # 基础验证
        try:
            self._validate_basic_structure(config)
            return True
        except ValidationError:
            return False
    
    def load_from_string(self, config_str: str, format: str = 'yaml') -> Config:
        """从字符串加载配置
        
        Args:
            config_str: 配置字符串
            format: 格式类型 ('yaml' 或 'json')
            
        Returns:
            解析后的配置字典
            
        Raises:
            ConfigError: 解析失败
        """
        try:
            if format.lower() in {'yaml', 'yml'}:
                config = yaml.safe_load(config_str)
            elif format.lower() == 'json':
                config = json.loads(config_str)
            else:
                raise ConfigError(f"Unsupported format: {format}")
            
            config = self._resolve_env_vars(config)
            self._validate_basic_structure(config)
            
            return config
            
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ConfigError(f"Failed to parse config string: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to load config from string: {e}")


# 创建默认配置解析器实例
default_parser = ConfigParser()