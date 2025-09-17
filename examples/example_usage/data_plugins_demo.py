"""
ASCEND 数据插件使用演示 (data_plugins_demo.py)
展示如何使用数据插件层进行数据获取、处理和存储

功能:
- Tushare数据获取
- 数据预处理和特征工程
- 数据存储和管理
- 缓存机制演示
"""

import asyncio
from typing import Dict, Any
import pandas as pd

from ascend.plugin_manager.manager import PluginManager
from quant_plugins.data_plugins import (
    TushareDataPlugin, 
    DataPreprocessingPlugin,
    WarehouseStoragePlugin
)


async def main():
    """主函数：演示数据插件的使用"""
    
    print("🚀 ASCEND 量化插件使用示例")
    print("=" * 50)
    
    # 创建插件管理器
    plugin_manager = PluginManager()
    
    try:
        # 配置插件
        plugin_configs = {
            'tushare_data': {
                'token': 'your_tushare_token_here',  # 需要替换为实际的token
                'timeout': 30,
                'max_retries': 3,
                'cache_enabled': True
            },
            'data_preprocessing': {
                'missing_value_strategy': 'fill',
                'scaling_method': 'standard',
                'feature_engineering': True
            },
            'warehouse_storage': {
                'storage_path': './data/warehouse',
                'storage_format': 'parquet'
            }
        }
        
        print("1. 加载数据插件...")
        
        # 加载数据插件
        data_plugins = {}
        for plugin_name in ['tushare_data', 'data_preprocessing', 'warehouse_storage']:
            plugin = plugin_manager.load_plugin(plugin_name)
            plugin.configure(plugin_configs.get(plugin_name, {}))
            plugin.initialize()
            data_plugins[plugin_name] = plugin
            print(f"   ✅ {plugin_name} 加载成功")
        
        # 获取插件实例
        tushare_plugin = data_plugins['tushare_data']
        preprocessing_plugin = data_plugins['data_preprocessing']
        storage_plugin = data_plugins['warehouse_storage']
        
        print("\n2. 获取股票数据...")
        
        # 获取股票数据示例
        symbols = tushare_plugin.get_available_symbols()[:3]  # 只取前3个股票
        print(f"   可用的股票代码: {symbols}")
        
        # 获取平安银行的数据
        symbol = '000001.SZ'
        print(f"   获取 {symbol} 的数据...")
        
        try:
            # 获取日线数据
            raw_data = tushare_plugin.fetch_data(
                symbol=symbol,
                start_date='2023-01-01',
                end_date='2023-01-31',
                data_type='daily',
                adjust='qfq'
            )
            
            if not raw_data.empty:
                print(f"   ✅ 成功获取 {len(raw_data)} 条数据")
                print(f"   数据列: {list(raw_data.columns)}")
                print(f"   数据示例:\n{raw_data.head(2)}")
                
                print("\n3. 数据预处理...")
                
                # 数据清洗
                cleaned_data = preprocessing_plugin.clean_data(raw_data)
                print("   ✅ 数据清洗完成")
                
                # 处理缺失值
                processed_data = preprocessing_plugin.handle_missing_values(cleaned_data)
                print("   ✅ 缺失值处理完成")
                
                # 数据标准化
                normalized_data = preprocessing_plugin.normalize_data(processed_data)
                print("   ✅ 数据标准化完成")
                
                # 特征工程
                featured_data = preprocessing_plugin.extract_features(normalized_data)
                print("   ✅ 特征工程完成")
                print(f"   处理后数据形状: {featured_data.shape}")
                
                print("\n4. 数据存储...")
                
                # 保存原始数据
                storage_key = f"{symbol}_raw_202301"
                storage_plugin.save_data(raw_data, storage_key)
                print(f"   ✅ 原始数据保存成功: {storage_key}")
                
                # 保存处理后的数据
                processed_key = f"{symbol}_processed_202301"
                storage_plugin.save_data(featured_data, processed_key)
                print(f"   ✅ 处理数据保存成功: {processed_key}")
                
                # 列出保存的数据
                saved_keys = storage_plugin.list_keys(f"*{symbol}*")
                print(f"   已保存的数据键: {saved_keys}")
                
                print("\n5. 数据加载验证...")
                
                # 加载保存的数据进行验证
                loaded_data = storage_plugin.load_data(processed_key)
                print(f"   ✅ 数据加载成功，形状: {loaded_data.shape}")
                
            else:
                print("   ⚠️ 未获取到数据，请检查Tushare token配置")
                
        except Exception as e:
            print(f"   ❌ 数据获取失败: {e}")
            print("   💡 提示: 请确保已安装tushare并配置有效的token")
        
        print("\n6. 清理资源...")
        
        # 清理插件
        for plugin in data_plugins.values():
            plugin.cleanup()
        
        print("   ✅ 资源清理完成")
        
    except Exception as e:
        print(f"❌ 示例运行失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 示例运行完成！")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())