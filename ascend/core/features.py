"""
基础特征提取器实现模块

提供了一个实现IFeatureExtractor协议的基础特征提取器类，作为所有具体特征提取器实现的基类。
包含了基础的特征提取和维度管理功能。
"""

from typing import Dict, Any, List
import logging
import numpy as np


from .protocols import IFeatureExtractor, Feature

logger = logging.getLogger(__name__)

class BaseFeatureExtractor(IFeatureExtractor):
    """基础特征提取器实现
    
    实现了IFeatureExtractor协议的抽象基类，提供了特征提取的基础功能框架。
    具体的特征提取器类需要继承该类并实现抽象方法。
    
    Attributes:
        name (str): 特征提取器名称
        config (Dict[str, Any]): 配置参数
        feature_dim (int): 特征维度
    """
    
    def __init__(self, name: str, config: Dict[str, Any]) -> None:
        """初始化特征提取器
        
        Args:
            name: 特征提取器名称
            config: 配置参数字典
        """
        self.name = name
        self.config = config
        self.feature_dim = self._compute_feature_dim()
        self._init_extractors()
        logger.info(f"Initialized feature extractor {self.name}")
    
    def _init_extractors(self) -> None:
        """初始化提取器组件
        
        可以在子类中重写以添加具体的特征提取器组件
        """
        pass
    
    
    def _compute_feature_dim(self) -> int:
        """计算特征维度
        
        Returns:
            特征维度
        """
        raise NotImplementedError
    
    
    def extract_features(self, raw_data: Any) -> Feature:
        """提取特征

        Args:
            raw_data: 原始数据

        Returns:
            提取的特征
        """
        raise NotImplementedError
    
    def get_feature_dim(self) -> int:
        """获取特征维度
        
        Returns:
            特征维度
        """
        return self.feature_dim
    
    def validate_feature(self, feature: Feature) -> bool:
        """验证特征是否有效
        
        Args:
            feature: 待验证的特征
            
        Returns:
            特征是否有效
        """
        try:
            # 检查特征维度
            if isinstance(feature, dict):
                feature_array = np.array(list(feature.values()))
            else:
                feature_array = np.array(feature)
            return feature_array.size == self.feature_dim
        except:
            return False
    
    def combine_features(self, features: List[Feature]) -> Feature:
        """组合多个特征
        
        Args:
            features: 特征列表
            
        Returns:
            组合后的特征
        """
        # 默认实现是简单的字典合并或数组拼接
        if all(isinstance(f, dict) for f in features):
            combined = {}
            for f in features:
                combined.update(f)
            return combined
        else:
            return np.concatenate([np.array(f).flatten() for f in features])
    
    def normalize_feature(self, feature: Feature) -> Feature:
        """归一化特征
        
        Args:
            feature: 原始特征
            
        Returns:
            归一化后的特征
        """
        # 默认实现是最小-最大归一化
        if isinstance(feature, dict):
            values = np.array(list(feature.values()))
            normalized_values = (values - values.min()) / (values.max() - values.min() + 1e-8)
            return dict(zip(feature.keys(), normalized_values))
        else:
            feature_array = np.array(feature)
            return (feature_array - feature_array.min()) / (feature_array.max() - feature_array.min() + 1e-8)
    
    def get_config(self) -> Dict[str, Any]:
        """获取特征提取器配置
        
        Returns:
            配置字典的深拷贝
        """
        return self.config.copy()
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """更新配置参数
        
        Args:
            new_config: 新的配置参数
        """
        self.config.update(new_config)
        # 更新特征维度
        self.feature_dim = self._compute_feature_dim()
        logger.info(f"Updated feature extractor {self.name} config")
    
    def extract_state(self, raw_data: Any) -> State:
        """提取状态表示

        Args:
            raw_data: 原始数据

        Returns:
            状态表示
        """
        raise NotImplementedError