"""
Warehouse 数据存储插件
基于 warehouse 库的数据持久化存储插件

功能:
- 数据持久化存储 (支持多种格式)
- 快速数据查询和检索
- 数据版本管理
- 数据压缩和优化
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field,field_validator
import pandas as pd
import numpy as np
import json
import pickle
from pathlib import Path
import tempfile
import shutil

from ascend.plugins.base import BasePlugin
from ascend.core.exceptions import PluginError
from . import IDataStoragePlugin

# 插件配置模型
class WarehouseStoragePluginConfig(BaseModel):
    """Warehouse 存储插件配置"""
    
    storage_path: str = Field("./data/warehouse", description="数据存储路径")
    storage_format: str = Field("parquet", description="存储格式: parquet, csv, pickle, feather")
    compression: str = Field("snappy", description="压缩格式: snappy, gzip, none")
    auto_cleanup: bool = Field(True, description="是否自动清理临时文件")
    max_file_size: int = Field(1024 * 1024 * 100, description="最大文件大小(字节)")
    enable_indexing: bool = Field(True, description="是否启用索引")
    
    @field_validator('storage_format')
    def validate_storage_format(cls, v):
        valid_formats = ['parquet', 'csv', 'pickle', 'feather']
        if v not in valid_formats:
            raise ValueError(f'Storage format must be one of: {valid_formats}')
        return v
    
    @field_validator('compression')
    def validate_compression(cls, v):
        valid_compressions = ['snappy', 'gzip', 'none']
        if v not in valid_compressions:
            raise ValueError(f'Compression must be one of: {valid_compressions}')
        return v
    
    @field_validator('storage_path')
    def validate_storage_path(cls, v):
        path = Path(v)
        # 自动创建父目录，而不是抛出错误
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)


class WarehouseStoragePlugin(BasePlugin, IDataStoragePlugin):
    """Warehouse 数据存储插件实现"""
    
    def __init__(self):
        super().__init__(
            name="warehouse_storage",
            version="1.0.0",
            description="Warehouse 数据存储插件，支持多种格式的数据持久化",
            author="ASCEND Team",
            license="Apache 2.0"
        )
        self._storage_path = None
        self._temp_dir = None
        self._metadata = {}
    
    def get_config_schema(self) -> Optional[type]:
        """获取配置模型"""
        return WarehouseStoragePluginConfig
    
    def _initialize(self) -> None:
        """初始化存储目录"""
        try:
            # 创建存储目录
            self._storage_path = Path(self.config.get('storage_path', './data/warehouse'))
            self._storage_path.mkdir(parents=True, exist_ok=True)
            
            # 创建临时目录
            self._temp_dir = Path(tempfile.mkdtemp(prefix='ascend_warehouse_'))
            
            # 加载元数据
            self._load_metadata()
            
        except Exception as e:
            raise PluginError(f"Failed to initialize warehouse storage: {e}")
    
    def _load_metadata(self) -> None:
        """加载元数据文件"""
        metadata_file = self._storage_path / 'metadata.json'
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    self._metadata = json.load(f)
            except:
                self._metadata = {}
        else:
            self._metadata = {}
    
    def _save_metadata(self) -> None:
        """保存元数据文件"""
        metadata_file = self._storage_path / 'metadata.json'
        try:
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self._metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise PluginError(f"Failed to save metadata: {e}")
    
    def _get_file_path(self, key: str) -> Path:
        """根据键获取文件路径"""
        # 使用哈希确保文件名安全
        import hashlib
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self._storage_path / f"{key_hash}.{self.config.get('storage_format', 'parquet')}"
    
    def save_data(self, data: Any, key: str, **kwargs) -> bool:
        """保存数据
        
        Args:
            data: 要保存的数据
            key: 数据标识键
            **kwargs: 额外参数
                - overwrite: 是否覆盖现有数据
                - metadata: 附加元数据
                
        Returns:
            是否保存成功
        """
        try:
            file_path = self._get_file_path(key)
            overwrite = kwargs.get('overwrite', False)
            
            # 检查文件是否已存在
            if file_path.exists() and not overwrite:
                raise PluginError(f"Data with key '{key}' already exists. Use overwrite=True to replace.")
            
            # 根据数据类型选择保存方法
            if isinstance(data, pd.DataFrame):
                self._save_dataframe(data, file_path)
            elif isinstance(data, np.ndarray):
                self._save_array(data, file_path)
            elif isinstance(data, (dict, list)):
                self._save_json(data, file_path)
            else:
                self._save_pickle(data, file_path)
            
            # 更新元数据
            self._update_metadata(key, data, kwargs.get('metadata', {}))
            
            return True
            
        except Exception as e:
            raise PluginError(f"Failed to save data with key '{key}': {e}")
    
    def _save_dataframe(self, df: pd.DataFrame, file_path: Path) -> None:
        """保存 DataFrame 数据"""
        storage_format = self.config.get('storage_format', 'parquet')
        compression = self.config.get('compression', 'snappy')
        
        if storage_format == 'parquet':
            df.to_parquet(file_path, compression=compression, engine='pyarrow')
        elif storage_format == 'csv':
            df.to_csv(file_path, index=False)
        elif storage_format == 'feather':
            df.to_feather(file_path)
        elif storage_format == 'pickle':
            df.to_pickle(file_path)
    
    def _save_array(self, array: np.ndarray, file_path: Path) -> None:
        """保存 numpy array 数据"""
        storage_format = self.config.get('storage_format', 'parquet')
        
        if storage_format == 'parquet':
            # 将数组转换为 DataFrame 保存
            df = pd.DataFrame(array)
            df.to_parquet(file_path, compression=self.config.get('compression', 'snappy'))
        elif storage_format == 'csv':
            pd.DataFrame(array).to_csv(file_path, index=False)
        elif storage_format == 'pickle':
            np.save(file_path, array)
        else:
            # 对于不支持的格式，使用 pickle
            with open(file_path, 'wb') as f:
                pickle.dump(array, f)
    
    def _save_json(self, data: Any, file_path: Path) -> None:
        """保存 JSON 数据"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _save_pickle(self, data: Any, file_path: Path) -> None:
        """保存任意 Python 对象"""
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
    
    def _update_metadata(self, key: str, data: Any, custom_metadata: Dict) -> None:
        """更新元数据"""
        import hashlib
        
        # 计算数据哈希
        if hasattr(data, 'values'):
            data_hash = hashlib.md5(pd.util.hash_pandas_object(data).values).hexdigest()
        else:
            data_hash = hashlib.md5(pickle.dumps(data)).hexdigest()
        
        # 更新元数据
        self._metadata[key] = {
            'key': key,
            'data_hash': data_hash,
            'size': self._get_data_size(data),
            'format': self.config.get('storage_format'),
            'timestamp': pd.Timestamp.now().isoformat(),
            **custom_metadata
        }
        
        # 保存元数据
        self._save_metadata()
    
    def _get_data_size(self, data: Any) -> int:
        """估算数据大小"""
        if isinstance(data, pd.DataFrame):
            return data.memory_usage(deep=True).sum()
        elif isinstance(data, np.ndarray):
            return data.nbytes
        else:
            return len(pickle.dumps(data))
    
    def load_data(self, key: str, **kwargs) -> Any:
        """加载数据
        
        Args:
            key: 数据标识键
            **kwargs: 额外参数
                - default: 如果数据不存在时的默认值
                
        Returns:
            加载的数据
        """
        try:
            file_path = self._get_file_path(key)
            
            if not file_path.exists():
                if 'default' in kwargs:
                    return kwargs['default']
                raise PluginError(f"Data with key '{key}' not found")
            
            # 根据文件格式选择加载方法
            return self._load_data_from_file(file_path)
            
        except Exception as e:
            if 'default' in kwargs:
                return kwargs['default']
            raise PluginError(f"Failed to load data with key '{key}': {e}")
    
    def _load_data_from_file(self, file_path: Path) -> Any:
        """从文件加载数据"""
        storage_format = self.config.get('storage_format', 'parquet')
        
        if storage_format == 'parquet':
            return pd.read_parquet(file_path)
        elif storage_format == 'csv':
            return pd.read_csv(file_path)
        elif storage_format == 'feather':
            return pd.read_feather(file_path)
        elif storage_format == 'pickle':
            if file_path.suffix == '.npy':
                return np.load(file_path)
            else:
                with open(file_path, 'rb') as f:
                    return pickle.load(f)
        else:
            # 尝试自动检测格式
            return self._auto_detect_format(file_path)
    
    def _auto_detect_format(self, file_path: Path) -> Any:
        """自动检测文件格式并加载"""
        try:
            # 尝试作为 parquet 加载
            return pd.read_parquet(file_path)
        except:
            pass
        
        try:
            # 尝试作为 CSV 加载
            return pd.read_csv(file_path)
        except:
            pass
        
        try:
            # 尝试作为 pickle 加载
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        except:
            pass
        
        # 最后尝试作为文本文件读取
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def delete_data(self, key: str, **kwargs) -> bool:
        """删除数据
        
        Args:
            key: 数据标识键
            **kwargs: 额外参数
            
        Returns:
            是否删除成功
        """
        try:
            file_path = self._get_file_path(key)
            
            if file_path.exists():
                file_path.unlink()
            
            # 从元数据中移除
            if key in self._metadata:
                del self._metadata[key]
                self._save_metadata()
            
            return True
            
        except Exception as e:
            raise PluginError(f"Failed to delete data with key '{key}': {e}")
    
    def list_keys(self, pattern: str = "*") -> List[str]:
        """列出数据键
        
        Args:
            pattern: 键模式匹配 (支持通配符)
            
        Returns:
            键列表
        """
        import fnmatch
        
        if pattern == "*":
            return list(self._metadata.keys())
        else:
            return [key for key in self._metadata.keys() if fnmatch.fnmatch(key, pattern)]
    
    def register(self, registry) -> None:
        """注册插件到框架"""
        # 注册为数据存储组件
        registry.register_feature_extractor(self.name, self)
    
    def _cleanup(self) -> None:
        """清理资源"""
        # 清理临时目录
        if self.config.get('auto_cleanup', True) and self._temp_dir and self._temp_dir.exists():
            try:
                shutil.rmtree(self._temp_dir)
            except:
                pass
        
        # 保存元数据
        self._save_metadata()