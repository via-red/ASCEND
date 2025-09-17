"""
基础性能评估插件
提供基本的性能指标计算功能，基于核心评估器实现
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import pandas as pd

from ascend.plugin_manager.base import BasePlugin
from ascend.core.exceptions import PluginError
from .core_performance_evaluator import CorePerformanceEvaluator


class BasicPerformanceEvaluatorConfig(BaseModel):
    """基础性能评估器配置"""
    
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


class BasicPerformanceEvaluatorPlugin(BasePlugin):
    """基础性能评估器插件实现"""
    
    def __init__(self):
        super().__init__(
            name="performance_evaluator",
            version="1.0.0",
            description="基础性能评估器插件，提供核心的性能指标计算",
            author="ASCEND Team",
            license="Apache 2.0"
        )
        self._metrics_cache = {}
        self._logger = None
        self._evaluator = None
    
    def get_config_schema(self) -> Optional[type]:
        """获取配置模型"""
        return BasicPerformanceEvaluatorConfig
    
    def _initialize(self) -> None:
        """初始化性能评估器"""
        self._setup_logging()
        self._metrics_cache = {}
        risk_free_rate = self.config.get('risk_free_rate', 0.02) if self.config else 0.02
        self._evaluator = CorePerformanceEvaluator(risk_free_rate=risk_free_rate)
        self._logger.info("基础性能评估器插件初始化完成")
    
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
            
            # 使用核心评估器计算指标
            metrics = self._evaluator.calculate_metrics(
                equity_curve, trades, include_advanced=False
            )
            
            # 缓存计算结果
            self._metrics_cache = metrics
            
            return metrics
            
        except Exception as e:
            raise PluginError(f"Metrics calculation failed: {e}")
    
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
        return self._evaluator.compare_with_benchmark(equity_curve, benchmark)
    
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