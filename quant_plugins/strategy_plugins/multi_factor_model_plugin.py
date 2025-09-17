"""
多因子模型插件
提供多因子计算和管理的插件实现

功能:
- 多因子计算和管理
- 因子数据验证和质量控制
- 因子组合和优化
- 因子绩效分析
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, field_validator
import pandas as pd
import numpy as np
from datetime import datetime
import warnings

from ascend.plugin_manager.base import BasePlugin
from ascend.core.exceptions import PluginError
from . import IFactorModel, IStrategyPlugin

# 插件配置模型
class MultiFactorModelPluginConfig(BaseModel):
    """多因子模型插件配置"""
    
    enabled_factors: List[str] = Field(
        ["momentum", "value", "growth", "quality", "volatility"],
        description="启用的因子列表"
    )
    factor_calculation_window: int = Field(252, description="因子计算窗口期")
    factor_normalization: str = Field("zscore", description="因子标准化方法: zscore, rank, none")
    enable_factor_rotation: bool = Field(False, description="是否启用因子轮动")
    min_data_points: int = Field(20, description="最小数据点数")
    
    @field_validator('enabled_factors')
    def validate_enabled_factors(cls, v):
        if not v:
            raise ValueError('Enabled factors cannot be empty')
        return v
    
    @field_validator('factor_calculation_window')
    def validate_calculation_window(cls, v):
        if v < 10:
            raise ValueError('Factor calculation window must be at least 10')
        return v
    
    @field_validator('factor_normalization')
    def validate_normalization_method(cls, v):
        valid_methods = ['zscore', 'rank', 'none']
        if v not in valid_methods:
            raise ValueError(f'Normalization method must be one of: {valid_methods}')
        return v


class MultiFactorModelPlugin(BasePlugin, IFactorModel, IStrategyPlugin):
    """多因子模型插件实现"""
    
    def __init__(self):
        super().__init__(
            name="multi_factor_model",
            version="1.0.0",
            description="多因子模型插件，提供因子计算、验证和组合功能",
            author="ASCEND Team",
            license="Apache 2.0"
        )
        self._factor_calculators = {}
        self._factor_data = {}
        self._current_factors = []
    
    def get_config_schema(self) -> Optional[type]:
        """获取配置模型"""
        return MultiFactorModelPluginConfig
    
    def _initialize(self) -> None:
        """初始化因子计算器"""
        # 初始化因子计算器字典
        self._factor_calculators = {
            'momentum': self._calculate_momentum_factor,
            'value': self._calculate_value_factor,
            'growth': self._calculate_growth_factor,
            'quality': self._calculate_quality_factor,
            'volatility': self._calculate_volatility_factor,
            'size': self._calculate_size_factor,
            'liquidity': self._calculate_liquidity_factor
        }
        
        # 设置当前启用的因子
        self._current_factors = self.config.get('enabled_factors', [
            "momentum", "value", "growth", "quality", "volatility"
        ])
    
    def execute(self, data: Any, **kwargs) -> Any:
        """执行多因子计算
        
        Args:
            data: 输入数据 (DataFrame 或字典)
            **kwargs: 额外参数
            
        Returns:
            因子计算结果
        """
        try:
            if isinstance(data, pd.DataFrame):
                # 单股票数据
                factors = self.calculate_factors(data, **kwargs)
                return {'factors': factors, 'validation': self.validate_factors(factors)}
            elif isinstance(data, dict):
                # 多股票数据
                results = {}
                for symbol, stock_data in data.items():
                    if isinstance(stock_data, pd.DataFrame):
                        factors = self.calculate_factors(stock_data, **kwargs)
                        results[symbol] = {
                            'factors': factors,
                            'validation': self.validate_factors(factors)
                        }
                return results
            else:
                raise ValueError("Unsupported data type")
                
        except Exception as e:
            raise PluginError(f"Multi-factor model execution failed: {e}")
    
    def calculate_factors(self, data: Any, **kwargs) -> Dict[str, Any]:
        """计算因子值
        
        Args:
            data: 输入数据
            **kwargs: 额外参数
            
        Returns:
            因子值字典 {因子名称: 因子值}
        """
        try:
            if not isinstance(data, pd.DataFrame):
                raise ValueError("Data must be a pandas DataFrame")
            
            # 验证数据完整性
            self._validate_factor_data(data)
            
            factors = {}
            enabled_factors = kwargs.get('enabled_factors', self._current_factors)
            
            for factor_name in enabled_factors:
                if factor_name in self._factor_calculators:
                    try:
                        factor_value = self._factor_calculators[factor_name](data)
                        factors[factor_name] = factor_value
                    except Exception as e:
                        # 因子计算失败，记录错误但继续其他因子
                        factors[factor_name] = None
                        self.logger.warning(f"Factor {factor_name} calculation failed: {e}")
            
            # 因子标准化
            normalized_factors = self._normalize_factors(factors)
            
            # 缓存因子数据
            self._factor_data = normalized_factors
            
            return normalized_factors
            
        except Exception as e:
            raise PluginError(f"Factor calculation failed: {e}")
    
    def _calculate_momentum_factor(self, data: pd.DataFrame) -> float:
        """计算动量因子"""
        if 'close' not in data.columns or len(data) < 20:
            return 0.0
        
        closes = data['close'].values
        short_return = (closes[-1] / closes[-5] - 1) if len(closes) >= 5 else 0
        medium_return = (closes[-1] / closes[-20] - 1) if len(closes) >= 20 else 0
        long_return = (closes[-1] / closes[-60] - 1) if len(closes) >= 60 else 0
        
        # 综合动量得分
        momentum_score = (short_return * 0.4 + medium_return * 0.4 + long_return * 0.2)
        return momentum_score
    
    def _calculate_value_factor(self, data: pd.DataFrame) -> float:
        """计算价值因子"""
        # 这里需要财务数据，简化实现
        # 实际实现应该使用PE、PB、PS等估值指标
        return 0.0
    
    def _calculate_growth_factor(self, data: pd.DataFrame) -> float:
        """计算成长因子"""
        # 需要财务数据计算营收增长率、利润增长率等
        return 0.0
    
    def _calculate_quality_factor(self, data: pd.DataFrame) -> float:
        """计算质量因子"""
        # 需要财务数据计算ROE、ROA等质量指标
        return 0.0
    
    def _calculate_volatility_factor(self, data: pd.DataFrame) -> float:
        """计算波动率因子"""
        if 'close' not in data.columns or len(data) < 20:
            return 0.0
        
        closes = data['close'].values
        returns = np.diff(np.log(closes))
        volatility = np.std(returns) * np.sqrt(252) if len(returns) > 1 else 0
        
        # 波动率因子：低波动率得分高
        volatility_score = 1.0 / (1.0 + volatility) if volatility > 0 else 1.0
        return volatility_score
    
    def _calculate_size_factor(self, data: pd.DataFrame) -> float:
        """计算规模因子"""
        # 需要市值数据
        return 0.0
    
    def _calculate_liquidity_factor(self, data: pd.DataFrame) -> float:
        """计算流动性因子"""
        if 'volume' not in data.columns or len(data) < 20:
            return 0.0
        
        volumes = data['volume'].values
        avg_volume = np.mean(volumes[-20:]) if len(volumes) >= 20 else np.mean(volumes)
        current_volume = volumes[-1] if len(volumes) > 0 else 0
        
        if avg_volume == 0:
            return 0.0
        
        liquidity_ratio = current_volume / avg_volume
        # 流动性因子：高流动性得分高
        liquidity_score = min(liquidity_ratio, 2.0) / 2.0  # 归一化到0-1
        return liquidity_score
    
    def _normalize_factors(self, factors: Dict[str, Any]) -> Dict[str, Any]:
        """标准化因子值"""
        normalization_method = self.config.get('factor_normalization', 'zscore')
        
        if normalization_method == 'none' or not factors:
            return factors
        
        valid_factors = {k: v for k, v in factors.items() if v is not None and np.isfinite(v)}
        
        if not valid_factors:
            return factors
        
        if normalization_method == 'zscore':
            # Z-score 标准化
            values = list(valid_factors.values())
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            if std_val == 0:
                return {k: 0.0 for k in valid_factors.keys()}
            
            normalized = {k: (v - mean_val) / std_val for k, v in valid_factors.items()}
            return {**factors, **normalized}
            
        elif normalization_method == 'rank':
            # 排名标准化 (0-1)
            values = list(valid_factors.values())
            ranks = pd.Series(values).rank(pct=True)
            normalized = {k: ranks[i] for i, (k, v) in enumerate(valid_factors.items())}
            return {**factors, **normalized}
        
        return factors
    
    def _validate_factor_data(self, data: pd.DataFrame) -> None:
        """验证因子数据完整性"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in data.columns:
                raise ValueError(f"Missing required column for factor calculation: {col}")
        
        min_points = self.config.get('min_data_points', 20)
        if len(data) < min_points:
            raise ValueError(f"Insufficient data points for factor calculation: {len(data)} < {min_points}")
    
    def get_available_factors(self) -> List[str]:
        """获取可用的因子列表"""
        return list(self._factor_calculators.keys())
    
    def validate_factors(self, factors: Dict[str, Any]) -> bool:
        """验证因子数据
        
        Args:
            factors: 因子数据
            
        Returns:
            是否验证通过
        """
        if not factors:
            return False
        
        # 检查因子值有效性
        valid_count = 0
        for factor_name, factor_value in factors.items():
            if factor_value is not None and np.isfinite(factor_value):
                valid_count += 1
        
        # 至少50%的因子有效才算通过
        validation_passed = (valid_count / len(factors)) >= 0.5
        return validation_passed
    
    def get_strategy_type(self) -> str:
        """获取策略类型"""
        return "multi_factor_model"
    
    def get_required_data_types(self) -> List[str]:
        """获取所需的数据类型"""
        return ['daily_kline', 'financial_data']
    
    def register(self, registry) -> None:
        """注册插件到框架"""
        # 注册为因子模型组件
        registry.register_feature_extractor(self.name, self)
    
    def _cleanup(self) -> None:
        """清理资源"""
        self._factor_calculators.clear()
        self._factor_data.clear()
        self._current_factors.clear()