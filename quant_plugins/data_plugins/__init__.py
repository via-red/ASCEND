"""
数据插件层
提供数据获取、预处理和存储功能的插件集合

包含以下插件:
- 数据源插件: TushareDataPlugin, 聚宽数据源, Wind数据源等
- 数据预处理插件: DataPreprocessingPlugin
- 数据存储插件: WarehouseStoragePlugin, MySQL存储, MongoDB存储等

协议接口:
- IDataSourcePlugin: 数据源插件协议
- IDataProcessorPlugin: 数据处理器插件协议  
- IDataStoragePlugin: 数据存储插件协议
"""

from typing import Protocol, Any, Dict, List, Optional
from abc import abstractmethod
from pydantic import BaseModel

# 数据插件协议接口
class IDataSourcePlugin(Protocol):
    """数据源插件协议 - 定义数据获取接口"""
    
    @abstractmethod
    def fetch_data(self, symbol: str, start_date: str, end_date: str, **kwargs) -> Any:
        """获取股票数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            **kwargs: 额外参数
            
        Returns:
            股票数据
        """
        ...
    
    @abstractmethod
    def get_available_symbols(self) -> List[str]:
        """获取可用的股票代码列表
        
        Returns:
            股票代码列表
        """
        ...
    
    @abstractmethod
    def get_data_types(self) -> List[str]:
        """获取支持的数据类型
        
        Returns:
            数据类型列表
        """
        ...


class IDataProcessorPlugin(Protocol):
    """数据处理器插件协议 - 定义数据预处理接口"""
    
    @abstractmethod
    def clean_data(self, raw_data: Any) -> Any:
        """数据清洗
        
        Args:
            raw_data: 原始数据
            
        Returns:
            清洗后的数据
        """
        ...
    
    @abstractmethod
    def handle_missing_values(self, data: Any, strategy: str = 'fill') -> Any:
        """处理缺失值
        
        Args:
            data: 输入数据
            strategy: 处理策略 ('fill', 'drop', 'interpolate')
            
        Returns:
            处理后的数据
        """
        ...
    
    @abstractmethod
    def normalize_data(self, data: Any) -> Any:
        """数据标准化
        
        Args:
            data: 输入数据
            
        Returns:
            标准化后的数据
        """
        ...
    
    @abstractmethod
    def extract_features(self, data: Any) -> Any:
        """特征工程
        
        Args:
            data: 输入数据
            
        Returns:
            提取的特征
        """
        ...


class IDataStoragePlugin(Protocol):
    """数据存储插件协议 - 定义数据存储接口"""
    
    @abstractmethod
    def save_data(self, data: Any, key: str, **kwargs) -> bool:
        """保存数据
        
        Args:
            data: 要保存的数据
            key: 数据标识键
            **kwargs: 额外参数
            
        Returns:
            是否保存成功
        """
        ...
    
    @abstractmethod
    def load_data(self, key: str, **kwargs) -> Any:
        """加载数据
        
        Args:
            key: 数据标识键
            **kwargs: 额外参数
            
        Returns:
            加载的数据
        """
        ...
    
    @abstractmethod
    def delete_data(self, key: str, **kwargs) -> bool:
        """删除数据
        
        Args:
            key: 数据标识键
            **kwargs: 额外参数
            
        Returns:
            是否删除成功
        """
        ...
    
    @abstractmethod
    def list_keys(self, pattern: str = "*") -> List[str]:
        """列出数据键
        
        Args:
            pattern: 键模式匹配
            
        Returns:
            键列表
        """
        ...


# 导出插件类 (将在具体实现文件中定义)
from .tushare_data_plugin import TushareDataPlugin
from .ashare_data_plugin import AshareDataPlugin
from .data_preprocessing_plugin import DataPreprocessingPlugin
from .warehouse_storage_plugin import WarehouseStoragePlugin

__all__ = [
    # 协议接口
    'IDataSourcePlugin',
    'IDataProcessorPlugin',
    'IDataStoragePlugin',
    
    # 具体插件
    'TushareDataPlugin',
    'AshareDataPlugin',
    'DataPreprocessingPlugin',
    'WarehouseStoragePlugin'
]