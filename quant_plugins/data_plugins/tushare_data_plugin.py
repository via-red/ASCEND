"""
Tushare 数据源插件
基于 Tushare API 的股票数据获取插件

功能:
- 获取沪深创业板股票日K线数据
- 支持多种数据类型的获取
- 自动数据更新和维护
- 支持批量数据获取
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ascend.plugins.base import BasePlugin
from ascend.core.exceptions import PluginError
from . import IDataSourcePlugin

# 插件配置模型
class TushareDataPluginConfig(BaseModel):
    """Tushare 数据插件配置"""
    
    token: str = Field(..., description="Tushare API token")
    timeout: int = Field(30, description="API请求超时时间(秒)")
    max_retries: int = Field(3, description="最大重试次数")
    cache_enabled: bool = Field(True, description="是否启用缓存")
    cache_duration: int = Field(3600, description="缓存持续时间(秒)")
    
    @validator('token')
    def validate_token(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Tushare token cannot be empty')
        return v.strip()
    
    @validator('timeout')
    def validate_timeout(cls, v):
        if v < 1:
            raise ValueError('Timeout must be at least 1 second')
        return v
    
    @validator('max_retries')
    def validate_max_retries(cls, v):
        if v < 0:
            raise ValueError('Max retries cannot be negative')
        return v


class TushareDataPlugin(BasePlugin, IDataSourcePlugin):
    """Tushare 数据源插件实现"""
    
    def __init__(self):
        super().__init__(
            name="tushare_data",
            version="1.0.0",
            description="Tushare API数据源插件，支持沪深创业板股票数据获取",
            author="ASCEND Team",
            license="Apache 2.0"
        )
        self._tushare_pro = None
        self._cache = {}
        self._last_fetch_time = {}
    
    def get_config_schema(self) -> Optional[type]:
        """获取配置模型"""
        return TushareDataPluginConfig
    
    def _initialize(self) -> None:
        """初始化 Tushare 客户端"""
        try:
            # 延迟导入，避免没有安装 tushare 时无法导入
            import tushare as ts
            self._tushare_pro = ts.pro_api(self.config.get('token'))
            
            # 测试连接
            self._test_connection()
            
        except ImportError:
            raise PluginError("Tushare package not installed. Please install with: pip install tushare")
        except Exception as e:
            raise PluginError(f"Failed to initialize Tushare client: {e}")
    
    def _test_connection(self) -> None:
        """测试 Tushare 连接"""
        try:
            # 简单的 API 调用测试
            df = self._tushare_pro.trade_cal(exchange='', start_date='20230101', end_date='20230102')
            if df.empty:
                raise PluginError("Tushare API connection test failed")
        except Exception as e:
            raise PluginError(f"Tushare connection test failed: {e}")
    
    def fetch_data(self, symbol: str, start_date: str, end_date: str, **kwargs) -> Any:
        """获取股票日K线数据
        
        Args:
            symbol: 股票代码 (如: 000001.SZ)
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            **kwargs: 额外参数
                - data_type: 数据类型 ('daily', 'weekly', 'monthly')
                - adjust: 复权类型 ('none', 'qfq', 'hfq')
                
        Returns:
            pandas DataFrame 包含股票数据
        """
        try:
            # 参数处理
            data_type = kwargs.get('data_type', 'daily')
            adjust = kwargs.get('adjust', 'qfq')
            
            # 检查缓存
            cache_key = f"{symbol}_{data_type}_{adjust}_{start_date}_{end_date}"
            if self._should_use_cache(cache_key):
                return self._cache[cache_key]
            
            # 根据数据类型调用不同的 API
            if data_type == 'daily':
                df = self._fetch_daily_data(symbol, start_date, end_date, adjust)
            elif data_type == 'weekly':
                df = self._fetch_weekly_data(symbol, start_date, end_date, adjust)
            elif data_type == 'monthly':
                df = self._fetch_monthly_data(symbol, start_date, end_date, adjust)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
            
            # 缓存数据
            if self.config.get('cache_enabled', True):
                self._cache[cache_key] = df
                self._last_fetch_time[cache_key] = datetime.now()
            
            return df
            
        except Exception as e:
            raise PluginError(f"Failed to fetch data for {symbol}: {e}")
    
    def _fetch_daily_data(self, symbol: str, start_date: str, end_date: str, adjust: str) -> pd.DataFrame:
        """获取日线数据"""
        # 转换日期格式
        start_date_ts = start_date.replace('-', '')
        end_date_ts = end_date.replace('-', '')
        
        # 调用 Tushare API
        df = self._tushare_pro.daily(
            ts_code=symbol,
            start_date=start_date_ts,
            end_date=end_date_ts,
            adj=adjust
        )
        
        # 数据预处理
        if not df.empty:
            df = self._preprocess_data(df)
        
        return df
    
    def _fetch_weekly_data(self, symbol: str, start_date: str, end_date: str, adjust: str) -> pd.DataFrame:
        """获取周线数据"""
        # 转换日期格式
        start_date_ts = start_date.replace('-', '')
        end_date_ts = end_date.replace('-', '')
        
        try:
            # 调用 Tushare 周线API
            df = self._tushare_pro.weekly(
                ts_code=symbol,
                start_date=start_date_ts,
                end_date=end_date_ts,
                adj=adjust
            )
            
            # 数据预处理
            if not df.empty:
                df = self._preprocess_data(df)
            
            return df
            
        except Exception as e:
            self.logger.warning(f"Failed to fetch weekly data for {symbol}: {e}")
            return pd.DataFrame()
    
    def _fetch_monthly_data(self, symbol: str, start_date: str, end_date: str, adjust: str) -> pd.DataFrame:
        """获取月线数据"""
        # 转换日期格式
        start_date_ts = start_date.replace('-', '')
        end_date_ts = end_date.replace('-', '')
        
        try:
            # 调用 Tushare 月线API
            df = self._tushare_pro.monthly(
                ts_code=symbol,
                start_date=start_date_ts,
                end_date=end_date_ts,
                adj=adjust
            )
            
            # 数据预处理
            if not df.empty:
                df = self._preprocess_data(df)
            
            return df
            
        except Exception as e:
            self.logger.warning(f"Failed to fetch monthly data for {symbol}: {e}")
            return pd.DataFrame()
    
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据预处理"""
        # 转换日期格式
        if 'trade_date' in df.columns:
            df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
            df = df.sort_values('trade_date')
        
        # 重置索引
        df = df.reset_index(drop=True)
        
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
        try:
            # 尝试从 Tushare API 获取股票列表
            if self._tushare_pro:
                # 获取沪深主板、创业板、科创板股票
                df = self._tushare_pro.stock_basic(
                    exchange='',
                    list_status='L',
                    fields='ts_code,name,market,list_date'
                )
                if not df.empty:
                    return df['ts_code'].tolist()
            
            # 如果API调用失败，返回默认股票列表
            return [
                '000001.SZ',  # 平安银行
                '000002.SZ',  # 万科A
                '000063.SZ',  # 中兴通讯
                '300001.SZ',  # 特锐德
                '300002.SZ',  # 神州泰岳
                '600000.SH',  # 浦发银行
                '600036.SH',  # 招商银行
                '601318.SH',  # 中国平安
            ]
        except Exception as e:
            self.logger.warning(f"Failed to get available symbols from Tushare: {e}")
            # 返回默认股票列表
            return [
                '000001.SZ',  # 平安银行
                '000002.SZ',  # 万科A
                '000063.SZ',  # 中兴通讯
                '300001.SZ',  # 特锐德
                '300002.SZ',  # 神州泰岳
                '600000.SH',  # 浦发银行
                '600036.SH',  # 招商银行
                '601318.SH',  # 中国平安
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
        self._tushare_pro = None