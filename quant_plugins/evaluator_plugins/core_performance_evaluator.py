
"""
核心性能评估器
提供统一的性能指标计算、可视化和报告生成功能
"""

from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


class CorePerformanceEvaluator:
    """核心性能评估器 - 提供统一的性能指标计算和可视化功能"""
    
    def __init__(self, risk_free_rate: float = 0.02):
        self.risk_free_rate = risk_free_rate
        self.metrics_history = []
    
    def calculate_metrics(self, equity_curve: pd.Series, 
                         trades: Optional[List[Dict]] = None,
                         include_advanced: bool = True) -> Dict[str, Any]:
        """计算性能指标
        
        Args:
            equity_curve: 净值曲线
            trades: 交易记录列表，可选
            include_advanced: 是否包含高级指标
            
        Returns:
            性能指标字典
        """
        metrics = {}
        
        if equity_curve.empty:
            return metrics
        
        # 基础指标
        daily_returns = equity_curve.pct_change().dropna()
        total_return = (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1
        
        # 1. 收益指标
        metrics.update(self._calculate_return_metrics(daily_returns, total_return))
        
        # 2. 风险指标
        metrics.update(self._calculate_risk_metrics(daily_returns, equity_curve))
        
        # 3. 风险调整后收益指标
        metrics.update(self._calculate_risk_adjusted_metrics(daily_returns))
        
        # 4. 交易相关指标
        if trades:
            metrics.update(self._calculate_trade_metrics(trades))
        
        # 5. 高级指标（可选）
        if include_advanced:
            metrics.update(self._calculate_time_based_metrics(daily_returns))
            metrics.update(self._calculate_distribution_metrics(daily_returns))
        
        return metrics
    
    def _calculate_return_metrics(self, daily_returns: pd.Series, total_return: float) -> Dict[str, float]:
        """计算收益相关指标"""
        return {
            'total_return': total_return,
            'annualized_return': self._annualize_return(total_return, len(daily_returns)),
            'cagr': self._calculate_cagr(daily_returns),
            'avg_daily_return': daily_returns.mean(),
            'median_daily_return': daily_returns.median(),
            'positive_day_ratio': (daily_returns > 0).mean(),
            'negative_day_ratio': (daily_returns < 0).mean(),
            'best_day': daily_returns.max(),
            'worst_day': daily_returns.min()
        }
    
    def _calculate_risk_metrics(self, daily_returns: pd.Series, equity_curve: pd.Series) -> Dict[str, float]:
        """计算风险相关指标"""
        drawdowns = self._calculate_drawdowns(equity_curve)
        
        return {
            'volatility': daily_returns.std() * np.sqrt(252),
            'downside_volatility': self._calculate_downside_volatility(daily_returns),
            'max_drawdown': drawdowns.max() if not drawdowns.empty else 0,
            'avg_drawdown': drawdowns.mean() if not drawdowns.empty else 0,
            'drawdown_duration': self._calculate_avg_drawdown_duration(drawdowns),
            'value_at_risk_95': self._calculate_var(daily_returns, 0.95),
            'conditional_var_95': self._calculate_cvar(daily_returns, 0.95),
            'ulcer_index': self._calculate_ulcer_index(daily_returns)
        }
    
    def _calculate_risk_adjusted_metrics(self, daily_returns: pd.Series) -> Dict[str, float]:
        """计算风险调整后收益指标"""
        risk_free_rate_daily = self.risk_free_rate / 252
        
        return {
            'sharpe_ratio': self._calculate_sharpe_ratio(daily_returns, risk_free_rate_daily),
            'sortino_ratio': self._calculate_sortino_ratio(daily_returns, risk_free_rate_daily),
            'calmar_ratio': self._calculate_calmar_ratio(daily_returns),
            'omega_ratio': self._calculate_omega_ratio(daily_returns, risk_free_rate_daily),
            'treynor_ratio': self._calculate_treynor_ratio(daily_returns, risk_free_rate_daily),
            'information_ratio': self._calculate_information_ratio(daily_returns)
        }
    
    def _calculate_trade_metrics(self, trades: List[Dict]) -> Dict[str, float]:
        """计算交易相关指标"""
        if not trades:
            return {}
        
        profitable_trades = [t for t in trades if t.get('profit_loss', 0) > 0]
        losing_trades = [t for t in trades if t.get('profit_loss', 0) < 0]
        
        win_rate = len(profitable_trades) / len(trades) if trades else 0
        avg_profit = np.mean([t.get('profit_loss', 0) for t in profitable_trades]) if profitable_trades else 0
        avg_loss = np.mean([t.get('profit_loss', 0) for t in losing_trades]) if losing_trades else 0
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(profitable_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'profit_factor': abs(avg_profit * len(profitable_trades) / 
                               (avg_loss * len(losing_trades))) if losing_trades else float('inf'),
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'largest_win': max([t.get('profit_loss', 0) for t in profitable_trades]) if profitable_trades else 0,
            'largest_loss': min([t.get('profit_loss', 0) for t in losing_trades]) if losing_trades else 0,
            'avg_trade_return': np.mean([t.get('profit_loss', 0) for t in trades]) if trades else 0,
            'profit_ratio': avg_profit / abs(avg_loss) if avg_loss != 0 else float('inf'),
            'expectancy': (win_rate * avg_profit) - ((1 - win_rate) * abs(avg_loss)),
            'k_ratio': self._calculate_k_ratio(trades)
        }
    
    def _calculate_time_based_metrics(self, daily_returns: pd.Series) -> Dict[str, float]:
        """计算时间相关指标"""
        return {
            'monthly_win_ratio': self._calculate_monthly_win_ratio(daily_returns),
            'quarterly_consistency': self._calculate_quarterly_consistency(daily_returns),
            'yearly_performance': self._calculate_yearly_performance(daily_returns),
            'time_in_market': self._calculate_time_in_market(daily_returns)
        }
    
    def _calculate_distribution_metrics(self, daily_returns: pd.Series) -> Dict[str, float]:
        """计算分布相关指标"""
        return {
            'skewness': daily_returns.skew(),
            'kurtosis': daily_returns.kurtosis(),
            'jarque_bera': stats.jarque_bera(daily_returns)[0],
            'normality_pvalue': stats.normaltest(daily_returns)[1],
            'tail_ratio': self._calculate_tail_ratio(daily_returns)
        }
    
    # 辅助计算方法
    def _annualize_return(self, total_return: float, days: int) -> float:
        """年化收益率"""
        years = days / 252
        return (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
    
    def _calculate_cagr(self, returns: pd.Series) -> float:
        """计算复合年增长率"""
        if len(returns) < 2:
            return 0
        total_return = (1 + returns).prod() - 1
        years = len(returns) / 252
        return (1 + total_return) ** (1 / years) - 1
    
    def _calculate_drawdowns(self, equity_curve: pd.Series) -> pd.Series:
        """计算回撤序列"""
        rolling_max = equity_curve.expanding().max()
        return (equity_curve - rolling_max) / rolling_max
    
    def _calculate_avg_drawdown_duration(self, drawdowns: pd.Series) -> float:
        """计算平均回撤持续时间"""
        if drawdowns.empty:
            return 0
        
        in_drawdown = drawdowns < 0
        durations = []
        current_duration = 0
        
        for in_dd in in_drawdown:
            if in_dd:
                current_duration += 1
            elif current_duration > 0:
                durations.append(current_duration)
                current_duration = 0
        
        return np.mean(durations) if durations else 0
    
    def _calculate_downside_volatility(self, returns: pd.Series) -> float:
        """计算下行波动率"""
        downside_returns = returns[returns < 0]
        return downside_returns.std() * np.sqrt(252) if len(downside_returns) > 1 else 0
    
    def _calculate_var(self, returns: pd.Series, confidence: float) -> float:
        """计算风险价值"""
        return returns.quantile(1 - confidence)
    
    def _calculate_cvar(self, returns: pd.Series, confidence: float) -> float:
        """计算条件风险价值"""
        var = self._calculate_var(returns, confidence)
        tail_returns = returns[returns <= var]
        return tail_returns.mean() if not tail_returns.empty else 0
    
    def _calculate_ulcer_index(self, returns: pd.Series) -> float:
        """计算溃疡指数"""
        equity_curve = (1 + returns).cumprod()
        drawdowns = self._calculate_drawdowns(equity_curve)
        return np.sqrt((drawdowns ** 2).mean())
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float) -> float:
        """计算夏普比率"""
        excess_returns = returns - risk_free_rate
        return excess_returns.mean() / excess_returns.std() * np.sqrt(252) if len(excess_returns) > 1 else 0
    
    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float) -> float:
        """计算索提诺比率"""
        excess_returns = returns - risk_free_rate
        downside_returns = excess_returns[excess_returns < 0]
        return excess_returns.mean() / downside_returns.std() * np.sqrt(252) if len(downside_returns) > 1 else 0
    
    def _calculate_calmar_ratio(self, returns: pd.Series) -> float:
        """计算Calmar比率"""
        equity_curve = (1 + returns).cumprod()
        max_drawdown = self._calculate_drawdowns(equity_curve).max()
        annual_return = self._annualize_return(equity_curve.iloc[-1] / equity_curve.iloc[0] - 1, len(returns))
        return annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
    
    def _calculate_omega_ratio(self, returns: pd.Series, threshold: float) -> float:
        """计算Omega比率"""
        gains = returns[returns > threshold].sum()
        losses = returns[returns <= threshold].sum()
        return gains / abs(losses) if losses != 0 else float('inf')
    
    def _calculate_treynor_ratio(self, returns: pd.Series, risk_free_rate: float) -> float:
        """计算特雷诺比率"""
        # 简化版本，实际需要beta值
        excess_returns = returns - risk_free_rate
        return excess_returns.mean() * 252
    
    def _calculate_information_ratio(self, returns: pd.Series) -> float:
        """计算信息比率"""
        # 简化版本，实际需要基准数据
        return returns.mean() / returns.std() * np.sqrt(252) if len(returns) > 1 else 0
    
    def _calculate_k_ratio(self, trades: List[Dict]) -> float:
        """计算K比率"""
        if not trades or len(trades) < 2:
            return 0
        
        profits = [t.get('profit_loss', 0) for t in trades]
        returns = np.diff(profits) / np.abs(profits[:-1])
        return returns.mean() / returns.std() if returns.std() > 0 else 0
    
    def _calculate_monthly_win_ratio(self, returns: pd.Series) -> float:
        """计算月度胜率"""
        if hasattr(returns, 'resample'):
            monthly_returns = returns.resample('M').sum()
            return (monthly_returns > 0).mean()
        return 0
    
    def _calculate_quarterly_consistency(self, returns: pd.Series) -> float:
        """计算季度一致性"""
        if hasattr(returns, 'resample'):
            quarterly_returns = returns.resample('Q').sum()
            return (quarterly_returns > 0).mean()
        return 0
    
    def _calculate_yearly_performance(self, returns: pd.Series) -> Dict[str, float]:
        """计算年度表现"""
        if hasattr(returns, 'resample'):
            yearly_returns = returns.resample('Y').sum()
            return {
                'best_year': yearly_returns.max(),
                'worst_year': yearly_returns.min(),
                'avg_year': yearly_returns.mean()
            }
        return {}
    
    def _calculate_time_in_market(self, returns: pd.Series) -> float:
        """计算在市场中时间比例"""
        return (returns != 0).mean()
    
    def _calculate_tail_ratio(self, returns: pd.Series) -> float:
        """计算尾比"""
        positive_tail = returns.quantile(0.95)
        negative_tail = returns.quantile(0.05)
        return abs(positive_tail / negative_tail) if negative_tail != 0 else float('inf')
    
    def compare_with_benchmark(self, equity_curve: pd.Series,
                              benchmark: pd.Series) -> Dict[str, Any]:
        """与基准对比分析"""
        try:
            if equity_curve.empty or benchmark.empty:
                return {
                    'outperformance': 0.0,
                    'correlation': 0.0,
                    'beta': 1.0,
                    'alpha': 0.0,
                    'error': 'Empty data provided'
                }
            
            # 确保时间索引对齐
            aligned_data = pd.DataFrame({
                'strategy': equity_curve,
                'benchmark': benchmark
            }).dropna()
            
            if len(aligned_data) < 2:
                return {
                    'outperformance': 0.0,
                    'correlation': 0.0,
                    'beta': 1.0,
                    'alpha': 0.0,
                    'error': 'Insufficient data for comparison'
                }
            
            strategy_returns = aligned_data['strategy'].pct_change().dropna()
            benchmark_returns = aligned_data['benchmark'].pct_change().dropna()
            
            # 计算超额收益
            outperformance = (aligned_data['strategy'].iloc[-1] / aligned_data['strategy'].iloc[0] - 1) - \
                           (aligned_data['benchmark'].iloc[-1] / aligned_data['benchmark'].iloc[0] - 1)
            
            # 计算相关性
            correlation = strategy_returns.corr(benchmark_returns)
            
            # 计算Beta (市场风险暴露)
            covariance = np.cov(strategy_returns, benchmark_returns)[0, 1]
            benchmark_variance = np.var(benchmark_returns)
            beta = covariance / benchmark_variance if benchmark_variance != 0 else 1.0
            
            # 计算Alpha (超额收益)
            risk_free_rate_daily = self.risk_free_rate / 252
            alpha = np.mean(strategy_returns - risk_free_rate_daily) - beta * np.mean(benchmark_returns - risk_free_rate_daily)
            
            return {
                'outperformance': outperformance,
                'correlation': correlation,
                'beta': beta,
                'alpha': alpha,
                'tracking_error': np.std(strategy_returns - benchmark_returns),
                'information_ratio': (np.mean(strategy_returns - benchmark_returns) /
                                    np.std(strategy_returns - benchmark_returns)) if np.std(strategy_returns - benchmark_returns) != 0 else 0
            }
            
        except Exception as e:
            return {
                'outperformance': 0.0,
                'correlation': 0.0,
                'beta': 1.0,
                'alpha': 0.0,
                'error': str(e)
            }
    
    def generate_performance_report(self, metrics: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """生成性能报告"""
        report = [
            "📊 量化策略性能报告",
            "=" * 50,
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "🎯 收益表现:",
            f"  总收益率: {metrics.get('total_return', 0):.2%}",
            f"  年化收益率: {metrics.get('annualized_return', 0):.2%}",
            f"  复合年增长率: {metrics.get('cagr', 0):.2%}",
            "",
            "⚠️ 风险指标:",
            f"  年化波动率: {metrics.get('volatility', 0):.2%}",
            f"  最大回撤: {metrics.get('max_drawdown', 0):.2%}",
            f"  下行波动率: {metrics.get('downside_volatility', 0):.2%}",
            f"  VaR(95%): {metrics.get('value_at_risk_95', 0):.2%}",
            "",
            "📈 风险调整后收益:",
            f"  夏普比率: {metrics.get('sharpe_ratio', 0):.2f}",
            f"  索提诺比率: {metrics.get('sortino_ratio', 0):.2f}",
            f"  Calmar比率: {metrics.get('calmar_ratio', 0):.2f}",
            f"  Omega比率: {metrics.get('omega_ratio', 0):.2f}",
            "",
            "💼 交易统计:",
            f"  胜率: {metrics.get('win_rate', 0):.2%}",
            f"  盈亏比: {metrics.get('profit_factor', 0):.2f}",
            f"  期望值: {metrics.get('expectancy', 0):.2f}",
            f"  K比率: {metrics.get('k_ratio', 0):.2f}"
        ]
        
        report_text = "\n".join(report)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
        
        return report_text
    
    def plot_performance_charts(self, equity_curve: pd.Series,
                              metrics: Dict[str, Any],
                              output_path: Optional[str] = None):
        """绘制性能图表"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('量化策略性能分析', fontsize=16, fontweight='bold')
        
        # 1. 净值曲线
        axes[0, 0].plot(equity_curve.index, equity_curve.values, linewidth=2, color='blue')
        axes[0, 0].set_title('净值曲线', fontsize=14, fontweight='bold')
        axes[0, 0].set_ylabel('净值', fontsize=12)
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. 回撤曲线
        drawdowns = self._calculate_drawdowns(equity_curve)
        axes[0, 1].fill_between(drawdowns.index, drawdowns.values, 0, alpha=0.3, color='red')
        axes[0, 1].set_title('回撤曲线', fontsize=14, fontweight='bold')
        axes[0, 1].set_ylabel('回撤比例', fontsize=12)
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. 收益率分布
        returns = equity_curve.pct_change().dropna()
        axes[1, 0].hist(returns, bins=50, alpha=0.7, color='green', edgecolor='black')
        axes[1, 0].set_title('收益率分布', fontsize=14, fontweight='bold')
        axes[1, 0].set_xlabel('日收益率', fontsize=12)
        
        # 4. 月度表现热力图
        if hasattr(returns, 'resample'):
            monthly_returns = returns.resample('M').sum()
            monthly_matrix = monthly_returns.unstack()
            if not monthly_matrix.empty:
                sns.heatmap(monthly_matrix, annot=True, fmt='.2%', cmap='RdYlGn',
                           center=0, ax=axes[1, 1])
                axes[1, 1].set_title('月度收益率热力图', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
        else:
            plt.show()