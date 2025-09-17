"""
性能工具插件测试
验证PerformanceToolsPlugin的功能完整性
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from quant_plugins.evaluator_plugins.advanced_performance_plugin import AdvancedPerformanceEvaluatorPlugin


def test_performance_tools_plugin():
    """测试性能工具插件的基本功能"""
    print("🧪 开始测试性能工具插件...")
    
    # 创建插件实例
    plugin = AdvancedPerformanceEvaluatorPlugin()
    
    # 测试配置
    config = {
        'risk_free_rate': 0.02,
        'enable_advanced_metrics': True,
        'enable_visualization': True,
        'max_lookback_period': 252,
        'benchmark_symbol': '000300.SH'
    }
    
    # 配置插件
    plugin.configure(config)
    
    # 初始化插件
    plugin.initialize()
    
    print("✅ 插件初始化和配置成功")
    
    # 创建模拟数据
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    np.random.seed(42)
    
    # 创建模拟净值曲线 (随机游走)
    equity_values = [1000000]  # 初始资金100万
    for i in range(1, len(dates)):
        daily_return = np.random.normal(0.001, 0.02)  # 日均收益0.1%，波动率2%
        equity_values.append(equity_values[-1] * (1 + daily_return))
    
    equity_curve = pd.Series(equity_values, index=dates, name='equity')
    
    # 创建模拟交易记录
    trades = [
        {'symbol': '000001.SZ', 'quantity': 1000, 'price': 10.5, 'profit_loss': 500, 'date': '2023-01-15'},
        {'symbol': '000002.SZ', 'quantity': 800, 'price': 8.2, 'profit_loss': -320, 'date': '2023-02-20'},
        {'symbol': '600000.SH', 'quantity': 1200, 'price': 12.8, 'profit_loss': 960, 'date': '2023-03-10'},
        {'symbol': '000063.SZ', 'quantity': 600, 'price': 25.3, 'profit_loss': 450, 'date': '2023-04-05'},
        {'symbol': '300001.SZ', 'quantity': 1500, 'price': 6.7, 'profit_loss': -750, 'date': '2023-05-12'}
    ]
    
    print("✅ 模拟数据创建成功")
    
    # 测试性能指标计算
    try:
        metrics = plugin.calculate_metrics(equity_curve, trades)
        print(f"✅ 性能指标计算成功，共计算 {len(metrics)} 个指标")
        
        # 打印关键指标
        key_metrics = [
            'total_return', 'annualized_return', 'sharpe_ratio', 
            'max_drawdown', 'volatility', 'win_rate', 'profit_factor'
        ]
        
        print("\n📊 关键性能指标:")
        for metric in key_metrics:
            if metric in metrics:
                value = metrics[metric]
                if isinstance(value, float):
                    if metric.endswith('_ratio') or metric == 'win_rate':
                        print(f"   {metric}: {value:.4f}")
                    elif metric in ['total_return', 'annualized_return', 'max_drawdown', 'volatility']:
                        print(f"   {metric}: {value:.4%}")
                    else:
                        print(f"   {metric}: {value:.2f}")
        
    except Exception as e:
        print(f"❌ 性能指标计算失败: {e}")
        return False
    
    # 测试可用指标列表
    try:
        available_metrics = plugin.get_available_metrics()
        print(f"\n✅ 可用指标列表获取成功，共 {len(available_metrics)} 个指标")
    except Exception as e:
        print(f"❌ 获取可用指标列表失败: {e}")
        return False
    
    # 测试基准对比 (使用相同的净值曲线作为基准)
    try:
        benchmark_comparison = plugin.compare_with_benchmark(equity_curve, equity_curve)
        print(f"✅ 基准对比测试成功")
        
        print("\n📈 基准对比结果:")
        for key, value in benchmark_comparison.items():
            if isinstance(value, float):
                if key in ['outperformance', 'alpha']:
                    print(f"   {key}: {value:.4%}")
                elif key in ['correlation', 'beta']:
                    print(f"   {key}: {value:.4f}")
                else:
                    print(f"   {key}: {value:.2f}")
            else:
                print(f"   {key}: {value}")
                
    except Exception as e:
        print(f"❌ 基准对比测试失败: {e}")
        return False
    
    # 测试性能报告生成
    try:
        report = plugin.generate_performance_report(metrics)
        print(f"\n✅ 性能报告生成成功")
        print(f"报告长度: {len(report)} 字符")
    except Exception as e:
        print(f"❌ 性能报告生成失败: {e}")
        return False
    
    # 测试插件元数据
    try:
        metadata = plugin.get_metadata()
        print(f"\n✅ 插件元数据获取成功")
        print(f"插件名称: {metadata.get('name')}")
        print(f"版本: {metadata.get('version')}")
        print(f"描述: {metadata.get('description')}")
    except Exception as e:
        print(f"❌ 插件元数据获取失败: {e}")
        return False
    
    # 清理插件
    try:
        plugin.cleanup()
        print("✅ 插件清理成功")
    except Exception as e:
        print(f"❌ 插件清理失败: {e}")
        return False
    
    print("\n🎉 所有测试通过！性能工具插件功能完整")
    return True


if __name__ == "__main__":
    success = test_performance_tools_plugin()
    sys.exit(0 if success else 1)