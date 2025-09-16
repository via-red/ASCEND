"""
性能评估器插件
提供详细的回测性能评估和指标计算

功能:
- 计算各种性能指标 (收益率、夏普比率、最大回撤等)
- 生成详细的性能报告
- 与基准对比分析
- 交易统计和分析
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, field_validator
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings

from ascend.plugins.base import BasePlugin
from ascend.core.exceptions import PluginError
from . import IPerformanceEvaluator

# 插件配置模型
class PerformanceEvaluatorPluginConfig(BaseModel):
    """性能评估器配置"""
    
    risk_free_rate: float = Field(0.02, description="无风险利率")
    benchmark_symbol: str = Field("000300.SH", description="基准指数代码")
    calc_daily_metrics: bool = Field(True, description="是否计算每日指标")
    enable_detailed_stats: bool = Field(True, description="是否启用详细统计")
    max_lookback_period: int = Field(252, description="最大回看周期")
    
    @field_validator('risk_free_rate')
    def validate_risk_free_rate(cls, v):
        if v < 0:
            raise ValueError('Risk free rate cannot be negative')
        return v


class PerformanceEvaluatorPlugin(BasePlugin, IPerformanceEvaluator):
    """性能评估器插件实现"""
    
    def __init__(self):
        super().__init__(
            name="performance_evaluator",
            version="1.0.0",
            description="性能评估器插件，提供详细的回测性能指标计算",
            author="ASCEND Team",
            license="Apache 2.0"
        )
        self._metrics_cache = {}
    
    def get_config_schema(self) -> Optional[type]:
        """获取配置模型"""
        return PerformanceEvaluatorPluginConfig
    
    def _initialize(self) -> None:
        """初始化性能评估器"""
        self._metrics_cache = {}
    
    def calculate_metrics(self, equity_curve: pd.Series, 
                         trades: List[Dict], **kwargs) -> Dict[str, float]:
        """计算性能指标
        
        Args:
            equity_curve: 净值曲线
            trades: 交易记录列表
            **kwargs: 额外参数
            
        Returns:
            性能指标字典
        """
        try:
            if equity_curve.empty:
                return {}
            
            metrics = {}
            
            # 基础收益指标
            metrics.update(self._calculate_return_metrics(equity_curve))
            
            # 风险指标
            metrics.update(self._calculate_risk_metrics(equity_curve))
            
            # 风险调整后收益指标
            metrics.update(self._calculate_risk_adjusted_metrics(equity_curve))
            
            # 交易统计指标
            if trades:
                metrics.update(self._calculate_trade_metrics(trades))
            
            # 时间相关指标
            metrics.update(self._calculate_time_based_metrics(equity_curve))
            
            # 缓存计算结果
            self._metrics_cache = metrics
            
            return metrics
            
        except Exception as e:
            raise PluginError(f"Metrics calculation failed: {e}")
    
    def _calculate_return_metrics(self, equity_curve: pd.Series) -> Dict[str, float]:
        """计算收益指标"""
        initial_equity = equity_curve.iloc[0]
        final_equity = equity_curve.iloc[-1]
        total_return = (final_equity / initial_equity) - 1
        
        # 计算每日收益率
        daily_returns = equity_curve.pct_change().dropna()
        
        return {
            'total_return': total_return,
            'annualized_return': self._calc_annualized_return(total_return, len(equity_curve)),
            'avg_daily_return': daily_returns.mean(),
            'median_daily_return': daily_returns.median(),
            'positive_days': (daily_returns > 0).sum() / len(daily_returns),
            'negative_days': (daily_returns < 0).sum() / len(daily_returns)
        }
    
    def _calculate_risk_metrics(self, equity_curve: pd.Series) -> Dict[str, float]:
        """计算风险指标"""
        daily_returns = equity_curve.pct_change().dropna()
        
        # 计算回撤系列
        drawdowns = self._calculate_drawdown_series(equity_curve)
        
        return {
            'volatility': daily_returns.std() * np.sqrt(252),
            'max_drawdown': drawdowns.max() if not drawdowns.empty else 0,
            'avg_drawdown': drawdowns.mean() if not drawdowns.empty else 0,
            'drawdown_duration': self._calc_avg_drawdown_duration(drawdowns),
            'downside_volatility': self._calc_downside_volatility(daily_returns),
            'value_at_risk_95': self._calc_var(daily_returns, 0.95),
            'conditional_var_95': self._calc_cvar(daily_returns, 0.95)
        }
    
    def _calculate_risk_adjusted_metrics(self, equity_curve: pd.Series) -> Dict[str, float]:
        """计算风险调整后收益指标"""
        daily_returns = equity_curve.pct_change().dropna()
        risk_free_rate = self.config.get('risk_free_rate', 0.02) / 252
        
        excess_returns = daily_returns - risk_free_rate
        negative_returns = daily_returns[daily_returns < 0]
        
        sharpe = np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252) if len(excess_returns) > 1 else 0
        sortino = np.mean(excess_returns) / np.std(negative_returns) * np.sqrt(252) if len(negative_returns) > 1 else 0
        
        calmar = self._calc_calmar_ratio(equity_curve)
        omega = self._calc_omega_ratio(daily_returns, risk_free_rate)
        
        return {
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            'omega_ratio': omega,
            'information_ratio': self._calc_information_ratio(daily_returns),
            'treynor_ratio': self._calc_treynor_ratio(daily_returns, risk_free_rate)
        }
    
    def _calculate_trade_metrics(self, trades: List[Dict]) -> Dict[str, float]:
        """计算交易统计指标"""
        if not trades:
            return {}
        
        profitable_trades = [t for t in trades if t.get('profit_loss', 0) > 0]
        losing_trades = [t for t in trades if t.get('profit_loss', 0) < 0]
        
        win_rate = len(profitable_trades) / len(trades) if trades else 0
        
        avg_profit = np.mean([t.get('profit_loss', 0) for t in profitable_trades]) if profitable_trades else 0
        avg_loss = np.mean([t.get('profit_loss', 0) for t in losing_trades]) if losing_trades else 0
        
        profit_factor = abs(avg_profit * len(profitable_trades) / 
                           (avg_loss * len(losing_trades))) if losing_trades else float('inf')
        
        return {
            'total_trades': len(trades),
            'winning_trades': len(profitable_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_profit': avg_profit,
            'avg_loss': avg_loss,
            'largest_win': max([t.get('profit_loss', 0) for t in profitable_trades]) if profitable_trades else 0,
            'largest_loss': min([t.get('profit_loss', 0) for t in losing_trades]) if losing_trades else 0,
            'avg_trade_return': np.mean([t.get('profit_loss', 0) for t in trades]) if trades else 0
        }
    
    def _calculate_time_based_metrics(self, equity_curve: pd.Series) -> Dict[str, float]:
        """计算时间相关指标"""
        daily_returns = equity_curve.pct_change().dropna()
        
        # 计算滚动指标
        rolling_sharpe = self._calc_rolling_sharpe(daily_returns)
        rolling_volatility = daily_returns.rolling(63).std() * np.sqrt(252)
        
        return {
            'rolling_sharpe_avg': rolling_sharpe.mean() if not rolling_sharpe.empty else 0,
            'rolling_sharpe_std': rolling_sharpe.std() if not rolling_sharpe.empty else 0,
            'rolling_volatility_avg': rolling_volatility.mean() if not rolling_volatility.empty else 0,
            'best_month': daily_returns.resample('M').sum().max() if hasattr(daily_returns, 'resample') else 0,
            'worst_month': daily_returns.resample('M').sum().min() if hasattr(daily_returns, 'resample') else 0
        }
    
    def _calculate_drawdown_series(self, equity_curve: pd.Series) -> pd.Series:
        """计算回撤系列"""
        rolling_max = equity_curve.expanding().max()
        drawdowns = (equity_curve - rolling_max) / rolling_max
        return drawdowns
    
    def _calc_annualized_return(self, total_return: float, periods: int) -> float:
        """计算年化收益率"""
        years = periods / 252
        return (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
    
    def _calc_avg_drawdown_duration(self, drawdowns: pd.Series) -> float:
        """计算平均回撤持续时间"""
        if drawdowns.empty:
            return 0
        
        # 识别回撤期间
        in_drawdown = drawdowns < 0
        drawdown_periods = in_drawdown.astype(int)
        
        # 计算连续回撤天数
        drawdown_durations = []
        current_duration = 0
        
        for in_dd in drawdown_periods:
            if in_dd:
                current_duration += 1
            elif current_duration > 0:
                drawdown_durations.append(current_duration)
                current_duration = 0
        
        return np.mean(drawdown_durations) if drawdown_durations else 0
    
    def _calc_downside_volatility(self, returns: pd.Series) -> float:
        """计算下行波动率"""
        negative_returns = returns[returns < 0]
        return negative_returns.std() * np.sqrt(252) if len(negative_returns) > 1 else 0
    
    def _calc_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """计算风险价值 (VaR)"""
        return returns.quantile(1 - confidence)
    
    def _calc_cvar(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """计算条件风险价值 (CVaR)"""
        var = self._calc_var(returns, confidence)
        tail_returns = returns[returns <= var]
        return tail_returns.mean() if not tail_returns.empty else 0
    
    def _calc_calmar_ratio(self, equity_curve: pd.Series) -> float:
        """计算Calmar比率"""
        annual_return = self._calc_annualized_return(
            (equity_curve.iloc[-1] / equity_curve.iloc[0]) - 1,
            len(equity_curve)
        )
        max_drawdown = self._calculate_drawdown_series(equity_curve).max()
        return annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
    
    def _calc_omega_ratio(self, returns: pd.Series, threshold: float) -> float:
        """计算Omega比率"""
        gains = returns[returns > threshold].sum()
        losses = returns[returns <= threshold].sum()
        return gains / abs(losses) if losses != 0 else float('inf')
    
    def _calc_information_ratio(self, returns: pd.Series) -> float:
        """计算信息比率"""
        # 这里简化实现，实际应该与基准对比
        return returns.mean() / returns.std() * np.sqrt(252) if len(returns) > 1 else 0
    
    def _calc_treynor_ratio(self, returns: pd.Series, risk_free_rate: float) -> float:
        """计算特雷诺比率"""
        # 这里简化实现，实际需要beta值
        excess_returns = returns - risk_free_rate
        return excess_returns.mean() * 252  # 简化版本
    
    def _calc_rolling_sharpe(self, returns: pd.Series, window: int = 63) -> pd.Series:
        """计算滚动夏普比率"""
        risk_free_rate = self.config.get('risk_free_rate', 0.02) / 252
        excess_returns = returns - risk_free_rate
        rolling_sharpe = excess_returns.rolling(window).mean() / excess_returns.rolling(window).std() * np.sqrt(252)
        return rolling_sharpe
    
    def get_available_metrics(self) -> List[str]:
        """获取可用的性能指标"""
        return [
            'total_return', 'annualized_return', 'sharpe_ratio', 'sortino_ratio',
            'max_drawdown', 'volatility', 'win_rate', 'profit_factor',
            'calmar_ratio', 'omega_ratio', 'information_ratio'
        ]
    
    def compare_with_benchmark(self, equity_curve: pd.Series,
                              benchmark: pd.Series, **kwargs) -> Dict[str, Any]:
        """与基准对比
        
        Args:
            equity_curve: 策略净值曲线
            benchmark: 基准净值曲线
            **kwargs: 额外参数
            
        Returns:
            对比结果
        """
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
            risk_free_rate = self.config.get('risk_free_rate', 0.02) / 252
            alpha = np.mean(strategy_returns - risk_free_rate) - beta * np.mean(benchmark_returns - risk_free_rate)
            
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
            self.logger.error(f"Benchmark comparison failed: {e}")
            return {
                'outperformance': 0.0,
                'correlation': 0.0,
                'beta': 1.0,
                'alpha': 0.0,
                'error': str(e)
            }
    
    def register(self, registry) -> None:
        """注册插件到框架"""
        # 注册为性能评估组件
        registry.register_feature_extractor(self.name, self)
    
    def _cleanup(self) -> None:
        """清理资源"""
        self._metrics_cache.clear()