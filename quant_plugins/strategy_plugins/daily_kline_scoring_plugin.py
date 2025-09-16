"""
日K线评分策略插件
基于多因子模型的日K线评分策略实现

功能:
- 多因子评分模型 (动量、成交量、波动率、趋势、RSI)
- 动态权重配置
- 信号生成和排名筛选
- 支持沪深创业板股票评分
"""

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, field_validator
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import talib

from ascend.plugins.base import BasePlugin
from ascend.core.exceptions import PluginError
from . import IScoringStrategy, IStrategyPlugin

# 插件配置模型
class DailyKlineScoringPluginConfig(BaseModel):
    """日K线评分策略配置"""
    
    factor_weights: Dict[str, float] = Field(
        {
            "momentum": 0.35,
            "volume": 0.15, 
            "volatility": 0.15,
            "trend": 0.25,
            "rsi_strength": 0.10
        },
        description="因子权重配置"
    )
    scoring_threshold: float = Field(0.65, description="评分阈值")
    min_data_points: int = Field(20, description="最小数据点数")
    enable_dynamic_weights: bool = Field(True, description="是否启用动态权重")
    signal_generation: bool = Field(True, description="是否生成交易信号")
    
    @field_validator('factor_weights')
    def validate_factor_weights(cls, v):
        total_weight = sum(v.values())
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError('Factor weights must sum to 1.0')
        return v
    
    @field_validator('scoring_threshold')
    def validate_scoring_threshold(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Scoring threshold must be between 0 and 1')
        return v


class DailyKlineScoringPlugin(BasePlugin, IScoringStrategy, IStrategyPlugin):
    """日K线评分策略插件实现"""
    
    def __init__(self):
        super().__init__(
            name="daily_kline_scoring",
            version="1.0.0",
            description="日K线多因子评分策略插件，支持沪深创业板股票评分",
            author="ASCEND Team",
            license="Apache 2.0"
        )
        self._factor_calculators = {}
        self._current_weights = {}
    
    def get_config_schema(self) -> Optional[type]:
        """获取配置模型"""
        return DailyKlineScoringPluginConfig
    
    def _initialize(self) -> None:
        """初始化因子计算器"""
        # 初始化因子计算器
        self._factor_calculators = {
            'momentum': self._calculate_momentum_factor,
            'volume': self._calculate_volume_factor,
            'volatility': self._calculate_volatility_factor,
            'trend': self._calculate_trend_factor,
            'rsi_strength': self._calculate_rsi_factor
        }
        
        # 设置初始权重
        self._current_weights = self.config.get('factor_weights', {
            "momentum": 0.35,
            "volume": 0.15,
            "volatility": 0.15,
            "trend": 0.25,
            "rsi_strength": 0.10
        })
    
    def execute(self, data: Any, **kwargs) -> Any:
        """执行策略
        
        Args:
            data: 输入数据 (DataFrame 或字典)
            **kwargs: 额外参数
            
        Returns:
            策略执行结果
        """
        try:
            if isinstance(data, pd.DataFrame):
                # 单股票数据
                scores = self.calculate_score(data, **kwargs)
                signals = self.generate_signals(scores, **kwargs)
                return {'scores': scores, 'signals': signals}
            elif isinstance(data, dict):
                # 多股票数据
                results = {}
                for symbol, stock_data in data.items():
                    if isinstance(stock_data, pd.DataFrame):
                        scores = self.calculate_score(stock_data, **kwargs)
                        signals = self.generate_signals(scores, **kwargs)
                        results[symbol] = {'scores': scores, 'signals': signals}
                return results
            else:
                raise ValueError("Unsupported data type")
                
        except Exception as e:
            raise PluginError(f"Strategy execution failed: {e}")
    
    def calculate_score(self, data: Any, **kwargs) -> Dict[str, float]:
        """计算股票评分
        
        Args:
            data: 输入数据 (DataFrame)
            **kwargs: 额外参数
            
        Returns:
            股票评分字典
        """
        try:
            if not isinstance(data, pd.DataFrame):
                raise ValueError("Data must be a pandas DataFrame")
            
            # 检查数据完整性
            self._validate_data(data)
            
            # 计算所有因子
            factors = self._calculate_all_factors(data)
            
            # 计算综合评分
            total_score = 0.0
            factor_scores = {}
            
            for factor_name, factor_value in factors.items():
                if factor_name in self._current_weights:
                    # 标准化因子值到0-1范围
                    normalized_value = self._normalize_factor(factor_value, factor_name)
                    weighted_score = normalized_value * self._current_weights[factor_name]
                    factor_scores[factor_name] = weighted_score
                    total_score += weighted_score
            
            # 返回评分结果
            return {
                'total_score': total_score,
                'factor_scores': factor_scores,
                'factors': factors
            }
            
        except Exception as e:
            raise PluginError(f"Score calculation failed: {e}")
    
    def _calculate_all_factors(self, data: pd.DataFrame) -> Dict[str, float]:
        """计算所有因子值"""
        factors = {}
        
        for factor_name, calculator in self._factor_calculators.items():
            try:
                factor_value = calculator(data)
                factors[factor_name] = factor_value
            except Exception as e:
                # 因子计算失败，使用默认值
                factors[factor_name] = 0.0
        
        return factors
    
    def _calculate_momentum_factor(self, data: pd.DataFrame) -> float:
        """计算动量因子"""
        # 使用价格变化率作为动量指标
        if 'close' not in data.columns:
            return 0.0
        
        closes = data['close'].values
        if len(closes) < 2:
            return 0.0
        
        # 计算短期和长期动量
        short_period = min(5, len(closes))
        long_period = min(20, len(closes))
        
        short_return = (closes[-1] / closes[-short_period] - 1) * 100
        long_return = (closes[-1] / closes[-long_period] - 1) * 100
        
        # 综合动量得分
        momentum_score = (short_return * 0.6 + long_return * 0.4) / 10  # 缩放因子
        return max(min(momentum_score, 1.0), -1.0)  # 限制在-1到1之间
    
    def _calculate_volume_factor(self, data: pd.DataFrame) -> float:
        """计算成交量因子"""
        if 'volume' not in data.columns:
            return 0.0
        
        volumes = data['volume'].values
        if len(volumes) < 20:
            return 0.0
        
        # 计算成交量相对强度
        current_volume = volumes[-1]
        avg_volume = np.mean(volumes[-20:])
        
        if avg_volume == 0:
            return 0.0
        
        volume_ratio = current_volume / avg_volume
        # 成交量因子: 1.5倍以上为1.0，0.5倍以下为0.0
        volume_score = max(min((volume_ratio - 0.5) * 2, 1.0), 0.0)
        return volume_score
    
    def _calculate_volatility_factor(self, data: pd.DataFrame) -> float:
        """计算波动率因子"""
        if 'close' not in data.columns:
            return 0.0
        
        closes = data['close'].values
        if len(closes) < 20:
            return 0.0
        
        # 计算历史波动率 (年化)
        returns = np.diff(np.log(closes))
        if len(returns) == 0:
            return 0.0
        
        volatility = np.std(returns) * np.sqrt(252)  # 年化波动率
        
        # 波动率因子: 低波动率得分高，高波动率得分低
        # 假设合理波动率在20%-40%之间
        if volatility < 0.2:
            volatility_score = 1.0
        elif volatility > 0.4:
            volatility_score = 0.0
        else:
            volatility_score = 1.0 - (volatility - 0.2) / 0.2
        
        return max(min(volatility_score, 1.0), 0.0)
    
    def _calculate_trend_factor(self, data: pd.DataFrame) -> float:
        """计算趋势因子"""
        if 'close' not in data.columns:
            return 0.0
        
        closes = data['close'].values
        if len(closes) < 20:
            return 0.0
        
        # 使用移动平均线判断趋势
        short_ma = np.mean(closes[-5:])
        long_ma = np.mean(closes[-20:])
        
        if long_ma == 0:
            return 0.0
        
        # 趋势强度
        trend_strength = (short_ma - long_ma) / long_ma
        
        # 趋势因子: 强势上涨为1.0，强势下跌为0.0
        trend_score = (trend_strength + 0.1) / 0.2  # 映射到0-1范围
        return max(min(trend_score, 1.0), 0.0)
    
    def _calculate_rsi_factor(self, data: pd.DataFrame) -> float:
        """计算RSI相对强弱因子"""
        if 'close' not in data.columns:
            return 0.0
        
        closes = data['close'].values
        if len(closes) < 14:
            return 0.0
        
        # 计算RSI
        try:
            rsi = talib.RSI(closes, timeperiod=14)[-1]
            if np.isnan(rsi):
                return 0.0
            
            # RSI因子: 50-70为最佳区间
            if 50 <= rsi <= 70:
                rsi_score = 1.0
            elif rsi < 30 or rsi > 80:
                rsi_score = 0.0
            else:
                # 线性插值
                if rsi < 50:
                    rsi_score = (rsi - 30) / 20
                else:
                    rsi_score = (80 - rsi) / 10
            
            return max(min(rsi_score, 1.0), 0.0)
            
        except:
            return 0.0
    
    def _normalize_factor(self, value: float, factor_name: str) -> float:
        """标准化因子值到0-1范围"""
        # 不同因子可能有不同的标准化逻辑
        # 这里使用简单的sigmoid函数进行标准化
        return 1.0 / (1.0 + np.exp(-value))
    
    def _validate_data(self, data: pd.DataFrame) -> None:
        """验证数据完整性"""
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in data.columns:
                raise ValueError(f"Missing required column: {col}")
        
        min_points = self.config.get('min_data_points', 20)
        if len(data) < min_points:
            raise ValueError(f"Insufficient data points: {len(data)} < {min_points}")
    
    def generate_signals(self, scores: Dict[str, float], **kwargs) -> Dict[str, str]:
        """生成交易信号
        
        Args:
            scores: 股票评分字典
            **kwargs: 额外参数
            
        Returns:
            交易信号字典
        """
        threshold = kwargs.get('threshold', self.config.get('scoring_threshold', 0.65))
        
        total_score = scores.get('total_score', 0.0)
        
        if total_score >= threshold:
            return {
                'signal': 'BUY',
                'confidence': total_score,
                'reason': f"Score {total_score:.3f} >= threshold {threshold}"
            }
        elif total_score >= threshold * 0.8:
            return {
                'signal': 'HOLD',
                'confidence': total_score,
                'reason': f"Score {total_score:.3f} close to threshold {threshold}"
            }
        else:
            return {
                'signal': 'SELL',
                'confidence': total_score,
                'reason': f"Score {total_score:.3f} below threshold {threshold}"
            }
    
    def get_factor_weights(self) -> Dict[str, float]:
        """获取因子权重配置"""
        return self._current_weights.copy()
    
    def get_strategy_type(self) -> str:
        """获取策略类型"""
        return "daily_kline_scoring"
    
    def get_required_data_types(self) -> List[str]:
        """获取所需的数据类型"""
        return ['daily_kline']
    
    def register(self, registry) -> None:
        """注册插件到框架"""
        # 注册为策略组件
        registry.register_policy(self.name, self)
    
    def _cleanup(self) -> None:
        """清理资源"""
        self._factor_calculators.clear()
        self._current_weights.clear()