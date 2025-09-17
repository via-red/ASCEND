"""
Ashare 数据源插件
基于 Ashare API 的股票数据获取插件

功能:
- 获取沪深创业板股票日K线数据
- 支持多种数据类型的获取
- 自动数据更新和维护
- 支持批量数据获取

Ashare 特点:
- 免费开源的中国股票数据接口
- 支持实时和历史数据
- 无需API token
- 支持多种数据频率
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ascend.plugin_manager.base import BasePlugin
from ascend.core.exceptions import PluginError
from . import IDataSourcePlugin

# 插件配置模型
class AshareDataPluginConfig(BaseModel):
    """Ashare 数据插件配置"""
    
    timeout: int = Field(30, description="API请求超时时间(秒)")
    max_retries: int = Field(3, description="最大重试次数")
    cache_enabled: bool = Field(True, description="是否启用缓存")
    cache_duration: int = Field(3600, description="缓存持续时间(秒)")
    use_proxy: bool = Field(False, description="是否使用代理")


class AshareDataPlugin(BasePlugin, IDataSourcePlugin):
    """Ashare 数据源插件实现"""
    
    def __init__(self):
        super().__init__(
            name="ashare_data",
            version="1.0.0",
            description="Ashare API数据源插件，支持沪深创业板股票数据获取",
            author="ASCEND Team",
            license="Apache 2.0"
        )
        self._ashare_module = None
        self._cache = {}
        self._last_fetch_time = {}
    
    def get_config_schema(self) -> Optional[type]:
        """获取配置模型"""
        return AshareDataPluginConfig
    
    def _initialize(self) -> None:
        """初始化 Ashare 客户端"""
        try:
            # 导入本地 Ashare 模块
            from .ashare import get_price
            self._ashare_module = get_price
            
            # 测试连接
            self._test_connection()
            
        except ImportError as e:
            raise PluginError(f"Failed to import Ashare module: {e}")
        except Exception as e:
            raise PluginError(f"Failed to initialize Ashare client: {e}")
    
    def _test_connection(self) -> None:
        """测试 Ashare 连接"""
        try:
            # 简单的导入测试，不实际调用API
            # Ashare 是本地模块，不需要网络连接测试
            # 实际的数据获取会在 fetch_data 中进行
            pass
        except Exception as e:
            raise PluginError(f"Ashare connection test failed: {e}")
    
    def fetch_data(self, symbol: str, start_date: str, end_date: str, **kwargs) -> Any:
        """获取股票日K线数据
        
        Args:
            symbol: 股票代码 (如: 000001 或 000001.SZ)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            **kwargs: 额外参数
                - data_type: 数据类型 ('daily', 'weekly', 'monthly')
                - frequency: 数据频率 ('1d', '1w', '1M')
                - adjust: 复权类型 (Ashare 自动处理为qfq)
                
        Returns:
            pandas DataFrame 包含股票数据
        """
        try:
            # 参数处理
            data_type = kwargs.get('data_type', 'daily')
            frequency = kwargs.get('frequency', '1d')
            
            # 清理股票代码格式
            clean_symbol = self._clean_symbol(symbol)
            
            # 检查缓存
            cache_key = f"{clean_symbol}_{data_type}_{frequency}_{start_date}_{end_date}"
            if self._should_use_cache(cache_key):
                return self._cache[cache_key]
            
            # 计算需要获取的数据点数
            count = self._calculate_data_count(start_date, end_date, frequency)
            
            # 调用 Ashare API
            df = self._ashare_module(
                clean_symbol, 
                frequency=frequency, 
                count=count
            )
            
            if df is None or df.empty:
                return pd.DataFrame()
            
            # 数据预处理
            df = self._preprocess_data(df, start_date, end_date)
            
            # 缓存数据
            if self.config.get('cache_enabled', True):
                self._cache[cache_key] = df
                self._last_fetch_time[cache_key] = datetime.now()
            
            return df
            
        except Exception as e:
            raise PluginError(f"Failed to fetch data for {symbol}: {e}")
    
    def _calculate_data_count(self, start_date: str, end_date: str, frequency: str) -> int:
        """计算需要获取的数据点数"""
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        days_diff = (end_dt - start_dt).days + 1
        
        # 根据频率调整数据点数
        if frequency == '1d':  # 日线
            return days_diff + 10  # 多加一些缓冲
        elif frequency == '1w':  # 周线
            return (days_diff // 7) + 5
        elif frequency == '1M':  # 月线
            return (days_diff // 30) + 3
        else:  # 分钟线
            return days_diff * 4 + 20  # 假设每天4小时交易时间
    
    def _clean_symbol(self, symbol: str) -> str:
        """清理股票代码格式"""
        # 移除 .SZ, .SH 等交易所后缀，Ashare 需要标准格式
        if '.' in symbol:
            return symbol
        # 如果没有后缀，添加默认的交易所后缀
        if symbol.startswith('6'):
            return symbol + '.XSHG'
        elif symbol.startswith('0') or symbol.startswith('3'):
            return symbol + '.XSHE'
        return symbol
    
    def _preprocess_data(self, df: pd.DataFrame, start_date: str, end_date: str) -> pd.DataFrame:
        """数据预处理"""
        if df.empty:
            return df
        
        # 确保索引是日期类型
        if hasattr(df.index, 'name') and df.index.name == 'day':
            df.index = pd.to_datetime(df.index)
        
        # 过滤日期范围
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        
        # 确保数据在指定日期范围内
        df = df[(df.index >= start_dt) & (df.index <= end_dt)]
        
        # 标准化列名
        column_mapping = {
            'open': 'open',
            'close': 'close', 
            'high': 'high',
            'low': 'low',
            'volume': 'volume',
            'time': 'date',
            'day': 'date'
        }
        
        df = df.rename(columns=column_mapping)
        
        # 确保必要的列存在
        required_columns = ['open', 'close', 'high', 'low', 'volume']
        for col in required_columns:
            if col not in df.columns:
                df[col] = np.nan
        
        return df
    
    def _should_use_cache(self, cache_key: str) -> bool:
        """检查是否应该使用缓存"""
        if not self.config.get('cache_enabled', True):
            return False
        
        if cache_key not in self._cache:
            return False
        
        if cache_key not in self._last_fetch_time:
            return False
        
        cache_duration = self.config.get('cache_duration', 3600)
        time_diff = (datetime.now() - self._last_fetch_time[cache_key]).total_seconds()
        
        return time_diff < cache_duration
    
    def get_available_symbols(self) -> List[str]:
        """获取可用的股票代码列表
        
        返回沪深创业板的主要股票代码
        """
        # Ashare 不需要预先获取股票列表，可以动态处理
        # 返回一些常见的股票代码
        return [
            '000001.XSHE',  # 平安银行
            '000002.XSHE',  # 万科A
            '000063.XSHE',  # 中兴通讯
            '300001.XSHE',  # 特锐德
            '300002.XSHE',  # 神州泰岳
            '600000.XSHG',  # 浦发银行
            '600036.XSHG',  # 招商银行
            '601318.XSHG',  # 中国平安
            '000300.XSHG',  # 沪深300
            '000001.XSHG',  # 上证指数
            '399001.XSHE',  # 深证成指
            '399006.XSHE',  # 创业板指
        ]
    
    def get_data_types(self) -> List[str]:
        """获取支持的数据类型"""
        return ['daily', 'weekly', 'monthly']
    
    def register(self, registry) -> None:
        """注册插件到框架"""
        # 注册为数据源组件
        registry.register_feature_extractor(self.name, self)
    
    def _cleanup(self) -> None:
        """清理资源"""
        self._cache.clear()
        self._last_fetch_time.clear()
        self._ashare_module = None