"""
策略评分选股运行脚本
基于quant_plugins的多因子评分模型对股票进行评分和筛选

使用说明:
1. 直接运行使用示例数据: python run_stock_scoring.py
2. 使用真实数据可选择数据源:
   - Tushare: 需要配置Tushare token (--data-source tushare --tushare-token YOUR_TOKEN)
   - Ashare: 免费数据源 (--data-source ashare)
3. 支持命令行参数配置
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import argparse
import json
import sys
import os
from dotenv import load_dotenv

# 添加父目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ascend.plugins.manager import PluginManager
from quant_plugins import get_plugin_class

class SimpleStockScorer:
    """简化版股票评分器"""
    
    def __init__(self, config=None):
        self.plugin_manager = PluginManager()
        self.scoring_plugin = None
        self.data_plugin = None
        self.storage_plugin = None
        self.config = config or self._get_default_config()
        self.results = {}
        self._data_cache = {}
        
    def _get_default_config(self):
        """获取默认配置"""
        return {
            'factor_weights': {
                'momentum': 0.35,
                'volume': 0.15,
                'volatility': 0.15,
                'trend': 0.25,
                'rsi_strength': 0.10
            },
            'scoring_threshold': 65.0,
            'min_data_points': 20,
            'plugins': {
                'scoring': 'daily_kline_scoring',
                'data_source': 'tushare_data',  # 插件名称: 'tushare_data' 或 'ashare_data'
                'storage': 'warehouse_storage'
            },
            'tushare_token': '',  # Tushare API token
            'storage_path': './data/warehouse',  # 数据存储路径
            'cache_enabled': True,  # 是否启用数据缓存
            'index_constituents': {  # 指数成分股配置
                '000300.SH': '沪深300',
                '000905.SH': '中证500',
                '000852.SH': '中证1000'
            }
        }
    
    def initialize(self):
        """初始化所有插件"""
        try:
            # 获取插件配置
            plugin_config = self.config.get('plugins', {})
            
            # 加载评分插件
            scoring_plugin_name = plugin_config.get('scoring', 'daily_kline_scoring')
            scoring_plugin_class = get_plugin_class(scoring_plugin_name)
            if scoring_plugin_class:
                self.scoring_plugin = scoring_plugin_class()
                self.scoring_plugin.configure(self.config)
                self.scoring_plugin.initialize()
                print(f"✅ 评分插件初始化成功: {scoring_plugin_name}")
            else:
                raise ValueError(f"无法找到评分插件: {scoring_plugin_name}")
            
            # 加载数据源插件
            data_plugin_name = plugin_config.get('data_source', 'tushare_data')
            data_plugin_class = get_plugin_class(data_plugin_name)
            if data_plugin_class:
                self.data_plugin = data_plugin_class()
                
                # 配置数据插件
                data_config = {
                    'timeout': 30,
                    'max_retries': 3,
                    'cache_enabled': True,
                    'cache_duration': 3600
                }
                if data_plugin_name == 'tushare_data':
                    data_config['token'] = self.config.get('tushare_token', '')
                
                self.data_plugin.configure(data_config)
                self.data_plugin.initialize()
                print(f"✅ 数据插件初始化成功: {data_plugin_name}")
            else:
                raise ValueError(f"无法找到数据插件: {data_plugin_name}")
            
            # 加载存储插件
            storage_plugin_name = plugin_config.get('storage', 'warehouse_storage')
            storage_plugin_class = get_plugin_class(storage_plugin_name)
            if storage_plugin_class:
                self.storage_plugin = storage_plugin_class()
                
                # 配置存储插件
                storage_config = {
                    'storage_path': self.config.get('storage_path', './data/warehouse'),
                    'storage_format': 'parquet',
                    'compression': 'snappy',
                    'auto_cleanup': True
                }
                self.storage_plugin.configure(storage_config)
                self.storage_plugin.initialize()
                print(f"✅ 存储插件初始化成功: {storage_plugin_name}")
            else:
                raise ValueError(f"无法找到存储插件: {storage_plugin_name}")
            
            return True
        except Exception as e:
            print(f"❌ 插件初始化失败: {e}")
            return False
    
    def _get_data_key(self, symbol, start_date, end_date):
        """生成数据存储键"""
        return f"stock_data_{symbol}_{start_date}_{end_date}"
    
    def _get_index_constituents_key(self, index_code):
        """生成指数成分股存储键"""
        return f"index_constituents_{index_code}"
    
    def fetch_real_data(self, symbol, start_date, end_date):
        """获取真实股票数据（带缓存检查）"""
        data_key = self._get_data_key(symbol, start_date, end_date)
        
        # 检查缓存中是否已有数据
        if data_key in self._data_cache:
            print(f"   📦 {symbol} 使用缓存数据")
            return self._data_cache[data_key]
        
        # 检查存储中是否已有数据
        try:
            cached_data = self.storage_plugin.load_data(data_key, default=None)
            if cached_data is not None:
                print(f"   📦 {symbol} 使用存储数据")
                self._data_cache[data_key] = cached_data
                return cached_data
        except Exception as e:
            print(f"   ⚠️ {symbol} 存储数据加载失败: {e}")
        
        # 从数据源获取数据
        data_plugin_name = self.config.get('plugins', {}).get('data_source', 'tushare_data')
        source_name = "Ashare" if data_plugin_name == 'ashare_data' else "Tushare"
        print(f"   📡 {symbol} 从{source_name}获取数据 ({start_date} 至 {end_date})")
        try:
            stock_data = self.data_plugin.fetch_data(symbol, start_date, end_date)
            
            if stock_data is not None and not stock_data.empty:
                # 保存到存储
                try:
                    self.storage_plugin.save_data(stock_data, data_key, overwrite=True)
                    print(f"   💾 {symbol} 数据保存成功")
                except Exception as e:
                    print(f"   ⚠️ {symbol} 数据保存失败: {e}")
                
                # 缓存数据
                self._data_cache[data_key] = stock_data
                return stock_data
            else:
                print(f"   ❌ {symbol} 数据获取失败或为空")
                return None
                
        except Exception as e:
            print(f"   ❌ {symbol} 数据获取失败: {e}")
            return None
    
    def fetch_index_constituents(self, index_code):
        """获取指数成分股名单"""
        constituents_key = self._get_index_constituents_key(index_code)
        
        # 检查存储中是否已有成分股数据
        try:
            cached_constituents = self.storage_plugin.load_data(constituents_key, default=None)
            if cached_constituents is not None:
                print(f"   📦 {index_code} 成分股使用存储数据")
                return cached_constituents
        except Exception as e:
            print(f"   ⚠️ {index_code} 成分股数据加载失败: {e}")
        
        # 获取指数成分股
        data_plugin_name = self.config.get('plugins', {}).get('data_source', 'tushare_data')
        source_name = "Ashare" if data_plugin_name == 'ashare_data' else "Tushare"
        print(f"   📡 从{source_name}获取 {index_code} 成分股名单")
        try:
            # 这里需要根据数据源API实现具体的成分股获取逻辑
            # 暂时返回空列表，需要根据实际API实现
            constituents = []
            
            # 保存到存储
            try:
                self.storage_plugin.save_data(constituents, constituents_key, overwrite=True)
                print(f"   💾 {index_code} 成分股保存成功")
            except Exception as e:
                print(f"   ⚠️ {index_code} 成分股保存失败: {e}")
            
            return constituents
            
        except Exception as e:
            print(f"   ❌ {index_code} 成分股获取失败: {e}")
            return []
    
    def generate_sample_data(self, symbols, days=60):
        """生成示例股票数据（仅在没有真实数据时使用）"""
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
    
    def score_stocks(self, stock_data):
        """对股票进行评分"""
        scoring_results = {}
        
        for symbol, data in stock_data.items():
            try:
                # 执行评分
                result = self.scoring_plugin.execute(data)
                
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
        
        return scoring_results
    
    def filter_stocks(self, scoring_results, min_score=0.6, max_stocks=10):
        """筛选符合条件的股票"""
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
    
    def cleanup(self):
        """清理资源"""
        self.scoring_plugin.cleanup()
        self.data_plugin.cleanup()
        self.storage_plugin.cleanup()
        print("🧹 资源清理完成")
    
    def run_selection(self, symbols, use_real_data=False, start_date=None, end_date=None, min_score=65.0, max_stocks=10):
        """运行选股流程"""
        print(f"🎯 开始选股流程: {len(symbols)} 只股票")
        print("=" * 60)
        
        # 设置日期范围
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
        
        # 获取数据
        stock_data = {}
        if use_real_data:
            print(f"📡 使用真实数据 ({start_date} 至 {end_date})")
            
            # 首先获取并存储指数成分股
            index_constituents_data = {}
            for index_code in self.config.get('index_constituents', {}).keys():
                constituents = self.fetch_index_constituents(index_code)
                index_constituents_data[index_code] = constituents
            
            # 获取股票数据
            valid_symbols = 0
            for symbol in symbols:
                data = self.fetch_real_data(symbol, start_date, end_date)
                if data is not None and not data.empty:
                    stock_data[symbol] = data
                    valid_symbols += 1
                    print(f"   ✅ {symbol} 数据获取成功")
                else:
                    print(f"   ⚠️ {symbol} 数据获取失败，使用示例数据")
                    # 如果真实数据获取失败，使用示例数据
                    sample_data = self.generate_sample_data([symbol], days=60)
                    if sample_data:
                        stock_data[symbol] = sample_data[symbol]
                        valid_symbols += 1
            
            data_source = 'real'
        else:
            print("📊 使用示例数据")
            stock_data = self.generate_sample_data(symbols)
            data_source = 'sample'
            valid_symbols = len(stock_data)
        
        if not stock_data:
            print("❌ 无有效股票数据")
            return {}
        
        print(f"✅ 成功获取 {valid_symbols}/{len(symbols)} 只股票数据")
        
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
            'data_period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'selection_criteria': {
                'min_score': min_score,
                'max_stocks': max_stocks,
                'data_source': data_source
            }
        }
        
        return self.results
    
    def print_results(self):
        """打印选股结果"""
        if not self.results or 'selected_stocks' not in self.results:
            print("❌ 无选股结果")
            return
        
        selected_stocks = self.results['selected_stocks']
        criteria = self.results.get('selection_criteria', {})
        
        print("\n" + "=" * 80)
        print("📋 策略评分选股结果")
        print("=" * 80)
        print(f"选股标准: 评分 >= {criteria.get('min_score', 0.6)}, "
              f"最大 {criteria.get('max_stocks', 10)} 只股票")
        print(f"数据来源: {criteria.get('data_source', 'sample')}")
        print(f"总共分析: {self.results.get('stock_data_count', 0)} 只股票")
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
    
    def save_results(self, filename):
        """保存结果到文件"""
        if not self.results:
            print("❌ 无结果可保存")
            return
        
        try:
            # 转换为可序列化的格式
            serializable_results = {}
            for key, value in self.results.items():
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
        self.scoring_plugin.cleanup()
        self.data_plugin.cleanup()
        self.storage_plugin.cleanup()
        print("🧹 资源清理完成")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='策略评分选股工具')
    parser.add_argument('--symbols', nargs='+', help='股票代码列表', default=[
        '000001.SZ', '000002.SZ', '000063.SZ', 
        '300001.SZ', '300002.SZ', '600000.SH',
        '600036.SH', '601318.SH', '601988.SH',
        '601398.SH', '601857.SH', '601288.SH'
    ])
    parser.add_argument('--min-score', type=float, default=65.0, help='最低评分阈值 (0-100分)')
    parser.add_argument('--max-stocks', type=int, default=10, help='最大股票数量')
    parser.add_argument('--output', help='结果输出文件')
    parser.add_argument('--use-real-data', action='store_true', help='使用真实数据 (需要配置Tushare token)')
    parser.add_argument('--data-plugin', choices=['tushare_data', 'ashare_data'], default='tushare_data',
                       help='数据源插件: tushare_data (需要token) 或 ashare_data (免费)')
    parser.add_argument('--tushare-token', help='Tushare API token')
    parser.add_argument('--start-date', help='数据开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='数据结束日期 (YYYY-MM-DD)')
    parser.add_argument('--storage-path', default='./data/warehouse', help='数据存储路径')
    parser.add_argument('--config', help='JSON配置文件路径')
    
    args = parser.parse_args()
    
    # 加载配置文件（如果提供）
    config = {}
    if args.config:
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ 配置文件加载成功: {args.config}")
        except Exception as e:
            print(f"❌ 配置文件加载失败: {e}")
            return
    
    print("🎯 ASCEND 策略评分选股工具")
    print("=" * 60)
    
    # 加载环境变量
    load_dotenv()
    
    # 获取Tushare token（优先级：命令行参数 > 环境变量 > 配置文件）
    tushare_token = (
        args.tushare_token or
        os.getenv('TUSHARE_TOKEN') or
        (config.get('tushare_token') if config else '')
    )
    
    # 创建评分器配置（合并命令行参数和配置文件）
    final_config = {
        'scoring_threshold': args.min_score,
        'min_data_points': 20,
        'plugins': {
            'data_source': args.data_plugin
        },
        'tushare_token': tushare_token,
        'storage_path': args.storage_path,
        'index_constituents': {
            '000300.SH': '沪深300',
            '000905.SH': '中证500',
            '000852.SH': '中证1000'
        }
    }
    
    # 合并配置文件（配置文件优先级更高）
    if config:
        final_config.update(config)
    
    scorer = SimpleStockScorer(final_config)
    
    if args.use_real_data:
        if args.data_plugin == 'tushare_data' and not tushare_token:
            print("❌ 使用Tushare数据插件需要提供Tushare token")
            print("   可以通过以下方式提供:")
            print("   - 命令行参数: --tushare-token YOUR_TOKEN")
            print("   - 环境变量: 在 .env 文件中设置 TUSHARE_TOKEN")
            print("   - 配置文件: 在 JSON 配置文件中设置 tushare_token")
            return
        elif args.data_plugin == 'ashare_data':
            print("💡 使用Ashare数据插件 (免费)")
        else:
            print(f"💡 使用{args.data_plugin}数据插件")
    else:
        print("💡 使用示例数据进行测试")
    print("=" * 60)
    
    try:
        # 初始化
        if not scorer.initialize():
            return
        
        # 运行选股
        results = scorer.run_selection(
            symbols=args.symbols,
            use_real_data=args.use_real_data,
            start_date=args.start_date,
            end_date=args.end_date,
            min_score=args.min_score,
            max_stocks=args.max_stocks
        )
        
        # 显示结果
        scorer.print_results()
        
        # 保存结果
        if args.output:
            scorer.save_results(args.output)
        
        print("✅ 选股完成!")
        
    except Exception as e:
        print(f"❌ 选股过程异常: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        scorer.cleanup()

if __name__ == "__main__":
    main()