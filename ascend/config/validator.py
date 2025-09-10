"""
ASCEND配置验证器
提供配置数据的验证和完整性检查
"""

import re
from typing import Dict, Any, List, Optional, Set
from pathlib import Path

from ascend.core.exceptions import ValidationError
from ascend.core.types import Config, ComponentType

class ConfigValidator:
    """配置验证器类"""
    
    # 基础验证规则
    BASE_RULES = {
        'version': {
            'required': True,
            'type': 'string',
            'pattern': r'^\d+\.\d+\.\d+$'  # 语义化版本格式
        },
        'framework': {
            'required': True,
            'type': 'string',
            'allowed': ['ascend']
        },
        'agent.type': {
            'required': True,
            'type': 'string',
            'min_length': 1
        },
        'environment.type': {
            'required': True,
            'type': 'string',
            'min_length': 1
        },
        'training.total_timesteps': {
            'required': True,
            'type': 'integer',
            'min': 1000
        },
        'training.learning_rate': {
            'type': 'number',
            'min': 0,
            'max': 1
        }
    }
    
    # 组件类型验证规则
    COMPONENT_RULES = {
        ComponentType.AGENT.value: {
            'type': {'required': True, 'type': 'string'},
            'config': {'type': 'dict'}
        },
        ComponentType.ENVIRONMENT.value: {
            'type': {'required': True, 'type': 'string'},
            'config': {'type': 'dict'}
        },
        ComponentType.MODEL.value: {
            'type': {'required': True, 'type': 'string'},
            'config': {'type': 'dict'}
        },
        ComponentType.REWARD.value: {
            'type': {'required': True, 'type': 'string'},
            'config': {'type': 'dict'}
        }
    }
    
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
            
            # 字段级验证
            self._validate_fields(config, self.BASE_RULES)
            
            # 组件配置验证
            self._validate_components(config)
            
            # 插件依赖验证
            self._validate_plugin_dependencies(config)
            
            # 路径验证
            self._validate_paths(config)
            
            return len(self.errors) == 0
            
        except ValidationError as e:
            if strict:
                raise
            self.errors.append(str(e))
            return False
    
    def _validate_basic_structure(self, config: Config) -> None:
        """验证配置基础结构"""
        if not isinstance(config, dict):
            raise ValidationError("Config must be a dictionary")
        
        required_sections = ['agent', 'environment', 'training']
        for section in required_sections:
            if section not in config:
                raise ValidationError(f"Missing required section: {section}", section)
    
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