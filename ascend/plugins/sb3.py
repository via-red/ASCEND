"""
Stable-Baselines3 (SB3) 强化学习插件模块

提供了与 Stable-Baselines3 库的集成，包括:
- 算法适配器：封装 SB3 的算法接口
- 环境适配器：使 ASCEND 环境可用于 SB3
- 策略封装：包装 SB3 的策略为 ASCEND 策略接口
"""

from typing import Dict, Any, Type, Optional, Union, List
import logging
import gymnasium as gym
import numpy as np
from pydantic import BaseModel, Field
from stable_baselines3 import PPO, A2C, DQN, SAC, TD3
from stable_baselines3.common.policies import BasePolicy
from stable_baselines3.common.vec_env import DummyVecEnv

from ..core.protocols import IAgent, IEnvironment, IPolicy, State, Action, Experience
from ..core.types import PolicyType
from .base import BasePlugin, IPlugin

logger = logging.getLogger(__name__)

# 支持的 SB3 算法映射
SUPPORTED_ALGORITHMS = {
    'ppo': PPO,
    'a2c': A2C,
    'dqn': DQN,
    'sac': SAC,
    'td3': TD3
}

class SB3PluginConfig(BaseModel):
    """SB3 插件配置模型
    
    Attributes:
        algorithm: 使用的算法名称
        policy: 使用的策略网络类型
        learning_rate: 学习率
        batch_size: 批次大小
        n_steps: 每次更新的步数
        device: 运行设备
        verbose: 日志级别
    """
    algorithm: str = Field(..., description="算法名称，支持: ppo, a2c, dqn, sac, td3")
    policy: str = Field("MlpPolicy", description="策略网络类型")
    learning_rate: float = Field(3e-4, description="学习率", gt=0, le=1)
    batch_size: int = Field(64, description="批次大小", gt=0)
    n_steps: int = Field(2048, description="每次更新的步数", gt=0)
    device: str = Field("auto", description="运行设备")
    verbose: int = Field(1, description="日志级别", ge=0)

class SB3EnvironmentWrapper(gym.Env):
    """ASCEND 环境到 Gym 环境的适配器
    
    将 ASCEND 的环境接口适配为 Gym 接口，使其可用于 SB3 算法。
    
    Attributes:
        env: ASCEND 环境实例
    """
    
    def __init__(self, env: IEnvironment) -> None:
        """初始化环境包装器
        
        Args:
            env: ASCEND 环境实例
        """
        super().__init__()
        self.env = env
        self.action_space = env.action_space
        self.observation_space = env.observation_space
    
    def reset(self, **kwargs):
        """重置环境
        
        Returns:
            初始观察
        """
        return self.env.reset()
    
    def step(self, action):
        """执行动作
        
        Args:
            action: 动作
            
        Returns:
            (observation, reward, done, info) 元组
        """
        return self.env.step(action)
    
    def render(self, mode='human'):
        """渲染环境
        
        Args:
            mode: 渲染模式
            
        Returns:
            渲染结果
        """
        return self.env.render()
    
    def close(self):
        """关闭环境"""
        self.env.close()

class SB3PolicyWrapper(IPolicy):
    """SB3 策略到 ASCEND 策略的适配器
    
    将 SB3 的策略接口适配为 ASCEND 策略接口。
    
    Attributes:
        name: 策略名称
        model: SB3 模型实例
        config: 配置参数
    """
    
    def __init__(self, name: str, model: BasePolicy, config: Dict[str, Any]) -> None:
        """初始化策略包装器
        
        Args:
            name: 策略名称
            model: SB3 模型实例
            config: 配置参数
        """
        self.name = name
        self.model = model
        self.config = config
    
    def get_action(self, state: State) -> Action:
        """获取动作
        
        Args:
            state: 当前状态
            
        Returns:
            选择的动作
        """
        action, _ = self.model.predict(state, deterministic=True)
        return action
    
    def update(self, experiences: List[Experience]) -> Dict[str, Any]:
        """更新策略
        
        Args:
            experiences: 经验数据
            
        Returns:
            更新指标
        """
        # SB3 模型通过自己的方式更新，这里返回空字典
        return {}
    
    def save(self, path: str) -> None:
        """保存策略
        
        Args:
            path: 保存路径
        """
        self.model.save(path)
    
    def load(self, path: str) -> None:
        """加载策略
        
        Args:
            path: 加载路径
        """
        self.model = self.model.load(path)

