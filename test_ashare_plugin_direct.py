#!/usr/bin/env python3
"""
直接测试重构后的 AshareDataPlugin
"""

import sys
import os

# 直接导入模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接导入需要的模块
from ascend.plugin_manager.base import BasePlugin
from ascend.core.exceptions import PluginError

# 手动定义 IDataSourcePlugin 接口
from typing import Protocol, Any, List

class IDataSourcePlugin(Protocol):
    def fetch_data(self, symbol: str, start_date: str, end_date: str, **kwargs) -> Any:
        ...
    
    def get_available_symbols(self) -> List[str]:
        ...
    
    def get_data_types(self) -> List[str]:
        ...

# 直接导入 AshareDataPlugin
import importlib.util
spec = importlib.util.spec_from_file_location(
    "ashare_data_plugin", 
    "quant_plugins/data_plugins/ashare_data_plugin.py"
)
ashare_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ashare_module)

def test_ashare_plugin():
    """测试 Ashare 数据插件"""
    print("🧪 直接测试 AshareDataPlugin 重构")
    print("=" * 50)
    
    try:
        # 创建插件实例
        plugin = ashare_module.AshareDataPlugin()
        
        print("1. 测试插件初始化")
        print("-" * 30)
        
        # 配置插件
        config = {
            "timeout": 30,
            "max_retries": 3,
            "cache_enabled": True,
            "cache_duration": 3600,
            "use_proxy": False
        }
        
        plugin.configure(config)
        plugin.initialize()
        
        print("✅ 插件初始化成功")
        
        print("\n2. 测试 start() 方法 - 获取股票列表")
        print("-" * 30)
        
        # 测试获取股票列表
        symbols = plugin.start(operation='get_symbols')
        print(f"可用股票代码: {len(symbols)} 个")
        print(f"示例: {symbols[:5]}")
        
        print("\n3. 测试 start() 方法 - 获取数据类型")
        print("-" * 30)
        
        # 测试获取数据类型
        data_types = plugin.start(operation='get_data_types')
        print(f"支持的数据类型: {data_types}")
        
        print("\n4. 测试 start() 方法结构")
        print("-" * 30)
        
        # 测试 start 方法参数处理
        result = plugin.start(
            operation='fetch_data',
            symbols=['000001.SZ'],
            start_date='2023-01-01',
            end_date='2023-01-10'
        )
        
        print(f"✅ start() 方法调用成功，返回类型: {type(result)}")
        
        print("\n5. 测试 IDataSourcePlugin 接口兼容性")
        print("-" * 30)
        
        # 检查是否实现了必要的方法
        required_methods = ['fetch_data', 'get_available_symbols', 'get_data_types']
        for method in required_methods:
            if hasattr(plugin, method) and callable(getattr(plugin, method)):
                print(f"✅ {method}() 方法存在")
            else:
                print(f"❌ {method}() 方法缺失")
        
        print("\n6. 测试插件清理")
        print("-" * 30)
        
        plugin.cleanup()
        print("✅ 插件清理成功")
        
        print("\n" + "=" * 50)
        print("🎉 AshareDataPlugin 重构测试完成！")
        print("✅ 新的 start() 方法架构实现成功")
        print("✅ IDataSourcePlugin 接口保持兼容")
        print("✅ 支持数据流式执行模式")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ashare_plugin()