#!/usr/bin/env python3
"""
ASCEND框架基础使用示例
演示如何使用统一的ascend实例加载配置、管理插件和使用核心功能
"""

import os
import sys
from pathlib import Path

def main():
    print("🚀 ASCEND框架基础使用示例")
    print("=" * 50)
    
    config_path = Path(__file__).parent / "config.yaml"
    
    try:
        # 直接使用配置文件路径初始化ascend实例
        from ascend import Ascend
        
        print("1. 初始化ASCEND实例...")
        ascend = Ascend(config_path)
        print(f"   ✅ ASCEND实例初始化成功，配置文件: {config_path}")
        
        # 获取已加载的插件列表（通过初始化自动加载）
        loaded_plugins = list(ascend.loaded_plugins.keys())
        print(f"   ✅ 自动加载插件: {loaded_plugins}")
        
        # 通过ascend获取插件实例
        print("\n3. 获取插件实例...")
        if loaded_plugins:
            plugin_name = loaded_plugins[0]
            plugin = ascend.get_plugin(plugin_name)
            print(f"   ✅ 获取到插件实例: {plugin_name} ({type(plugin).__name__})")
        
        # 打印插件信息
        print("\n4. 打印插件信息...")
        ascend.print_plugin_info()
        
        # 执行插件实例的功能（如果有可用功能）
        print("\n5. 尝试执行插件功能...")
        if loaded_plugins:
            plugin_name = loaded_plugins[0]
            
            # 检查插件是否有get_info方法
            if hasattr(plugin, 'get_info'):
                try:
                    info = ascend.execute_plugin_function(plugin_name, 'get_info')
                    print(f"   ✅ 执行 {plugin_name}.get_info() 成功")
                    print(f"      返回信息: {info}")
                except Exception as e:
                    print(f"   ⚠️ 执行 {plugin_name}.get_info() 失败: {e}")
            
            # 检查插件是否有其他常用方法
            common_methods = ['initialize', 'configure', 'start', 'stop', 'status']
            for method in common_methods:
                if hasattr(plugin, method):
                    print(f"   插件 {plugin_name} 有方法: {method}")
        
        # 通过ascend销毁插件实例
        print("\n6. 销毁插件实例...")
        ascend.destroy_all_plugins()
        print("   ✅ 所有插件实例已销毁")
        
    except Exception as e:
        print(f"❌ 示例运行失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("🎉 ASCEND基础示例运行完成！")

if __name__ == "__main__":
    main()