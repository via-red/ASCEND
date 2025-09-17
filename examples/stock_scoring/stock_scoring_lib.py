"""
ASCEND 策略评分选股库 (stock_scoring_lib.py)
基于quant_plugins的多因子评分模型对股票进行评分和筛选

功能:
- 多股票批量评分
- 多因子综合评分 (动量、成交量、波动率、趋势、RSI)
- 阈值筛选和排名
- 详细结果输出
- 可编程接口，支持集成到其他系统
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import argparse
import json
from datetime import datetime, timedelta

from ascend.plugins.manager import PluginManager
from quant_plugins.strategy_plugins import DailyKlineScoringPlugin
from quant_plugins.data_plugins import TushareDataPlugin, DataPreprocessingPlugin


class StockScoringSelector:
    """股票评分选股器"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化选股器
        
        Args:
            config: 配置字典，包含插件配置
        """
        self.plugin_manager = PluginManager()
        self.plugins = {}
        self.results = {}
        self.config = config or self._get_default_config()
        
    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            'tushare_data': {
                'token': 'your_tushare_token_here',  # 需要替换为实际的Tushare token
                'timeout': 30,
                'max_retries': 3,
                'cache_enabled': True
            },
            'data_preprocessing': {
                'missing_value_strategy': 'fill',
                'scaling_method': 'standard',
                'feature_engineering': True
            },
            'daily_kline_scoring': {
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
        }
    
    def initialize_plugins(self) -> bool:
        """初始化所有插件"""
        try:
            print("🔌 初始化插件...")
            
            # 加载和配置插件
            plugin_names = ['tushare_data', 'data_preprocessing', 'daily_kline_scoring']
            
            for plugin_name in plugin_names:
                plugin = self.plugin_manager.load_plugin(plugin_name)
                plugin_config = self.config.get(plugin_name, {})
                plugin.configure(plugin_config)
                plugin.initialize()
                self.plugins[plugin_name] = plugin
                print(f"   ✅ {plugin_name} 初始化成功")
            
            return True
            
        except Exception as e:
            print(f"❌ 插件初始化失败: {e}")
            return False
    
    def get_stock_data(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]:
        """
        获取股票数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            股票数据字典 {symbol: DataFrame}
        """
        try:
            tushare_plugin = self.plugins['tushare_data']
            preprocessing_plugin = self.plugins['data_preprocessing']
            
            stock_data = {}
            
            for symbol in symbols:
                try:
                    print(f"📡 获取 {symbol} 数据...")
                    
                    # 获取原始数据
                    raw_data = tushare_plugin.fetch_data(
                        symbol=symbol,
                        start_date=start_date,
                        end_date=end_date,
                        data_type='daily',
                        adjust='qfq'
                    )
                    
                    if not raw_data.empty:
                        # 数据预处理
                        cleaned_data = preprocessing_plugin.clean_data(raw_data)
                        processed_data = preprocessing_plugin.handle_missing_values(cleaned_data)
                        featured_data = preprocessing_plugin.extract_features(processed_data)
                        
                        stock_data[symbol] = featured_data
                        print(f"   ✅ {symbol} 数据处理完成 ({len(featured_data)} 条记录)")
                    else:
                        print(f"   ⚠️ {symbol} 无数据")
                        
                except Exception as e:
                    print(f"   ❌ {symbol} 数据处理失败: {e}")
            
            return stock_data
            
        except Exception as e:
            print(f"❌ 数据获取失败: {e}")
            return {}
    
    def score_stocks(self, stock_data: Dict[str, pd.DataFrame]) -> Dict[str, Dict]:
        """
        对股票进行评分
        
        Args:
            stock_data: 股票数据字典
            
        Returns:
            评分结果字典 {symbol: score_details}
        """
        try:
            scoring_plugin = self.plugins['daily_kline_scoring']
            scoring_results = {}
            
            for symbol, data in stock_data.items():
                try:
                    # 执行评分策略
                    result = scoring_plugin.execute(data)
                    
                    if result and 'scores' in result:
                        score_info = result['scores']
                        scoring_results[symbol] = {
                            'total_score': score_info.get('total_score', 0),
                            'factor_scores': score_info.get('factor_scores', {}),
                            'factors': score_info.get('factors', {}),
                            'signal': result.get('signals', {}).get('signal', 'UNKNOWN')
                        }
                        print(f"   ✅ {symbol} 评分完成: {score_info.get('total_score', 0):.3f}")
                    else:
                        print(f"   ⚠️ {symbol} 评分结果异常")
                        
                except Exception as e:
                    print(f"   ❌ {symbol} 评分失败: {e}")
            
            return scoring_results
            
        except Exception as e:
            print(f"❌ 评分过程失败: {e}")
            return {}
    
    def filter_stocks(self, scoring_results: Dict[str, Dict], 
                     min_score: float = 0.6, 
                     max_stocks: int = 10) -> List[Dict]:
        """
        筛选符合条件的股票
        
        Args:
            scoring_results: 评分结果
            min_score: 最低评分阈值
            max_stocks: 最大股票数量
            
        Returns:
            筛选后的股票列表
        """
        # 按评分排序
        sorted_stocks = sorted(
            scoring_results.items(),
            key=lambda x: x[1]['total_score'],
            reverse=True
        )
        
        # 筛选符合条件的股票
        filtered_stocks = []
        for symbol, score_data in sorted_stocks:
            if score_data['total_score'] >= min_score and len(filtered_stocks) < max_stocks:
                filtered_stocks.append({
                    'symbol': symbol,
                    'total_score': score_data['total_score'],
                    'factor_scores': score_data['factor_scores'],
                    'signal': score_data['signal']
                })
        
        return filtered_stocks
    
    def generate_sample_data(self, symbols: List[str], days: int = 60) -> Dict[str, pd.DataFrame]:
        """
        生成示例数据（用于测试）
        
        Args:
            symbols: 股票代码列表
            days: 数据天数
            
        Returns:
            示例数据字典
        """
        print("📊 生成示例数据...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        dates = pd.date_range(start_date, end_date, freq='D')
        
        sample_data = {}
        for symbol in symbols:
            # 生成随机价格数据
            np.random.seed(hash(symbol) % 1000)  # 基于symbol的随机种子
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
    
    def run_selection(self, symbols: List[str], 
                     start_date: str, 
                     end_date: str,
                     use_sample_data: bool = False,
                     min_score: float = 0.6,
                     max_stocks: int = 10) -> Dict:
        """
        运行选股流程
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            use_sample_data: 是否使用示例数据
            min_score: 最低评分阈值
            max_stocks: 最大股票数量
            
        Returns:
            选股结果
        """
        print(f"🎯 开始选股流程: {len(symbols)} 只股票")
        print("=" * 60)
        
        # 获取数据
        if use_sample_data:
            stock_data = self.generate_sample_data(symbols)
        else:
            stock_data = self.get_stock_data(symbols, start_date, end_date)
        
        if not stock_data:
            print("❌ 无有效股票数据")
            return {}
        
        # 评分
        print(f"\n📊 对 {len(stock_data)} 只股票进行评分...")
        scoring_results = self.score_stocks(stock_data)
        
        if not scoring_results:
            print("❌ 无评分结果")
            return {}
        
        # 筛选
        print(f"\n🔍 筛选评分 >= {min_score} 的股票...")
        selected_stocks = self.filter_stocks(scoring_results, min_score, max_stocks)
        
        # 保存结果
        self.results = {
            'selected_stocks': selected_stocks,
            'all_scores': scoring_results,
            'stock_data_count': len(stock_data),
            'selection_criteria': {
                'min_score': min_score,
                'max_stocks': max_stocks,
                'date_range': f"{start_date} 到 {end_date}"
            }
        }
        
        return self.results
    
    def print_results(self, results: Optional[Dict] = None):
        """打印选股结果"""
        if results is None:
            results = self.results
        
        if not results or 'selected_stocks' not in results:
            print("❌ 无选股结果")
            return
        
        selected_stocks = results['selected_stocks']
        criteria = results.get('selection_criteria', {})
        
        print("\n" + "=" * 80)
        print("📋 策略评分选股结果")
        print("=" * 80)
        print(f"选股标准: 评分 >= {criteria.get('min_score', 0.6)}, "
              f"最大 {criteria.get('max_stocks', 10)} 只股票")
        print(f"时间范围: {criteria.get('date_range', '未知')}")
        print(f"总共分析: {results.get('stock_data_count', 0)} 只股票")
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
    
    def save_results(self, filename: str, results: Optional[Dict] = None):
        """保存结果到文件"""
        if results is None:
            results = self.results
        
        if not results:
            print("❌ 无结果可保存")
            return
        
        try:
            # 转换为可序列化的格式
            serializable_results = {}
            for key, value in results.items():
                if key == 'selected_stocks':
                    serializable_results[key] = value
                elif key == 'all_scores':
                    # 简化all_scores以便序列化
                    simplified_scores = {}
                    for symbol, score_data in value.items():
                        simplified_scores[symbol] = {
                            'total_score': score_data.get('total_score', 0),
                            'signal': score_data.get('signal', 'UNKNOWN')
                        }
                    serializable_results[key] = simplified_scores
                else:
                    serializable_results[key] = value
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 结果已保存到: {filename}")
            
        except Exception as e:
            print(f"❌ 结果保存失败: {e}")
    
    def cleanup(self):
        """清理资源"""
        print("\n🧹 清理资源...")
        for plugin_name, plugin in self.plugins.items():
            try:
                plugin.cleanup()
                print(f"   ✅ {plugin_name} 清理完成")
            except Exception as e:
                print(f"   ❌ {plugin_name} 清理失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='策略评分选股工具')
    parser.add_argument('--symbols', nargs='+', help='股票代码列表', default=[
        '000001.SZ', '000002.SZ', '000063.SZ', 
        '300001.SZ', '300002.SZ', '600000.SH',
        '600036.SH', '601318.SH'
    ])
    parser.add_argument('--start-date', default='2023-01-01', help='开始日期')
    parser.add_argument('--end-date', default='2023-12-31', help='结束日期')
    parser.add_argument('--min-score', type=float, default=0.6, help='最低评分阈值')
    parser.add_argument('--max-stocks', type=int, default=10, help='最大股票数量')
    parser.add_argument('--use-sample', action='store_true', help='使用示例数据')
    parser.add_argument('--output', help='结果输出文件')
    
    args = parser.parse_args()
    
    print("🎯 ASCEND 策略评分选股工具")
    print("=" * 60)
    
    # 创建选股器
    selector = StockScoringSelector()
    
    try:
        # 初始化插件
        if not selector.initialize_plugins():
            return
        
        # 运行选股
        results = selector.run_selection(
            symbols=args.symbols,
            start_date=args.start_date,
            end_date=args.end_date,
            use_sample_data=args.use_sample,
            min_score=args.min_score,
            max_stocks=args.max_stocks
        )
        
        # 显示结果
        selector.print_results(results)
        
        # 保存结果
        if args.output:
            selector.save_results(args.output, results)
        
        print("✅ 选股完成!")
        
    except Exception as e:
        print(f"❌ 选股过程异常: {e}")
    
    finally:
        # 清理资源
        selector.cleanup()


if __name__ == "__main__":
    main()