from .base import register_builtin_plugin

@register_builtin_plugin
class SB3Plugin(BasePlugin):
    """Stable-Baselines3 插件实现
    
    提供与 SB3 库的集成，支持常用的强化学习算法。
    
    Attributes:
        name: 插件名称
        version: 插件版本
        config: 配置参数
        model: SB3 模型实例
    """
    
    def __init__(self) -> None:
        """初始化插件"""
        super().__init__(
            name="rl_sb3",
            version="0.1.0",
            description="Integrates Stable Baselines3 for RL agents and policies."
        )
        self.config: Optional[SB3PluginConfig] = None
        self.model = None
    
    def register(self, registry: 'IPluginRegistry') -> None:
        """注册插件
        
        Args:
            registry: 插件注册表
        """
        try:
            import stable_baselines3
            registry.register_plugin(self.name, self)
            logger.info(f"Registered plugin: {self.name} v{self.version}")
            
            # 注册算法组件
            for algo_name, algo_cls in SUPPORTED_ALGORITHMS.items():
                registry.register_agent(f"{algo_name}_sb3", self.create_agent)
                logger.info(f"Registered algorithm: {algo_name}")
        except ImportError:
            logger.warning("Failed to register SB3 plugin: stable_baselines3 not installed. Please run 'pip install stable-baselines3'")
            raise
    
    def configure(self, config: Dict[str, Any]) -> None:
        """配置插件
        
        Args:
            config: 配置参数
        """
        try:
            self.config = SB3PluginConfig(**config)
            logger.info(f"Configured SB3 plugin with algorithm: {self.config.algorithm}")
        except Exception as e:
            logger.error(f"Failed to configure SB3 plugin: {e}")
            raise
    
    def create_agent(self, env: IEnvironment) -> IAgent:
        """创建智能体
        
        Args:
            env: 环境实例
            
        Returns:
            智能体实例
        """
        if not self.config:
            raise ValueError("Plugin not configured")
            
        # 包装环境
        wrapped_env = SB3EnvironmentWrapper(env)
        vec_env = DummyVecEnv([lambda: wrapped_env])
        
        # 获取算法类
        algorithm_cls = SUPPORTED_ALGORITHMS.get(self.config.algorithm.lower())
        if not algorithm_cls:
            raise ValueError(f"Unsupported algorithm: {self.config.algorithm}")
        
        # 创建模型
        self.model = algorithm_cls(
            self.config.policy,
            vec_env,
            learning_rate=self.config.learning_rate,
            batch_size=self.config.batch_size,
            device=self.config.device,
            verbose=self.config.verbose
        )
        
        # 包装策略
        policy = SB3PolicyWrapper(
            name=f"sb3_{self.config.algorithm}",
            model=self.model,
            config=self.config.dict()
        )
        
        # 返回智能体
        from ..core.agents import BaseAgent

        class SB3Agent(BaseAgent):
            """SB3代理类
            """
            def process_observation(self, observation, **kwargs):
                """处理环境观察
                """
                return observation
            
            def explain(self, **kwargs):
                """解释代理的决策
                """
                return {"explanation": "SB3代理使用神经网络策略进行决策"}
        
        return SB3Agent(
            name=f"sb3_{self.config.algorithm}_agent",
            policy=policy,
            config=self.config.dict()
        )
    
    def get_name(self) -> str:
        """获取插件名称
        
        Returns:
            插件名称
        """
        return self.name
    
    def get_version(self) -> str:
        """获取插件版本
        
        Returns:
            插件版本
        """
        return self.version
    
    def get_metadata(self) -> Dict[str, Any]:
        """获取插件元数据
        
        Returns:
            元数据字典
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": "Stable-Baselines3 强化学习算法集成",
            "supported_algorithms": list(SUPPORTED_ALGORITHMS.keys())
        }
    
    def get_config_schema(self) -> Optional[Type[BaseModel]]:
        """获取配置模式
        
        Returns:
            配置模式类
        """
        return SB3PluginConfig

from pydantic import BaseModel, Field, PositiveInt

from ascend.plugins.base import BasePlugin
from ascend.core.protocols import IPluginRegistry
from ascend.core.exceptions import PluginError


