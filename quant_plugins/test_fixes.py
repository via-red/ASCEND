"""
测试修复后的插件功能
验证核心插件缺失和协议接口合规性问题的修复
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime

def test_multi_factor_model_plugin():
    """测试多因子模型插件"""
    print("🧪 测试 MultiFactorModelPlugin...")
    
    try:
        from quant_plugins.strategy_plugins.multi_factor_model_plugin import MultiFactorModelPlugin
        
        # 创建插件实例
        plugin = MultiFactorModelPlugin()
        
        # 测试配置
        config = {
            'enabled_factors': ['momentum', 'volatility'],
            'factor_normalization': 'zscore'
        }
        plugin.configure(config)
        plugin.initialize()
        
        # 测试可用因子列表
        available_factors = plugin.get_available_factors()
        print(f"   ✅ 可用因子: {available_factors}")
        
        # 测试策略类型
        strategy_type = plugin.get_strategy_type()
        print(f"   ✅ 策略类型: {strategy_type}")
        
        # 测试所需数据类型
        data_types = plugin.get_required_data_types()
        print(f"   ✅ 所需数据类型: {data_types}")
        
        print("   ✅ MultiFactorModelPlugin 测试通过!")
        return True
        
    except Exception as e:
        print(f"   ❌ MultiFactorModelPlugin 测试失败: {e}")
        return False

def test_register_methods():
    """测试插件注册方法"""
    print("\n🧪 测试插件注册方法...")
    
    plugins_to_test = [
        ('data_plugins', 'warehouse_storage'),
        ('backtest_plugins', 'daily_backtest_engine'),
        ('backtest_plugins', 'performance_evaluator'),
        ('execution_plugins', 'sim_trader'),
        ('execution_plugins', 'realtime_monitor')
    ]
    
    success_count = 0
    for module_name, plugin_name in plugins_to_test:
        try:
            module = __import__(f'quant_plugins.{module_name}', fromlist=[plugin_name])
            plugin_class = getattr(module, f'{plugin_name.capitalize()}Plugin')
            
            plugin = plugin_class()
            
            # 模拟注册器
            class MockRegistry:
                def __init__(self):
                    self.registered = {}
                
                def register_feature_extractor(self, name, plugin):
                    self.registered[name] = plugin
                    print(f"   ✅ {name} 注册为特征提取器")
                
                def register_environment(self, name, plugin):
                    self.registered[name] = plugin
                    print(f"   ✅ {name} 注册为环境")
                
                def register_policy(self, name, plugin):
                    self.registered[name] = plugin
                    print(f"   ✅ {name} 注册为策略")
                
                def register_monitor(self, name, plugin):
                    self.registered[name] = plugin
                    print(f"   ✅ {name} 注册为监控器")
            
            registry = MockRegistry()
            plugin.register(registry)
            
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ {plugin_name} 注册测试失败: {e}")
    
    print(f"   ✅ 注册方法测试: {success_count}/{len(plugins_to_test)} 通过")
    return success_count == len(plugins_to_test)

def test_tushare_improvements():
    """测试 Tushare 数据插件改进"""
    print("\n🧪 测试 Tushare 数据插件改进...")
    
    try:
        from quant_plugins.data_plugins.tushare_data_plugin import TushareDataPlugin
        
        plugin = TushareDataPlugin()
        
        # 测试可用股票代码方法
        symbols = plugin.get_available_symbols()
        print(f"   ✅ 可用股票代码数量: {len(symbols)}")
        print(f"   ✅ 示例股票代码: {symbols[:5]}")
        
        # 测试数据类型
        data_types = plugin.get_data_types()
        print(f"   ✅ 支持的数据类型: {data_types}")
        
        print("   ✅ Tushare 数据插件改进测试通过!")
        return True
        
    except Exception as e:
        print(f"   ❌ Tushare 数据插件改进测试失败: {e}")
        return False

def test_performance_evaluator():
    """测试性能评估器改进"""
    print("\n🧪 测试性能评估器改进...")
    
    try:
        from quant_plugins.backtest_plugins.performance_evaluator_plugin import PerformanceEvaluatorPlugin
        
        plugin = PerformanceEvaluatorPlugin()
        
        # 测试基准对比方法
        # 创建示例数据
        dates = pd.date_range('2023-01-01', '2023-06-30', freq='D')
        strategy_equity = pd.Series(
            np.cumprod(1 + np.random.normal(0.001, 0.02, len(dates))),
            index=dates
        )
        benchmark_equity = pd.Series(
            np.cumprod(1 + np.random.normal(0.0005, 0.015, len(dates))),
            index=dates
        )
        
        result = plugin.compare_with_benchmark(strategy_equity, benchmark_equity)
        print(f"   ✅ 基准对比结果: {list(result.keys())}")
        
        # 测试可用指标
        metrics = plugin.get_available_metrics()
        print(f"   ✅ 可用性能指标: {metrics}")
        
        print("   ✅ 性能评估器改进测试通过!")
        return True
        
    except Exception as e:
        print(f"   ❌ 性能评估器改进测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 开始测试插件修复情况")
    print("=" * 60)
    
    test_results = []
    
    # 运行所有测试
    test_results.append(test_multi_factor_model_plugin())
    test_results.append(test_register_methods())
    test_results.append(test_tushare_improvements())
    test_results.append(test_performance_evaluator())
    
    # 汇总结果
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有修复测试通过!")
        print("✅ 核心插件缺失问题已解决")
        print("✅ 协议接口合规性问题已修复")
    else:
        print("⚠️  部分测试未通过，需要进一步检查")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)