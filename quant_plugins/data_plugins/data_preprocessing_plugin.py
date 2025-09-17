"""
数据预处理插件
提供数据清洗、缺失值处理、标准化和特征工程功能

功能:
- 数据清洗和验证
- 缺失值处理 (填充、删除、插值)
- 数据标准化和归一化
- 技术指标计算和特征工程
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.impute import SimpleImputer

from ascend.plugin_manager.base import BasePlugin
from ascend.core.exceptions import PluginError
from . import IDataProcessorPlugin

# 插件配置模型
class DataPreprocessingPluginConfig(BaseModel):
    """数据预处理插件配置"""
    
    missing_value_strategy: str = Field('fill', description="缺失值处理策略: fill, drop, interpolate")
    fill_value: float = Field(0.0, description="填充值（当策略为fill时使用）")
    scaling_method: str = Field('standard', description="标准化方法: standard, minmax, none")
    outlier_handling: str = Field('clip', description="异常值处理: clip, remove, ignore")
    outlier_threshold: float = Field(3.0, description="异常值阈值（标准差倍数）")
    feature_engineering: bool = Field(True, description="是否启用特征工程")
    
    @field_validator('missing_value_strategy')
    def validate_missing_strategy(cls, v):
        valid_strategies = ['fill', 'drop', 'interpolate']
        if v not in valid_strategies:
            raise ValueError(f'Missing value strategy must be one of: {valid_strategies}')
        return v
    
    @field_validator('scaling_method')
    def validate_scaling_method(cls, v):
        valid_methods = ['standard', 'minmax', 'none']
        if v not in valid_methods:
            raise ValueError(f'Scaling method must be one of: {valid_methods}')
        return v
    
    @field_validator('outlier_handling')
    def validate_outlier_handling(cls, v):
        valid_methods = ['clip', 'remove', 'ignore']
        if v not in valid_methods:
            raise ValueError(f'Outlier handling must be one of: {valid_methods}')
        return v


class DataPreprocessingPlugin(BasePlugin, IDataProcessorPlugin):
    """数据预处理插件实现"""
    
    def __init__(self):
        super().__init__(
            name="data_preprocessing",
            version="1.0.0",
            description="数据预处理插件，提供数据清洗、缺失值处理和特征工程功能",
            author="ASCEND Team",
            license="Apache 2.0"
        )
        self._scaler = None
        self._imputer = None
    
    def get_config_schema(self) -> Optional[type]:
        """获取配置模型"""
        return DataPreprocessingPluginConfig
    
    def _initialize(self) -> None:
        """初始化预处理工具"""
        # 根据配置初始化标准化器和填充器
        scaling_method = self.config.get('scaling_method', 'standard')
        missing_strategy = self.config.get('missing_value_strategy', 'fill')
        
        if scaling_method == 'standard':
            self._scaler = StandardScaler()
        elif scaling_method == 'minmax':
            self._scaler = MinMaxScaler()
        
        if missing_strategy == 'fill':
            fill_value = self.config.get('fill_value', 0.0)
            self._imputer = SimpleImputer(strategy='constant', fill_value=fill_value)
    
    def clean_data(self, raw_data: Any) -> Any:
        """数据清洗
        
        Args:
            raw_data: 原始数据 (DataFrame 或 numpy array)
            
        Returns:
            清洗后的数据
        """
        try:
            if isinstance(raw_data, pd.DataFrame):
                return self._clean_dataframe(raw_data)
            elif isinstance(raw_data, np.ndarray):
                return self._clean_array(raw_data)
            else:
                raise ValueError("Unsupported data type. Expected DataFrame or numpy array.")
                
        except Exception as e:
            raise PluginError(f"Data cleaning failed: {e}")
    
    def _clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """清洗 DataFrame 数据"""
        # 复制数据避免修改原始数据
        cleaned_df = df.copy()
        
        # 处理无限值
        cleaned_df = cleaned_df.replace([np.inf, -np.inf], np.nan)
        
        # 处理重复数据
        cleaned_df = cleaned_df.drop_duplicates()
        
        # 处理异常值
        outlier_method = self.config.get('outlier_handling', 'clip')
        if outlier_method != 'ignore':
            cleaned_df = self._handle_outliers(cleaned_df, outlier_method)
        
        return cleaned_df
    
    def _clean_array(self, array: np.ndarray) -> np.ndarray:
        """清洗 numpy array 数据"""
        # 处理无限值
        array = np.where(np.isfinite(array), array, np.nan)
        
        # 处理异常值
        outlier_method = self.config.get('outlier_handling', 'clip')
        if outlier_method != 'ignore':
            array = self._handle_array_outliers(array, outlier_method)
        
        return array
    
    def _handle_outliers(self, df: pd.DataFrame, method: str) -> pd.DataFrame:
        """处理 DataFrame 异常值"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if method == 'clip':
                df[col] = self._clip_outliers(df[col])
            elif method == 'remove':
                df = df[~self._is_outlier(df[col])]
        
        return df
    
    def _handle_array_outliers(self, array: np.ndarray, method: str) -> np.ndarray:
        """处理数组异常值"""
        if method == 'clip':
            return self._clip_outliers(array)
        elif method == 'remove':
            # 对于数组，移除操作较复杂，这里使用 clipping
            return self._clip_outliers(array)
        return array
    
    def _clip_outliers(self, data: Any, threshold: float = None) -> Any:
        """Clipping 异常值"""
        if threshold is None:
            threshold = self.config.get('outlier_threshold', 3.0)
        
        if isinstance(data, pd.Series):
            mean = data.mean()
            std = data.std()
            lower_bound = mean - threshold * std
            upper_bound = mean + threshold * std
            return data.clip(lower_bound, upper_bound)
        else:
            mean = np.nanmean(data)
            std = np.nanstd(data)
            lower_bound = mean - threshold * std
            upper_bound = mean + threshold * std
            return np.clip(data, lower_bound, upper_bound)
    
    def _is_outlier(self, data: pd.Series, threshold: float = None) -> pd.Series:
        """检测异常值"""
        if threshold is None:
            threshold = self.config.get('outlier_threshold', 3.0)
        
        mean = data.mean()
        std = data.std()
        return (data < mean - threshold * std) | (data > mean + threshold * std)
    
    def handle_missing_values(self, data: Any, strategy: str = 'fill') -> Any:
        """处理缺失值
        
        Args:
            data: 输入数据
            strategy: 处理策略 ('fill', 'drop', 'interpolate')
            
        Returns:
            处理后的数据
        """
        try:
            if isinstance(data, pd.DataFrame):
                return self._handle_df_missing_values(data, strategy)
            elif isinstance(data, np.ndarray):
                return self._handle_array_missing_values(data, strategy)
            else:
                raise ValueError("Unsupported data type")
                
        except Exception as e:
            raise PluginError(f"Missing value handling failed: {e}")
    
    def _handle_df_missing_values(self, df: pd.DataFrame, strategy: str) -> pd.DataFrame:
        """处理 DataFrame 缺失值"""
        if strategy == 'drop':
            return df.dropna()
        elif strategy == 'fill':
            fill_value = self.config.get('fill_value', 0.0)
            return df.fillna(fill_value)
        elif strategy == 'interpolate':
            return df.interpolate()
        else:
            raise ValueError(f"Unknown missing value strategy: {strategy}")
    
    def _handle_array_missing_values(self, array: np.ndarray, strategy: str) -> np.ndarray:
        """处理数组缺失值"""
        if strategy == 'drop':
            # 对于数组，drop 操作较复杂，这里使用填充
            return np.nan_to_num(array, nan=self.config.get('fill_value', 0.0))
        elif strategy == 'fill':
            fill_value = self.config.get('fill_value', 0.0)
            return np.nan_to_num(array, nan=fill_value)
        elif strategy == 'interpolate':
            # 简单的线性插值
            mask = np.isnan(array)
            array[mask] = np.interp(
                np.flatnonzero(mask), 
                np.flatnonzero(~mask), 
                array[~mask]
            )
            return array
        else:
            raise ValueError(f"Unknown missing value strategy: {strategy}")
    
    def normalize_data(self, data: Any) -> Any:
        """数据标准化
        
        Args:
            data: 输入数据
            
        Returns:
            标准化后的数据
        """
        scaling_method = self.config.get('scaling_method', 'standard')
        
        if scaling_method == 'none' or self._scaler is None:
            return data
        
        try:
            if isinstance(data, pd.DataFrame):
                numeric_cols = data.select_dtypes(include=[np.number]).columns
                data[numeric_cols] = self._scaler.fit_transform(data[numeric_cols])
                return data
            else:
                return self._scaler.fit_transform(data.reshape(-1, 1)).flatten()
                
        except Exception as e:
            raise PluginError(f"Data normalization failed: {e}")
    
    def extract_features(self, data: Any) -> Any:
        """特征工程
        
        Args:
            data: 输入数据
            
        Returns:
            提取的特征
        """
        if not self.config.get('feature_engineering', True):
            return data
        
        try:
            if isinstance(data, pd.DataFrame):
                return self._extract_dataframe_features(data)
            else:
                # 对于数组，特征工程较复杂，返回原始数据
                return data
                
        except Exception as e:
            raise PluginError(f"Feature extraction failed: {e}")
    
    def _extract_dataframe_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """从 DataFrame 提取特征"""
        # 这里实现具体的特征工程逻辑
        # 例如：计算技术指标、统计特征等
        
        result_df = df.copy()
        numeric_cols = result_df.select_dtypes(include=[np.number]).columns
        
        # 添加简单的统计特征作为示例
        for col in numeric_cols:
            # 移动平均
            result_df[f'{col}_ma5'] = result_df[col].rolling(window=5).mean()
            result_df[f'{col}_ma20'] = result_df[col].rolling(window=20).mean()
            
            # 波动率
            result_df[f'{col}_volatility'] = result_df[col].rolling(window=20).std()
            
            # 收益率
            result_df[f'{col}_return'] = result_df[col].pct_change()
        
        # 处理新产生的缺失值
        result_df = self.handle_missing_values(result_df, 'fill')
        
        return result_df
    
    def register(self, registry) -> None:
        """注册插件到框架"""
        # 注册为特征处理器组件
        registry.register_feature_extractor(self.name, self)
    
    def _cleanup(self) -> None:
        """清理资源"""
        self._scaler = None
        self._imputer = None