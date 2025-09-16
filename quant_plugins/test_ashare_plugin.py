#!/usr/bin/env python3
"""
Ashare 数据插件测试脚本
用于测试 AshareDataPlugin 的功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant_plugins.data_plugins.ashare_data_plugin import AshareDataPlugin, AshareDataPluginConfig
from datetime import datetime, timedelta

def test_ashare_plugin():
    """测试 Ashare 数据插件"""
    print("=" * 50)
    print("测试 Ashare 数据插件")
    print("=" * 50)
    
    # 创建插件实例
    plugin = AshareDataPlugin()
    
    # 设置配置
    config = AshareDataPluginConfig(
        timeout=30,
        max_retries=3,
        cache_enabled=True,
        cache_duration=3600
    )
    
    # 配置和初始化插件
    try:
        plugin.configure(config.model_dump())
        plugin.initialize()
        print("✓ Ashare 插件初始化成功")
    except Exception as e:
        print(f"✗ Ashare 插件初始化失败: {e}")
        return False
    
    # 测试获取可用股票代码
    try:
        symbols = plugin.get_available_symbols()
        print(f"✓ 获取到 {len(symbols)} 个股票代码")
        print(f"  示例: {symbols[:5]}")
    except Exception as e:
        print(f"✗ 获取股票代码失败: {e}")
        return False
    
    # 测试获取支持的数据类型
    try:
        data_types = plugin.get_data_types()
        print(f"✓ 支持的数据类型: {data_types}")
    except Exception as e:
        print(f"✗ 获取数据类型失败: {e}")
        return False
    
    # 测试获取股票数据
    test_symbols = ['000001.XSHE', '600000.XSHG']  # 平安银行, 浦发银行
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    for symbol in test_symbols:
        try:
            print(f"\n测试获取 {symbol} 数据:")
            print(f"  时间范围: {start_date} 到 {end_date}")
            
            # 获取日线数据
            daily_data = plugin.fetch_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                data_type='daily',
                frequency='1d'
            )
            
            if not daily_data.empty:
                print(f"✓ 获取日线数据成功: {len(daily_data)} 条记录")
                print(f"  最新数据: {daily_data.index[-1].strftime('%Y-%m-%d')}")
                print(f"  数据列: {list(daily_data.columns)}")
            else:
                print("✗ 获取日线数据为空")
                continue
            
            # 测试缓存功能
            cached_data = plugin.fetch_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                data_type='daily',
                frequency='1d'
            )
            
            if len(daily_data) == len(cached_data):
                print("✓ 缓存功能正常")
            else:
                print("✗ 缓存功能异常")
                
        except Exception as e:
            print(f"✗ 获取 {symbol} 数据失败: {e}")
            continue
    
    # 测试不同频率的数据
    frequencies = ['1d', '1w', '1M']
    for freq in frequencies:
        try:
            data = plugin.fetch_data(
                symbol='000001.XSHE',
                start_date=start_date,
                end_date=end_date,
                frequency=freq
            )
            if not data.empty:
                print(f"✓ {freq} 频率数据获取成功: {len(data)} 条记录")
            else:
                print(f"⚠ {freq} 频率数据为空")
        except Exception as e:
            print(f"✗ {freq} 频率数据获取失败: {e}")
    
    # 清理资源
    try:
        plugin.cleanup()
        print("\n✓ 插件资源清理成功")
    except Exception as e:
        print(f"✗ 插件资源清理失败: {e}")
    
    print("\n" + "=" * 50)
    print("Ashare 数据插件测试完成")
    print("=" * 50)
    
    return True

def compare_with_tushare():
    """与 Tushare 插件对比测试"""
    print("\n" + "=" * 50)
    print("与 Tushare 插件对比测试")
    print("=" * 50)
    
    try:
        from quant_plugins.data_plugins.tushare_data_plugin import TushareDataPlugin, TushareDataPluginConfig
        
        # 需要 Tushare token，如果没有则跳过
        tushare_plugin = TushareDataPlugin()
        tushare_config = TushareDataPluginConfig(token="your_tushare_token_here")
        
        try:
            tushare_plugin.initialize(tushare_config.dict())
            print("✓ Tushare 插件也可用")
        except:
            print("⚠ Tushare 插件需要配置 token，跳过详细对比")
            return
            
    except ImportError:
        print("⚠ Tushare 插件不可用，跳过对比")
        return

if __name__ == "__main__":
    success = test_ashare_plugin()
    compare_with_tushare()
    
    if success:
        print("\n🎉 Ashare 数据插件测试通过！")
        print("现在您可以在配置中选择使用 Ashare 或 Tushare 作为数据源")
    else:
        print("\n❌ Ashare 数据插件测试失败")
        sys.exit(1)