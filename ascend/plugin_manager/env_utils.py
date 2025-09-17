"""
ASCEND环境变量工具
提供.env文件加载和环境变量处理功能
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

def load_env_file(env_file_path: Optional[str] = None) -> Dict[str, str]:
    """加载.env文件并返回环境变量字典
    
    Args:
        env_file_path: .env文件路径，如果为None则搜索默认位置
        
    Returns:
        环境变量字典
    """
    env_vars = {}
    
    # 确定.env文件路径
    if env_file_path is None:
        # 搜索默认位置：当前目录、用户目录、项目根目录
        possible_paths = [
            Path.cwd() / ".env",
            Path.home() / ".ascend" / ".env",
            Path(__file__).parent.parent.parent / ".env"
        ]
        
        for path in possible_paths:
            if path.exists():
                env_file_path = str(path)
                break
        else:
            # 没有找到.env文件
            return {}
    
    try:
        with open(env_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                
                # 解析键值对
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # 移除引号
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]
                    
                    env_vars[key] = value
                    
        logger.info(f"Loaded environment variables from {env_file_path}")
        
    except Exception as e:
        logger.warning(f"Failed to load .env file {env_file_path}: {e}")
    
    return env_vars

def get_env_var(key: str, default: Optional[str] = None, 
               env_file_path: Optional[str] = None) -> Optional[str]:
    """获取环境变量值，优先从.env文件读取
    
    Args:
        key: 环境变量名
        default: 默认值
        env_file_path: .env文件路径
        
    Returns:
        环境变量值，如果不存在则返回默认值
    """
    # 首先尝试从系统环境变量获取
    value = os.environ.get(key)
    if value is not None:
        return value
    
    # 如果系统环境变量中没有，尝试从.env文件获取
    env_vars = load_env_file(env_file_path)
    return env_vars.get(key, default)

def set_env_from_file(env_file_path: Optional[str] = None) -> None:
    """从.env文件加载环境变量到系统环境
    
    Args:
        env_file_path: .env文件路径
    """
    env_vars = load_env_file(env_file_path)
    for key, value in env_vars.items():
        if key not in os.environ:  # 不覆盖已存在的环境变量
            os.environ[key] = value
            logger.debug(f"Set environment variable from .env: {key}")

# 在模块加载时自动设置环境变量（可选）
# set_env_from_file()