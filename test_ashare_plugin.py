#!/usr/bin/env python3
"""
测试重构后的 AshareDataPlugin
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quant_plugins.data_plugins.ashare_data_plugin import AshareDataPlugin
from ascend.core.exceptions import PluginError

def test_ashare_plugin():
    """测试 Ashare 数据插件"""
    print("🧪 测试 AshareDataPlugin 重构")
    print("=" * 50)
    
    try:
        # 创建插件实例
        plugin = AshareDataPlugin()
        
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
        
        print("\n4. 测试 start() 方法 - 获取单个股票数据")
        print("-" * 30)
        
        # 测试获取单个股票数据
        result = plugin.start(
            operation='fetch_data',
            symbol='000001.SZ',
            start_date='2023-01-01',
            end_date='2023-01-10',
            data_type='daily'
        )
        
        if isinstance(result, dict) and 'error' in result:
            print(f"❌ 数据获取失败: {result['error']}")
        else:
            print(f"✅ 数据获取成功，数据形状: {result.shape if hasattr(result, 'shape') else 'N/A'}")
            if hasattr(result, 'head'):
                print(f"数据预览:\n{result.head()}")
        
        print("\n5. 测试 IDataSourcePlugin 接口兼容性")
        print("-" * 30)
        
        # 测试直接调用 fetch_data 方法（保持接口兼容）
        data = plugin.fetch_data(
            symbol='000001.SZ',
            start_date='2023-01-01',
            end_date='2023-01-05',
            data_type='daily'
        )
        
        if isinstance(data, dict) and 'error' in data:
            print(f"❌ 接口兼容性测试失败: {data['error']}")
        else:
            print("✅ IDataSourcePlugin 接口兼容性测试通过")
        
        print("\n6. 测试插件清理")
        print("-" * 30)
        
        plugin.cleanup()
        print("✅ 插件清理成功")
        
        print("\n" + "=" * 50)
        print("🎉 AshareDataPlugin 重构测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ashare_plugin()