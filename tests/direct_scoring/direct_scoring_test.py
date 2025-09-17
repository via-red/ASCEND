"""
直接策略评分测试
直接使用策略插件进行测试，不依赖插件管理器
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quant_plugins.strategy_plugins.daily_kline_scoring_plugin import DailyKlineScoringPlugin

def generate_sample_data(symbols, days=60):
    """生成示例股票数据"""
    print("📊 生成示例数据...")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start_date, end_date, freq='D')
    
    sample_data = {}
    for symbol in symbols:
        # 生成随机价格数据
        np.random.seed(hash(symbol) % 1000)
        base_price = np.random.uniform(10, 100)
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = base_price * np.exp(np.cumsum(returns))
        
        # 创建DataFrame
        df = pd.DataFrame({
            'date': dates,
            'open': prices * 0.99,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.lognormal(10, 1, len(dates))
        })
        
        sample_data[symbol] = df
        print(f"   ✅ {symbol} 示例数据生成完成")
    
    return sample_data

def test_direct_scoring():
    """直接测试评分插件"""
    print("🧪 直接测试日K线评分插件")
    print("=" * 50)
    
    # 创建评分插件实例
    scoring_plugin = DailyKlineScoringPlugin()
    
    try:
        # 配置插件
        config = {
            'factor_weights': {
                'momentum': 0.35,
                'volume': 0.15,
                'volatility': 0.15,
                'trend': 0.25,
                'rsi_strength': 0.10
            },
            'scoring_threshold': 0.65,
            'min_data_points': 20
        }
        
        # 配置和初始化插件
        scoring_plugin.configure(config)
        scoring_plugin.initialize()
        
        print("✅ 评分插件初始化成功")
        
        # 生成示例数据
        test_symbols = ['000001.SZ', '000002.SZ', '600000.SH']
        stock_data = generate_sample_data(test_symbols, days=60)
        
        # 对每只股票进行评分
        print(f"\n📊 对 {len(stock_data)} 只股票进行评分...")
        
        scoring_results = {}
        for symbol, data in stock_data.items():
            try:
                # 执行评分
                result = scoring_plugin.execute(data)
                
                if result and 'scores' in result:
                    score_info = result['scores']
                    scoring_results[symbol] = {
                        'total_score': score_info.get('total_score', 0),
                        'factor_scores': score_info.get('factor_scores', {}),
                        'signal': result.get('signals', {}).get('signal', 'UNKNOWN')
                    }
                    print(f"   ✅ {symbol} 评分: {score_info.get('total_score', 0):.3f}")
                else:
                    print(f"   ⚠️ {symbol} 评分结果异常")
                    
            except Exception as e:
                print(f"   ❌ {symbol} 评分失败: {e}")
        
        # 筛选和显示结果
        print(f"\n🔍 筛选评分结果...")
        
        if scoring_results:
            # 按评分排序
            sorted_stocks = sorted(
                scoring_results.items(),
                key=lambda x: x[1]['total_score'],
                reverse=True
            )
            
            # 筛选评分 >= 0.6 的股票
            min_score = 0.6
            selected_stocks = []
            
            for symbol, score_data in sorted_stocks:
                if score_data['total_score'] >= min_score:
                    selected_stocks.append({
                        'symbol': symbol,
                        'total_score': score_data['total_score'],
                        'factor_scores': score_data['factor_scores'],
                        'signal': score_data['signal']
                    })
            
            # 显示结果
            print("\n" + "=" * 80)
            print("📋 策略评分选股结果")
            print("=" * 80)
            print(f"选股标准: 评分 >= {min_score}")
            print(f"总共分析: {len(stock_data)} 只股票")
            print(f"符合条件: {len(selected_stocks)} 只股票")
            print("-" * 80)
            
            if selected_stocks:
                print("🏆 推荐股票:")
                print("-" * 80)
                for i, stock in enumerate(selected_stocks, 1):
                    print(f"{i:2d}. {stock['symbol']:10s} "
                          f"评分: {stock['total_score']:.3f} "
                          f"信号: {stock['signal']:4s}")
                    
                    # 显示因子得分详情
                    factor_scores = stock.get('factor_scores', {})
                    if factor_scores:
                        factor_details = " | ".join([
                            f"{k}: {v:.3f}" for k, v in factor_scores.items()
                        ])
                        print(f"     因子得分: {factor_details}")
                    print()
            else:
                print("⚠️ 无符合条件的股票")
            
            print("=" * 80)
            
            return True
        else:
            print("❌ 无评分结果")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理资源
        scoring_plugin.cleanup()
        print("\n🧹 资源清理完成")

def main():
    """主函数"""
    print("🚀 直接策略评分测试")
    print("=" * 60)
    
    success = test_direct_scoring()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 测试成功完成!")
    else:
        print("❌ 测试失败")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)