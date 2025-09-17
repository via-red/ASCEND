#!/usr/bin/env python3
"""
ASCEND框架基础使用示例
演示如何加载配置、管理插件和使用核心功能
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ascend import (
    load_config, validate_config, create_default_config,
    load_plugins, list_loaded_plugins, list_available_plugins,
    ConfigError, ValidationError, PluginError
)

def basic_config_example():
    """基础配置操作示例"""
    print("=" * 50)
    print("ASCEND框架基础配置示例")
    print("=" * 50)
    
    try:
        # 1. 加载配置文件
        print("\n1. 加载配置文件...")
        config_path = Path(__file__).parent / "config.yaml"
        config = load_config(str(config_path))
        print(f"✓ 配置文件加载成功: {config_path}")
        print(f"  框架版本: {config.get('version')}")
        print(f"  智能体类型: {config['agent']['type']}")
        print(f"  环境类型: {config['environment']['type']}")
        
        # 2. 验证配置
        print("\n2. 验证配置...")
        is_valid = validate_config(config)
        print(f"✓ 配置验证通过: {is_valid}")
        
        # 3. 创建默认配置
        print("\n3. 创建默认配置...")
        default_config = create_default_config()
        print(f"✓ 默认配置创建成功")
        print(f"  默认智能体: {default_config['agent']['type']}")
        print(f"  默认环境: {default_config['environment']['type']}")
        
        return config
        
    except (ConfigError, ValidationError) as e:
        print(f"✗ 配置错误: {e}")
        return None
    except Exception as e:
        print(f"✗ 未知错误: {e}")
        return None

def plugin_management_example():
    """插件管理示例"""
    print("\n" + "=" * 50)
    print("插件管理示例")
    print("=" * 50)
    
    try:
        # 1. 列出可用插件
        print("\n1. 列出可用插件...")
        available_plugins = list_available_plugins()
        print(f"发现 {len(available_plugins)} 个可用插件:")
        for plugin_info in available_plugins:
            print(f"  - {plugin_info['name']}: {plugin_info['metadata']['description']}")
        
        # 2. 尝试加载插件（这里会失败，因为没有实际插件实现）
        print("\n2. 尝试加载插件...")
        print("注意: 由于没有实际插件实现，加载会失败")
        print("这只是演示框架的插件管理接口")
        
        # 模拟插件配置
        plugin_configs = {
            "ascend_rl_sb3": {"learning_rate": 0.0003},
            "ascend_env_gym": {"env_id": "CartPole-v1"}
        }
        
        try:
            plugins = load_plugins(["ascend_rl_sb3", "ascend_env_gym"], plugin_configs)
            print(f"✓ 插件加载成功: {len(plugins)} 个插件")
            
            # 3. 列出已加载插件
            loaded_plugins = list_loaded_plugins()
            print(f"已加载插件: {loaded_plugins}")
            
        except PluginError as e:
            print(f"✗ 插件加载失败（预期中）: {e}")
            print("这是正常的，因为我们还没有实现具体的插件")
        
        return True
        
    except Exception as e:
        print(f"✗ 插件管理错误: {e}")
        return False

def framework_info_example():
    """框架信息示例"""
    print("\n" + "=" * 50)
    print("框架信息示例")
    print("=" * 50)
    
    from ascend import __version__, __author__, __description__
    
    print(f"框架名称: ASCEND")
    print(f"版本: {__version__}")
    print(f"作者: {__author__}")
    print(f"描述: {__description__}")
    
    # 核心协议信息
    from ascend import (
        IAgent, IEnvironment, IPolicy, IModel,
        State, Action, Reward, Config
    )
    
    print(f"\n核心协议:")
    print(f"  - IAgent: {IAgent.__doc__}")
    print(f"  - IEnvironment: {IEnvironment.__doc__}")
    print(f"  - IPolicy: {IPolicy.__doc__}")
    print(f"  - IModel: {IModel.__doc__}")
    
    print(f"\n核心类型:")
    print(f"  - State: 状态表示")
    print(f"  - Action: 动作类型") 
    print(f"  - Reward: 奖励值")
    print(f"  - Config: 配置字典")

def create_custom_plugin_example():
    """创建自定义插件示例"""
    print("\n" + "=" * 50)
    print("创建自定义插件示例")
    print("=" * 50)
    
    from ascend.plugins import BasePlugin
    from ascend.core import PluginMetadata
    
    class DemoPlugin(BasePlugin):
        """演示插件"""
        
        def __init__(self):
            super().__init__(
                name="demo_plugin",
                version="0.1.0",
                description="演示插件示例",
                author="ASCEND Team"
            )
        
        def register(self, registry):
            """注册插件组件"""
            print("✓ 演示插件注册方法被调用")
            # 这里可以注册具体的组件
        
        def _get_required_plugins(self):
            return ["ascend_rl_sb3"]  # 依赖其他插件
        
        def _get_provided_components(self):
            return ["demo_component"]  # 提供 demo_component
    
    # 创建插件实例
    plugin = DemoPlugin()
    print(f"插件名称: {plugin.get_name()}")
    print(f"插件版本: {plugin.get_version()}")
    print(f"插件描述: {plugin.description}")
    
    # 获取元数据
    metadata = plugin.get_metadata()
    print(f"依赖插件: {metadata['requires']}")
    print(f"提供组件: {metadata['provides']}")
    
    print("✓ 自定义插件创建成功")

def main():
    """主函数"""
    print("ASCEND框架基础使用示例")
    print("本示例演示框架的核心功能和接口")
    print()
    
    # 运行各个示例
    config = basic_config_example()
    if config:
        plugin_management_example()
        framework_info_example()
        create_custom_plugin_example()
        
        print("\n" + "=" * 50)
        print("示例执行完成!")
        print("=" * 50)
        print("框架核心功能演示完毕。")
        print("下一步可以:")
        print("1. 实现具体的插件")
        print("2. 创建自定义智能体和环境")
        print("3. 开始训练实验")
    else:
        print("示例执行失败，请检查配置")

if __name__ == "__main__":
    main()