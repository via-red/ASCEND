"""
测试策略评分选股脚本
"""

import sys
import os

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant_plugins.stock_scoring_selection import StockScoringSelector

def test_basic_functionality():
    """测试基本功能"""
    print("🧪 测试策略评分选股基本功能")
    print("=" * 50)
    
    # 创建选股器
    selector = StockScoringSelector()
    
    try:
        # 初始化插件
        print("1. 初始化插件...")
        if not selector.initialize_plugins():
            print("❌ 插件初始化失败")
            return False
        
        # 测试股票列表
        test_symbols = ['000001.SZ', '000002.SZ', '600000.SH']
        
        # 使用示例数据运行选股
        print("2. 使用示例数据运行选股...")
        results = selector.run_selection(
            symbols=test_symbols,
            start_date='2023-01-01',
            end_date='2023-12-31',
            use_sample_data=True,  # 使用示例数据
            min_score=0.5,
            max_stocks=5
        )
        
        if results and 'selected_stocks' in results:
            selected_count = len(results['selected_stocks'])
            print(f"✅ 选股成功! 选中 {selected_count} 只股票")
            
            # 打印结果
            selector.print_results(results)
            
            # 测试保存功能
            print("3. 测试结果保存...")
            selector.save_results('test_results.json', results)
            
            return True
        else:
            print("❌ 选股失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理资源
        selector.cleanup()

def test_configuration():
    """测试配置功能"""
    print("\n🧪 测试配置功能")
    print("=" * 50)
    
    # 自定义配置
    custom_config = {
        'daily_kline_scoring': {
            'factor_weights': {
                'momentum': 0.4,
                'volume': 0.2,
                'volatility': 0.1,
                'trend': 0.2,
                'rsi_strength': 0.1
            },
            'scoring_threshold': 0.7
        }
    }
    
    selector = StockScoringSelector(custom_config)
    
    try:
        if selector.initialize_plugins():
            print("✅ 自定义配置初始化成功")
            return True
        else:
            print("❌ 自定义配置初始化失败")
            return False
            
    finally:
        selector.cleanup()

def main():
    """运行所有测试"""
    print("🚀 开始策略评分选股测试")
    print("=" * 60)
    
    # 运行功能测试
    test1_passed = test_basic_functionality()
    test2_passed = test_configuration()
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"基本功能测试: {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"配置功能测试: {'✅ 通过' if test2_passed else '❌ 失败'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 所有测试通过!")
        return True
    else:
        print("\n❌ 部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)