"""
ASCEND配置验证器
提供配置数据的验证和完整性检查。支持以下特性：
- 类型检查
- 值范围验证
- 必需字段验证
- 格式验证
- 自定义验证规则
"""

import re
import logging
from typing import Dict, Any, List, Optional, Set, Callable, Union
from pathlib import Path
from pydantic import BaseModel, validator, Field

from ..core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class RangeValidator:
    """范围验证器"""
    
    @staticmethod
    def validate_range(
        value: Union[int, float],
        min_val: Optional[Union[int, float]] = None,
        max_val: Optional[Union[int, float]] = None,
        inclusive: bool = True
    ) -> bool:
        """验证值是否在指定范围内
        
        Args:
            value: 要验证的值
            min_val: 最小值
            max_val: 最大值
            inclusive: 是否包含边界值
            
        Returns:
            是否有效
        """
        if min_val is not None:
            if inclusive:
                if value < min_val:
                    return False
            else:
                if value <= min_val:
                    return False
                
        if max_val is not None:
            if inclusive:
                if value > max_val:
                    return False
            else:
                if value >= max_val:
                    return False
                
        return True

class FormatValidator:
    """格式验证器"""
    
    @staticmethod
    def validate_regex(value: str, pattern: str) -> bool:
        """验证字符串是否匹配正则表达式
        
        Args:
            value: 要验证的字符串
            pattern: 正则表达式
            
        Returns:
            是否匹配
        """
        return bool(re.match(pattern, value))
    
    @staticmethod
    def validate_file_path(path: str, must_exist: bool = True) -> bool:
        """验证文件路径
        
        Args:
            path: 文件路径
            must_exist: 文件是否必须存在
            
        Returns:
            是否有效
        """
        try:
            path_obj = Path(path)
            return not must_exist or path_obj.exists()
        except:
            return False
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """验证URL格式
        
        Args:
            url: URL字符串
            
        Returns:
            是否有效
        """
        pattern = r'^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$'
        return bool(re.match(pattern, url))

class ConfigValidator:
    """配置验证器
    
    提供配置数据的验证功能。
    
    Attributes:
        schema: 配置模式
        custom_validators: 自定义验证器
    """
    
    def __init__(self, schema: Optional[BaseModel] = None) -> None:
        """初始化验证器
        
        Args:
            schema: 配置模式
        """
        self.schema = schema
        self.custom_validators: Dict[str, List[Callable]] = {}
        
    def add_validator(self, field: str, validator_func: Callable) -> None:
        """添加自定义验证器
        
        Args:
            field: 字段名
            validator_func: 验证函数
        """
        if field not in self.custom_validators:
            self.custom_validators[field] = []
        self.custom_validators[field].append(validator_func)
        
    def validate(self, config: Dict[str, Any]) -> None:
        """验证配置数据
        
        Args:
            config: 配置字典
            
        Raises:
            ValidationError: 验证失败
        """
        # 使用模式验证
        if self.schema:
            try:
                self.schema(**config)
            except Exception as e:
                raise ValidationError(f"Schema validation failed: {e}")
        
        # 应用自定义验证器
        for field, validators in self.custom_validators.items():
            if field in config:
                value = config[field]
                for validator_func in validators:
                    try:
                        if not validator_func(value):
                            raise ValidationError(
                                f"Validation failed for field {field}"
                            )
                    except Exception as e:
                        raise ValidationError(
                            f"Validation error for field {field}: {e}"
                        )
    
    def validate_required_fields(
        self,
        config: Dict[str, Any],
        required_fields: Set[str]
    ) -> None:
        """验证必需字段
        
        Args:
            config: 配置字典
            required_fields: 必需字段集合
            
        Raises:
            ValidationError: 缺少必需字段
        """
        missing = required_fields - set(config.keys())
        if missing:
            raise ValidationError(f"Missing required fields: {missing}")
    
    def validate_field_types(
        self,
        config: Dict[str, Any],
        type_mapping: Dict[str, type]
    ) -> None:
        """验证字段类型
        
        Args:
            config: 配置字典
            type_mapping: 字段类型映射
            
        Raises:
            ValidationError: 字段类型不匹配
        """
        for field, expected_type in type_mapping.items():
            if field in config:
                value = config[field]
                if not isinstance(value, expected_type):
                    raise ValidationError(
                        f"Field {field} should be of type {expected_type.__name__}"
                    )
    
    def validate_field_values(
        self,
        config: Dict[str, Any],
        value_constraints: Dict[str, Dict[str, Any]]
    ) -> None:
        """验证字段值
        
        Args:
            config: 配置字典
            value_constraints: 值约束字典
            
        Raises:
            ValidationError: 值验证失败
        """
        for field, constraints in value_constraints.items():
            if field in config:
                value = config[field]
                
                # 范围检查
                if 'range' in constraints:
                    range_spec = constraints['range']
                    if not RangeValidator.validate_range(
                        value,
                        range_spec.get('min'),
                        range_spec.get('max'),
                        range_spec.get('inclusive', True)
                    ):
                        raise ValidationError(
                            f"Value of field {field} is out of range"
                        )
                
                # 格式检查
                if 'format' in constraints:
                    format_spec = constraints['format']
                    if 'regex' in format_spec:
                        if not FormatValidator.validate_regex(
                            str(value),
                            format_spec['regex']
                        ):
                            raise ValidationError(
                                f"Value of field {field} has invalid format"
                            )
from ascend.core.types import Config, ComponentType

