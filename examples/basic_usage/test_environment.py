"""
简单的测试环境实现
用于演示SB3插件的功能
"""

import numpy as np
from typing import Tuple, Dict, Any
import gymnasium as gym
from gymnasium import spaces

from ascend.core.environments import BaseEnvironment
from ascend.core.protocols import State, Action, Reward, Info

class SimpleTestEnvironment(BaseEnvironment):
    """简单的测试环境，模拟CartPole问题"""
    
    def __init__(self, name: str = "simple_test", config: Dict[str, Any] = None):
        if config is None:
            config = {}
        
        # 环境参数（在调用 super().__init__ 之前设置，因为 _setup 需要这些参数）
        self.gravity = config.get('gravity', 9.8)
        self.masscart = config.get('masscart', 1.0)
        self.masspole = config.get('masspole', 0.1)
        self.length = config.get('length', 0.5)
        self.force_mag = config.get('force_mag', 10.0)
        self.tau = config.get('tau', 0.02)  # 时间步长
        self.theta_threshold_radians = config.get('theta_threshold_radians', 12 * 2 * np.pi / 360)
        self.x_threshold = config.get('x_threshold', 2.4)
        self.max_steps = config.get('max_steps', 500)
        
        super().__init__(name, config)
        
        # 状态变量
        self.x = 0.0  # 小车位置
        self.x_dot = 0.0  # 小车速度
        self.theta = 0.0  # 杆角度
        self.theta_dot = 0.0  # 杆角速度
        self.steps = 0
        
    def _setup(self):
        """设置环境空间"""
        # 观察空间: [位置, 速度, 角度, 角速度]
        high = np.array([
            self.x_threshold * 2,
            np.finfo(np.float32).max,
            self.theta_threshold_radians * 2,
            np.finfo(np.float32).max
        ], dtype=np.float32)
        
        self._observation_space = spaces.Box(-high, high, dtype=np.float32)
        
        # 动作空间: 0=向左, 1=向右
        self._action_space = spaces.Discrete(2)
    
    @property
    def observation_space(self):
        return self._observation_space
    
    @property
    def action_space(self):
        return self._action_space
    
    def reset(self) -> State:
        """重置环境到初始状态"""
        self.x = np.random.uniform(-0.05, 0.05)
        self.x_dot = np.random.uniform(-0.05, 0.05)
        self.theta = np.random.uniform(-0.05, 0.05)
        self.theta_dot = np.random.uniform(-0.05, 0.05)
        self.steps = 0
        
        state = self._get_state()
        return state
    
    def step(self, action: Action) -> Tuple[State, Reward, bool, Info]:
        """执行动作"""
        force = self.force_mag if action == 1 else -self.force_mag
        
        # 物理模拟
        costheta = np.cos(self.theta)
        sintheta = np.sin(self.theta)
        
        temp = (force + self.masspole * self.length * self.theta_dot ** 2 * sintheta) / (self.masscart + self.masspole)
        thetaacc = (self.gravity * sintheta - costheta * temp) / (self.length * (4.0/3.0 - self.masspole * costheta ** 2 / (self.masscart + self.masspole)))
        xacc = temp - self.masspole * self.length * thetaacc * costheta / (self.masscart + self.masspole)
        
        # 更新状态
        self.x = self.x + self.tau * self.x_dot
        self.x_dot = self.x_dot + self.tau * xacc
        self.theta = self.theta + self.tau * self.theta_dot
        self.theta_dot = self.theta_dot + self.tau * thetaacc
        
        self.steps += 1
        
        # 检查终止条件
        done = bool(
            self.x < -self.x_threshold
            or self.x > self.x_threshold
            or self.theta < -self.theta_threshold_radians
            or self.theta > self.theta_threshold_radians
            or self.steps >= self.max_steps
        )
        
        # 奖励：每一步都给予+1奖励
        reward = 1.0
        
        state = self._get_state()
        info = {"steps": self.steps}
        
        return state, reward, done, info
    
    def _get_state(self) -> State:
        """获取当前状态"""
        # 返回numpy数组格式的状态，符合SB3的期望
        return np.array([self.x, self.x_dot, self.theta, self.theta_dot], dtype=np.float32)
    
    def render(self) -> Any:
        """渲染环境状态"""
        print(f"Step {self.steps}: x={self.x:.3f}, v={self.x_dot:.3f}, θ={self.theta:.3f}, θ_dot={self.theta_dot:.3f}")
        return None