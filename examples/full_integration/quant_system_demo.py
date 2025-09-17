"""
ASCEND 完整量化系统演示 (quant_system_demo.py)
展示如何使用所有量化插件构建完整的量化交易系统

功能:
- 数据获取 → 数据预处理 → 策略执行 → 回测 → 性能评估 → 实时监控
- 完整的插件生命周期管理
- 错误处理和日志记录
- 配置管理和结果可视化
- 完整的量化交易管道
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

from ascend.plugins.manager import PluginManager
from ascend.core.exceptions import PluginError

# 导入所有量化插件
from quant_plugins.data_plugins import (
    TushareDataPlugin, 
    DataPreprocessingPlugin,
    WarehouseStoragePlugin
)
from quant_plugins.strategy_plugins import (
    DailyKlineScoringPlugin
)
from quant_plugins.backtest_plugins import (
    DailyBacktestEnginePlugin,
    PerformanceEvaluatorPlugin
)
from quant_plugins.execution_plugins import (
    SimTraderPlugin,
    RealtimeMonitorPlugin
)


class QuantTradingSystem:
    """量化交易系统 - 完整的插件集成示例"""
    
    def __init__(self):
        self.plugin_manager = PluginManager()
        self.plugins = {}
        self.results = {}
        
    async def initialize_system(self):
        """初始化整个量化交易系统"""
        print("🚀 初始化量化交易系统")
        print("=" * 60)
        
        try:
            # 配置所有插件
            plugin_configs = {
                # 数据插件配置
                'tushare_data': {
                    'token': 'your_tushare_token_here',  # 需要替换为实际token
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
                },
                
                # 策略插件配置
                'daily_kline_scoring': {
                    'factor_weights': {
                        'momentum': 0.35,
                        'volume': 0.15,
                        'volatility': 0.15,
                        'trend': 0.25,
                        'rsi_strength': 0.10
                    },
                    'scoring_threshold': 0.65
                },
                
                # 回测插件配置
                'daily_backtest_engine': {
                    'initial_capital': 1000000.0,
                    'commission': 0.0003,
                    'slippage': 0.0001,
                    'max_position_per_stock': 0.2
                },
                'performance_evaluator': {
                    'risk_free_rate': 0.02,
                    'calc_daily_metrics': True
                },
                
                # 执行插件配置
                'sim_trader': {
                    'initial_capital': 1000000.0,
                    'commission_rate': 0.0003,
                    'slippage_rate': 0.0001
                },
                'realtime_monitor': {
                    'monitoring_interval': 60,
                    'log_level': 'INFO'
                }
            }
            
            # 加载和初始化所有插件
            plugin_names = [
                'tushare_data', 'data_preprocessing', 'warehouse_storage',
                'daily_kline_scoring', 
                'daily_backtest_engine', 'performance_evaluator',
                'sim_trader', 'realtime_monitor'
            ]
            
            for plugin_name in plugin_names:
                print(f"🔌 加载插件: {plugin_name}")
                
                plugin = self.plugin_manager.load_plugin(plugin_name)
                config = plugin_configs.get(plugin_name, {})
                plugin.configure(config)
                plugin.initialize()
                
                self.plugins[plugin_name] = plugin
                print(f"   ✅ {plugin_name} 初始化成功")
            
            print("\n✅ 所有插件加载完成!")
            return True
            
        except Exception as e:
            print(f"❌ 系统初始化失败: {e}")
            return False
    
    async def run_full_pipeline(self, symbols=None, start_date='2023-01-01', end_date='2023-06-30'):
        """运行完整的量化管道"""
        print(f"\n🎯 运行完整量化管道: {start_date} 到 {end_date}")
        print("=" * 60)
        
        try:
            # 1. 数据获取
            print("1. 📊 数据获取阶段")
            stock_data = await self._fetch_data(symbols, start_date, end_date)
            if not stock_data:
                print("   ⚠️ 数据获取失败，使用模拟数据")
                stock_data = self._generate_sample_data()
            
            # 2. 数据预处理
            print("2. 🔧 数据预处理阶段")
            processed_data = await self._preprocess_data(stock_data)
            
            # 3. 策略执行
            print("3. 🎯 策略执行阶段")
            strategy_results = await self._execute_strategy(processed_data)
            
            # 4. 回测验证
            print("4. 📈 回测验证阶段")
            backtest_results = await self._run_backtest(strategy_results, processed_data)
            
            # 5. 性能评估
            print("5. 📊 性能评估阶段")
            performance_metrics = await self._evaluate_performance(backtest_results)
            
            # 6. 实时监控
            print("6. 👁️ 实时监控阶段")
            await self._start_monitoring(performance_metrics)
            
            # 保存结果
            self.results = {
                'stock_data': stock_data,
                'processed_data': processed_data,
                'strategy_results': strategy_results,
                'backtest_results': backtest_results,
                'performance_metrics': performance_metrics
            }
            
            print("\n✅ 完整管道运行完成!")
            return True
            
        except Exception as e:
            print(f"❌ 管道运行失败: {e}")
            return False
    
    async def _fetch_data(self, symbols, start_date, end_date):
        """获取股票数据"""
        try:
            tushare_plugin = self.plugins['tushare_data']
            storage_plugin = self.plugins['warehouse_storage']
            
            if symbols is None:
                symbols = tushare_plugin.get_available_symbols()[:5]  # 只取5个股票
            
            print(f"   获取 {len(symbols)} 只股票数据")
            
            all_data = {}
            for symbol in symbols:
                try:
                    # 尝试从存储加载
                    cached_data = storage_plugin.load_data(f"{symbol}_{start_date}_{end_date}")
                    if cached_data is not None:
                        print(f"   ✅ {symbol} 从缓存加载")
                        all_data[symbol] = cached_data
                        continue
                    
                    # 从API获取
                    print(f"   📡 获取 {symbol} 数据...")
                    data = tushare_plugin.fetch_data(
                        symbol=symbol,
                        start_date=start_date,
                        end_date=end_date,
                        data_type='daily',
                        adjust='qfq'
                    )
                    
                    if not data.empty:
                        # 保存到存储
                        storage_plugin.save_data(data, f"{symbol}_{start_date}_{end_date}")
                        all_data[symbol] = data
                        print(f"   ✅ {symbol} 获取成功 ({len(data)} 条记录)")
                    else:
                        print(f"   ⚠️ {symbol} 无数据")
                        
                except Exception as e:
                    print(f"   ❌ {symbol} 数据获取失败: {e}")
            
            return all_data
            
        except Exception as e:
            print(f"   数据获取失败: {e}")
            return None
    
    async def _preprocess_data(self, stock_data):
        """数据预处理"""
        try:
            preprocessing_plugin = self.plugins['data_preprocessing']
            processed_data = {}
            
            for symbol, data in stock_data.items():
                try:
                    # 数据清洗
                    cleaned_data = preprocessing_plugin.clean_data(data)
                    
                    # 缺失值处理
                    processed_data = preprocessing_plugin.handle_missing_values(cleaned_data)
                    
                    # 特征工程
                    featured_data = preprocessing_plugin.extract_features(processed_data)
                    
                    processed_data[symbol] = featured_data
                    print(f"   ✅ {symbol} 预处理完成")
                    
                except Exception as e:
                    print(f"   ❌ {symbol} 预处理失败: {e}")
            
            return processed_data
            
        except Exception as e:
            print(f"   数据预处理失败: {e}")
            return None
    
    async def _execute_strategy(self, processed_data):
        """执行策略"""
        try:
            strategy_plugin = self.plugins['daily_kline_scoring']
            strategy_results = {}
            
            for symbol, data in processed_data.items():
                try:
                    # 执行评分策略
                    result = strategy_plugin.execute(data)
                    strategy_results[symbol] = result
                    print(f"   ✅ {symbol} 策略执行完成 - 评分: {result.get('total_score', 0):.3f}")
                    
                except Exception as e:
                    print(f"   ❌ {symbol} 策略执行失败: {e}")
            
            return strategy_results
            
        except Exception as e:
            print(f"   策略执行失败: {e}")
            return None
    
    async def _run_backtest(self, strategy_results, processed_data):
        """运行回测"""
        try:
            backtest_plugin = self.plugins['daily_backtest_engine']
            strategy_plugin = self.plugins['daily_kline_scoring']
            
            # 这里简化实现，实际应该按时间序列回测
            print("   运行回测...")
            
            # 使用第一个股票的数据进行示例回测
            if processed_data:
                first_symbol = list(processed_data.keys())[0]
                sample_data = processed_data[first_symbol]
                
                # 运行回测
                backtest_result = backtest_plugin.run_backtest(strategy_plugin, sample_data)
                print(f"   ✅ 回测完成 - 最终权益: {backtest_result['performance']['final_equity']:,.2f}")
                
                return backtest_result
            
            return None
            
        except Exception as e:
            print(f"   回测失败: {e}")
            return None
    
    async def _evaluate_performance(self, backtest_results):
        """性能评估"""
        try:
            performance_plugin = self.plugins['performance_evaluator']
            
            if backtest_results and 'equity_curve' in backtest_results:
                equity_curve = backtest_results['equity_curve']
                trades = backtest_results.get('trade_history', [])
                
                metrics = performance_plugin.calculate_metrics(equity_curve, trades)
                print(f"   ✅ 性能评估完成 - 夏普比率: {metrics.get('sharpe_ratio', 0):.2f}")
                
                return metrics
            
            return None
            
        except Exception as e:
            print(f"   性能评估失败: {e}")
            return None
    
    async def _start_monitoring(self, performance_metrics):
        """启动实时监控"""
        try:
            monitor_plugin = self.plugins['realtime_monitor']
            
            if performance_metrics:
                # 开始监控
                monitor_plugin.monitor_performance(performance_metrics)
                print("   ✅ 实时监控启动")
            
        except Exception as e:
            print(f"   监控启动失败: {e}")
    
    def _generate_sample_data(self):
        """生成示例数据（用于测试）"""
        print("   生成示例数据...")
        
        # 生成示例股票数据
        dates = pd.date_range('2023-01-01', '2023-06-30', freq='D')
        symbols = ['000001.SZ', '000002.SZ', '600000.SH']
        
        sample_data = {}
        for symbol in symbols:
            # 生成随机价格数据
            np.random.seed(42)  # 固定随机种子以便复现
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
        
        return sample_data
    
    def generate_report(self):
        """生成报告"""
        if not self.results:
            print("❌ 没有可用的结果数据")
            return
        
        print("\n📋 量化交易系统报告")
        print("=" * 60)
        
        # 显示性能指标
        metrics = self.results.get('performance_metrics', {})
        if metrics:
            print("📊 性能指标:")
            print(f"   总收益率: {metrics.get('total_return', 0):.2%}")
            print(f"   年化收益率: {metrics.get('annualized_return', 0):.2%}")
            print(f"   夏普比率: {metrics.get('sharpe_ratio', 0):.2f}")
            print(f"   最大回撤: {metrics.get('max_drawdown', 0):.2%}")
            print(f"   波动率: {metrics.get('volatility', 0):.2%}")
        
        # 显示交易统计
        backtest_results = self.results.get('backtest_results', {})
        if backtest_results and 'trades' in backtest_results:
            trades = backtest_results['trades']
            print(f"\n💼 交易统计:")
            print(f"   总交易次数: {trades.get('total_trades', 0)}")
            print(f"   胜率: {trades.get('win_rate', 0):.2%}")
            print(f"   盈亏比: {trades.get('profit_factor', 0):.2f}")
    
    async def cleanup(self):
        """清理资源"""
        print("\n🧹 清理资源...")
        for plugin_name, plugin in self.plugins.items():
            try:
                plugin.cleanup()
                print(f"   ✅ {plugin_name} 清理完成")
            except Exception as e:
                print(f"   ❌ {plugin_name} 清理失败: {e}")


async def main():
    """主函数"""
    print("🎯 ASCEND 量化交易系统完整示例")
    print("=" * 60)
    
    # 创建系统实例
    system = QuantTradingSystem()
    
    try:
        # 初始化系统
        if not await system.initialize_system():
            return
        
        # 运行完整管道
        success = await system.run_full_pipeline(
            symbols=['000001.SZ', '000002.SZ'],  # 测试用2只股票
            start_date='2023-01-01',
            end_date='2023-03-31'
        )
        
        if success:
            # 生成报告
            system.generate_report()
            
            print("\n✅ 示例运行成功!")
            print("💡 提示: 在实际使用中，请配置真实的Tushare token和数据源")
            
        else:
            print("\n❌ 示例运行失败")
        
    except Exception as e:
        print(f"❌ 系统运行异常: {e}")
    
    finally:
        # 清理资源
        await system.cleanup()
    
    print("\n" + "=" * 60)
    print("🎉 示例运行完成!")


if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())