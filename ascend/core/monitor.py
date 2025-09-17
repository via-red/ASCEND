"""
基础监控实现模块

提供了一个实现IMonitor协议的基础监控类，作为所有具体监控实现的基类。
包含了基础的训练过程监控和指标记录功能。
"""

from typing import Dict, Any, List, Optional
import logging
import time

from dataclasses import dataclass, field
from datetime import datetime

from .protocols import IMonitor, State, Action, Reward

logger = logging.getLogger(__name__)

@dataclass
class EpisodeStats:
    """回合统计数据类
    
    Attributes:
        episode_id: 回合ID
        total_reward: 总奖励
        steps: 步数
        start_time: 开始时间
        end_time: 结束时间
        metrics: 其他指标
    """
    episode_id: int
    total_reward: float = 0.0
    steps: int = 0
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

class BaseMonitor(IMonitor):
    """基础监控实现
    
    实现了IMonitor协议的基类，提供了监控的基础功能框架。
    具体的监控类可以继承该类并重写相关方法以添加自定义功能。
    
    Attributes:
        name (str): 监控模块名称
        config (Dict[str, Any]): 配置参数
        current_episode (Optional[EpisodeStats]): 当前回合的统计信息
        episode_history (List[EpisodeStats]): 历史回合统计信息
    """
    
    def __init__(self, name: str, config: Dict[str, Any]) -> None:
        """初始化监控模块
        
        Args:
            name: 监控模块名称
            config: 配置参数字典
        """
        self.name = name
        self.config = config
        self.current_episode: Optional[EpisodeStats] = None
        self.episode_history: List[EpisodeStats] = []
        self._init_monitor()
        logger.info(f"Initialized monitor {self.name}")
    
    def _init_monitor(self) -> None:
        """初始化监控组件
        
        可以在子类中重写以添加额外的监控组件初始化
        """
        pass
    
    def on_step_start(self, step: int, state: State) -> None:
        """步骤开始回调
        
        Args:
            step: 步骤数
            state: 当前状态
        """
        if self.current_episode:
            self.current_episode.steps = step
    
    def on_step_end(self, step: int, state: State, action: Action, 
                   reward: Reward, next_state: State, done: bool) -> None:
        """步骤结束回调
        
        Args:
            step: 步骤数
            state: 当前状态
            action: 执行的动作
            reward: 获得的奖励
            next_state: 下一个状态
            done: 是否结束
        """
        if self.current_episode:
            self.current_episode.total_reward += reward
            if done:
                self.current_episode.end_time = time.time()
    
    def on_episode_start(self, episode: int) -> None:
        """回合开始回调
        
        Args:
            episode: 回合数
        """
        self.current_episode = EpisodeStats(episode_id=episode)
        logger.info(f"Episode {episode} started")
    
    def on_episode_end(self, episode: int, total_reward: Reward) -> None:
        """回合结束回调
        
        Args:
            episode: 回合数
            total_reward: 总奖励
        """
        if self.current_episode:
            self.current_episode.end_time = time.time()
            self.current_episode.total_reward = total_reward
            self.episode_history.append(self.current_episode)
            duration = self.current_episode.end_time - self.current_episode.start_time
            logger.info(f"Episode {episode} ended - Total Reward: {total_reward:.2f}, "
                       f"Steps: {self.current_episode.steps}, Duration: {duration:.2f}s")
            self.current_episode = None
    
    def get_episode_stats(self, episode: int) -> Optional[EpisodeStats]:
        """获取指定回合的统计信息
        
        Args:
            episode: 回合ID
            
        Returns:
            回合统计信息，如果不存在则返回None
        """
        for stats in self.episode_history:
            if stats.episode_id == episode:
                return stats
        return None
    
    def get_latest_stats(self) -> Optional[EpisodeStats]:
        """获取最新回合的统计信息
        
        Returns:
            最新回合统计信息，如果没有则返回None
        """
        return self.episode_history[-1] if self.episode_history else None
    
    def get_episode_history(self) -> List[EpisodeStats]:
        """获取所有回合的统计历史
        
        Returns:
            回合统计历史列表
        """
        return self.episode_history.copy()
    
    def get_config(self) -> Dict[str, Any]:
        """获取监控模块配置
        
        Returns:
            配置字典的深拷贝
        """
        return self.config.copy()
    
    def clear_history(self) -> None:
        """清空历史统计信息"""
        self.episode_history.clear()
        logger.info(f"Cleared monitor {self.name} history")
    
    def export_stats(self, path: str) -> None:
        """导出统计信息到文件
        
        Args:
            path: 导出文件路径
        """
        # 子类可以重写以实现具体的导出逻辑
        pass
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """更新配置参数
        
        Args:
            new_config: 新的配置参数
        """
        self.config.update(new_config)
        logger.info(f"Updated monitor {self.name} config")