"""
高级性能评估插件
提供完整的性能指标计算、可视化和报告生成功能
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import pandas as pd

from ascend.plugin_manager.base import BasePlugin
from ascend.core.exceptions import PluginError
from .core_performance_evaluator import CorePerformanceEvaluator


class AdvancedPerformanceEvaluatorConfig(BaseModel):
    """高级性能评估器配置"""
    
    risk_free_rate: float = Field(0.02, description="无风险利率")
    enable_advanced_metrics: bool = Field(True, description="是否启用高级指标计算")
    enable_visualization: bool = Field(True, description="是否启用可视化功能")
    max_lookback_period: int = Field(252, description="最大回看周期")
    benchmark_symbol: str = Field("000300.SH", description="基准指数代码")
    
    @field_validator('risk_free_rate')
    def validate_risk_free_rate(cls, v):
        if v < 0:
            raise ValueError('Risk free rate cannot be negative')
        return v


class AdvancedPerformanceEvaluatorPlugin(BasePlugin):
    """高级性能评估插件 - 提供完整的性能分析和可视化功能"""
    
    def __init__(self):
        super().__init__(
            name="advanced_performance_tools",
            version="1.0.0",
            description="高级性能分析工具插件，提供详细的性能指标计算和可视化",
            author="ASCEND Team",
            license="Apache 2.0"
        )
        self._metrics_cache = {}
        self._logger = None
        self._evaluator = None
    
    def get_config_schema(self) -> Optional[type]:
        """获取配置模型"""
        return AdvancedPerformanceEvaluatorConfig
    
    def _initialize(self) -> None:
        """初始化性能工具插件"""
        self._setup_logging()
        self._metrics_cache = {}
        risk_free_rate = self.config.get('risk_free_rate', 0.02) if self.config else 0.02
        self._evaluator = CorePerformanceEvaluator(risk_free_rate=risk_free_rate)
        self._logger.info("高级性能评估器插件初始化完成")
    
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
            
            # 使用核心评估器计算完整指标
            metrics = self._evaluator.calculate_metrics(
                equity_curve, trades, include_advanced=True
            )
            
            # 缓存计算结果
            self._metrics_cache = metrics
            
            return metrics
            
        except Exception as e:
            raise PluginError(f"Metrics calculation failed: {e}")
    
    def get_available_metrics(self) -> List[str]:
        """获取可用的性能指标"""
        return [
            'total_return', 'annualized_return', 'cagr', 'avg_daily_return',
            'median_daily_return', 'positive_day_ratio', 'negative_day_ratio',
            'best_day', 'worst_day', 'volatility', 'downside_volatility',
            'max_drawdown', 'avg_drawdown', 'drawdown_duration',
            'value_at_risk_95', 'conditional_var_95', 'ulcer_index',
            'sharpe_ratio', 'sortino_ratio', 'calmar_ratio', 'omega_ratio',
            'treynor_ratio', 'information_ratio', 'win_rate', 'profit_factor',
            'avg_profit_per_trade', 'profit_ratio', 'expectancy', 'k_ratio'
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
        return self._evaluator.compare_with_benchmark(equity_curve, benchmark)
    
    def generate_performance_report(self, metrics: Dict[str, Any], 
                                  output_path: Optional[str] = None) -> str:
        """生成性能报告
        
        Args:
            metrics: 性能指标字典
            output_path: 输出文件路径
            
        Returns:
            报告文本
        """
        return self._evaluator.generate_performance_report(metrics, output_path)
    
    def plot_performance_charts(self, equity_curve: pd.Series, 
                              metrics: Dict[str, Any], 
                              output_path: Optional[str] = None):
        """绘制性能图表
        
        Args:
            equity_curve: 净值曲线
            metrics: 性能指标
            output_path: 输出文件路径
        """
        self._evaluator.plot_performance_charts(equity_curve, metrics, output_path)
    
    def register(self, registry) -> None:
        """注册插件到框架"""
        # 注册为性能评估组件
        registry.register_feature_extractor(self.name, self)
    
    def _setup_logging(self) -> None:
        """设置日志系统"""
        import logging
        
        self._logger = logging.getLogger(f"ascend.performance.{self.name}")
        self._logger.setLevel(logging.INFO)
        
        # 如果没有处理器，添加一个
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
    
    def _cleanup(self) -> None:
        """清理资源"""
        self._metrics_cache.clear()