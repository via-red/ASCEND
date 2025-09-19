"""
ASCEND插件版本工具
提供插件版本约束解析和验证功能
"""

import re
from typing import Optional, Tuple, List
from packaging import version
from packaging.specifiers import SpecifierSet

def parse_version_constraint(plugin_spec: str) -> Tuple[str, Optional[str]]:
    """解析插件名称和版本约束
    
    Args:
        plugin_spec: 插件规格字符串，格式为 "name" 或 "name:constraint"
        
    Returns:
        (插件名称, 版本约束) 元组
    """
    if ':' in plugin_spec:
        name, constraint = plugin_spec.split(':', 1)
        return name.strip(), constraint.strip()
    return plugin_spec.strip(), None

def check_version_compatibility(actual_version: str, constraint: str) -> bool:
    """检查版本兼容性
    
    Args:
        actual_version: 实际版本号
        constraint: 版本约束
        
    Returns:
        是否兼容
    """
    try:
        # 处理语义化版本约束
        spec = SpecifierSet(constraint)
        return spec.contains(version.parse(actual_version))
    except Exception:
        # 如果版本约束解析失败，尝试简单比较
        try:
            if constraint.startswith('>='):
                min_version = constraint[2:].strip()
                return version.parse(actual_version) >= version.parse(min_version)
            elif constraint.startswith('=='):
                exact_version = constraint[2:].strip()
                return version.parse(actual_version) == version.parse(exact_version)
            elif constraint.startswith('>'):
                min_version = constraint[1:].strip()
                return version.parse(actual_version) > version.parse(min_version)
            elif constraint.startswith('<='):
                max_version = constraint[2:].strip()
                return version.parse(actual_version) <= version.parse(max_version)
            elif constraint.startswith('<'):
                max_version = constraint[1:].strip()
                return version.parse(actual_version) < version.parse(max_version)
            else:
                # 默认使用精确匹配
                return actual_version == constraint
        except Exception:
            return False

def validate_plugin_version(plugin_info: dict, constraint: Optional[str]) -> bool:
    """验证插件版本是否符合约束
    
    Args:
        plugin_info: 插件信息字典
        constraint: 版本约束
        
    Returns:
        是否验证通过
    """
    if not constraint:
        return True  # 无版本约束，总是通过
    
    actual_version = plugin_info.get('version')
    if not actual_version:
        return False  # 无版本信息，验证失败
        
    return check_version_compatibility(actual_version, constraint)

def sort_plugins_by_version(plugins: List[dict]) -> List[dict]:
    """按版本号对插件进行排序（从高到低）
    
    Args:
        plugins: 插件信息列表
        
    Returns:
        排序后的插件列表
    """
    def get_version_key(plugin):
        version_str = plugin.get('version', '0.0.0')
        try:
            return version.parse(version_str)
        except Exception:
            return version.parse('0.0.0')
    
    return sorted(plugins, key=get_version_key, reverse=True)

def get_best_matching_plugin(plugins: List[dict], constraint: Optional[str] = None) -> Optional[dict]:
    """获取最佳匹配的插件（版本最高且符合约束）
    
    Args:
        plugins: 插件信息列表
        constraint: 版本约束
        
    Returns:
        最佳匹配的插件信息或None
    """
    # 先按版本排序
    sorted_plugins = sort_plugins_by_version(plugins)
    
    # 如果没有约束，返回最高版本
    if not constraint:
        return sorted_plugins[0] if sorted_plugins else None
    
    # 查找符合约束的最高版本
    for plugin in sorted_plugins:
        if validate_plugin_version(plugin, constraint):
            return plugin
    
    return None