class ConfigValidator:
    """配置验证器类"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self, config: Config, strict: bool = True) -> bool:
        """验证配置完整性
        
        Args:
            config: 配置字典
            strict: 是否严格模式（发现错误立即停止）
            
        Returns:
            是否验证通过
        """
        self.errors.clear()
        self.warnings.clear()
        
        try:
            # 基础结构验证
            self._validate_basic_structure(config)
            
            # 插件依赖验证
            self._validate_plugin_dependencies(config)
            
            # 路径验证
            self._validate_paths(config)
            
            # 注意：详细的字段级验证和组件验证逻辑已被移除，
            # 将由插件自身的Pydantic模型处理。
            # 此处可以保留一些全局级别的或跨插件的验证规则。
            
            return len(self.errors) == 0
            
        except ValidationError as e:
            if strict:
                # 重新抛出ValidationError，但确保参数正确
                raise ValidationError(str(e))
            self.errors.append(str(e))
            return False
    
    def _validate_basic_structure(self, config: Config) -> None:
        """验证配置基础结构"""
        if not isinstance(config, dict):
            raise ValidationError("Config must be a dictionary")
        
        # 注释掉对必需部分的检查，允许配置不包含这些部分
        # required_sections = ['agent', 'environment', 'training']
        # for section in required_sections:
        #     if section not in config:
        #         raise ValidationError(f"Missing required section: {section}", section)
    
    def _validate_fields(self, config: Config, rules: Dict[str, Dict], 
                        prefix: str = '') -> None:
        """递归验证字段规则"""
        for field_path, field_rules in rules.items():
            full_path = f"{prefix}.{field_path}" if prefix else field_path
            value = self._get_nested_value(config, field_path)
            
            # 检查必填字段
            if field_rules.get('required', False) and value is None:
                self.errors.append(f"Missing required field: {full_path}")
                continue
            
            if value is not None:
                # 类型验证
                self._validate_type(value, field_rules, full_path)
                
                # 值范围验证
                self._validate_value_range(value, field_rules, full_path)
                
                # 模式验证（字符串）
                self._validate_pattern(value, field_rules, full_path)
    
    def _validate_type(self, value: Any, rules: Dict[str, Any], field_path: str) -> None:
        """验证字段类型"""
        expected_type = rules.get('type')
        if not expected_type:
            return
        
        type_map = {
            'string': str,
            'integer': int,
            'number': (int, float),
            'boolean': bool,
            'dict': dict,
            'list': list,
            'array': list
        }
        
        expected_types = type_map.get(expected_type)
        if expected_types and not isinstance(value, expected_types):
            self.errors.append(
                f"Field {field_path}: expected {expected_type}, got {type(value).__name__}"
            )
    
    def _validate_value_range(self, value: Any, rules: Dict[str, Any], field_path: str) -> None:
        """验证值范围"""
        if isinstance(value, (int, float)):
            if 'min' in rules and value < rules['min']:
                self.errors.append(
                    f"Field {field_path}: value {value} is less than minimum {rules['min']}"
                )
            if 'max' in rules and value > rules['max']:
                self.errors.append(
                    f"Field {field_path}: value {value} is greater than maximum {rules['max']}"
                )
        
        elif isinstance(value, str):
            if 'min_length' in rules and len(value) < rules['min_length']:
                self.errors.append(
                    f"Field {field_path}: length {len(value)} is less than minimum {rules['min_length']}"
                )
            if 'max_length' in rules and len(value) > rules['max_length']:
                self.errors.append(
                    f"Field {field_path}: length {len(value)} is greater than maximum {rules['max_length']}"
                )
    
    def _validate_pattern(self, value: Any, rules: Dict[str, Any], field_path: str) -> None:
        """验证字符串模式"""
        if isinstance(value, str) and 'pattern' in rules:
            pattern = rules['pattern']
            if not re.match(pattern, value):
                self.errors.append(
                    f"Field {field_path}: value '{value}' does not match pattern '{pattern}'"
                )
    
    def _validate_components(self, config: Config) -> None:
        """验证组件配置"""
        component_sections = ['agent', 'environment', 'models', 'rewards']
        
        for section in component_sections:
            if section in config:
                component_config = config[section]
                
                # 处理嵌套的组件配置（如models.llm, models.vision）
                if isinstance(component_config, dict):
                    for comp_name, comp_config in component_config.items():
                        if isinstance(comp_config, dict):
                            comp_type = comp_config.get('type')
                            if not comp_type:
                                self.warnings.append(
                                    f"Component {section}.{comp_name}: missing 'type' field"
                                )
    
    def _validate_plugin_dependencies(self, config: Config) -> None:
        """验证插件依赖关系"""
        if 'plugins' in config and isinstance(config['plugins'], list):
            plugins = config['plugins']
            if not all(isinstance(p, str) for p in plugins):
                self.errors.append("Plugins must be a list of strings")
    
    def _validate_paths(self, config: Config) -> None:
        """验证路径配置"""
        path_fields = ['training.log_dir', 'training.checkpoint_dir']
        
        for field_path in path_fields:
            path_value = self._get_nested_value(config, field_path)
            if isinstance(path_value, str) and path_value:
                try:
                    path = Path(path_value)
                    if not path.parent.exists():
                        self.warnings.append(
                            f"Path {field_path}: parent directory does not exist: {path.parent}"
                        )
                except Exception as e:
                    self.warnings.append(f"Path {field_path}: invalid path: {e}")
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """获取嵌套字典中的值"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def get_errors(self) -> List[str]:
        """获取验证错误列表"""
        return self.errors.copy()
    
    def get_warnings(self) -> List[str]:
        """获取验证警告列表"""
        return self.warnings.copy()
    
    def clear(self) -> None:
        """清除验证结果"""
        self.errors.clear()
        self.warnings.clear()


# 创建默认验证器实例
default_validator = ConfigValidator()