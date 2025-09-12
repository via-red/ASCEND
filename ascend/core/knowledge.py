"""
基础知识库实现模块

提供了一个实现IKnowledgeBase协议的基础知识库类，作为所有具体知识库实现的基类。
包含了基础的知识存储、查询和更新功能。
"""

from typing import Dict, Any, List
import logging
import json
import os
from abc import ABC, abstractmethod

from .protocols import IKnowledgeBase, Knowledge

logger = logging.getLogger(__name__)

class BaseKnowledgeBase(ABC):
    """基础知识库实现
    
    实现了IKnowledgeBase协议的抽象基类，提供了知识管理的基础功能框架。
    具体的知识库类需要继承该类并实现抽象方法。
    
    Attributes:
        name (str): 知识库名称
        config (Dict[str, Any]): 配置参数
        knowledge_store (Dict[str, Knowledge]): 知识存储
    """
    
    def __init__(self, name: str, config: Dict[str, Any]) -> None:
        """初始化知识库
        
        Args:
            name: 知识库名称
            config: 配置参数字典
        """
        self.name = name
        self.config = config
        self.knowledge_store = {}
        self._init_store()
        logger.info(f"Initialized knowledge base {self.name}")
    
    def _init_store(self) -> None:
        """初始化知识存储
        
        可以在子类中重写以添加初始化知识
        """
        pass
    
    @abstractmethod
    def query(self, context: Dict[str, Any]) -> Knowledge:
        """查询知识
        
        Args:
            context: 查询上下文
            
        Returns:
            相关知识
        """
        raise NotImplementedError
    
    def update(self, new_knowledge: Knowledge) -> None:
        """更新知识库
        
        Args:
            new_knowledge: 新知识
        """
        self.knowledge_store.update(new_knowledge)
        logger.info(f"Updated knowledge base {self.name}")
    
    def clear(self) -> None:
        """清空知识库"""
        self.knowledge_store.clear()
        logger.info(f"Cleared knowledge base {self.name}")
    
    def save(self, path: str) -> None:
        """保存知识库到文件
        
        Args:
            path: 保存路径
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.knowledge_store, f)
        logger.info(f"Saved knowledge base {self.name} to {path}")
    
    def load(self, path: str) -> None:
        """从文件加载知识库
        
        Args:
            path: 加载路径
        """
        with open(path, 'r') as f:
            self.knowledge_store = json.load(f)
        logger.info(f"Loaded knowledge base {self.name} from {path}")
    
    def get_config(self) -> Dict[str, Any]:
        """获取知识库配置
        
        Returns:
            配置字典的深拷贝
        """
        return self.config.copy()
    
    def get_size(self) -> int:
        """获取知识库大小
        
        Returns:
            知识条目数量
        """
        return len(self.knowledge_store)
    
    def list_keys(self) -> List[str]:
        """列出所有知识键
        
        Returns:
            知识键列表
        """
        return list(self.knowledge_store.keys())
    
    def delete_knowledge(self, key: str) -> None:
        """删除指定知识
        
        Args:
            key: 知识键
        """
        if key in self.knowledge_store:
            del self.knowledge_store[key]
            logger.info(f"Deleted knowledge {key} from {self.name}")