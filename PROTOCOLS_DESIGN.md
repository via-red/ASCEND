# ASCEND Core Protocols Design

## 协议设计原则

1. **基于Python Protocol**: 使用`typing.Protocol`而非ABC
2. **完全抽象**: 只定义接口，不提供实现
3. **最小化依赖**: 协议间相互独立
4. **类型安全**: 完整的类型注解

## 核心协议定义

### 1. 状态协议 (State Protocol)
```python
from typing import Protocol, Any, Dict, List
from dataclasses import dataclass
from typing_extensions import TypeAlias

# 基础类型定义
State: TypeAlias = Dict[str, Any]
Action: TypeAlias = Any
Reward: TypeAlias = float
Experience: TypeAlias = Dict[str, Any]
```

### 2. 智能体协议 (IAgent)
```python
class IAgent(Protocol):
    """智能体核心协议，定义决策和学习行为"""
    
    def act(self, state: State) -> Action:
        """根据当前状态选择动作"""
        ...
    
    def learn(self, experiences: List[Experience]) -> Dict[str, Any]:
        """从经验中学习，返回学习指标"""
        ...
    
    def save(self, path: str) -> None:
        """保存智能体状态"""
        ...
    
    def load(self, path: str) -> None:
        """加载智能体状态"""
        ...
    
    def get_config(self) -> Dict[str, Any]:
        """获取智能体配置"""
        ...
```

### 3. 环境协议 (IEnvironment)
```python
class IEnvironment(Protocol):
    """环境交互协议，定义RL环境接口"""
    
    def reset(self) -> State:
        """重置环境到初始状态"""
        ...
    
    def step(self, action: Action) -> tuple[State, Reward, bool, Dict[str, Any]]:
        """执行动作，返回(next_state, reward, done, info)"""
        ...
    
    def render(self) -> Any:
        """渲染环境状态"""
        ...
    
    def close(self) -> None:
        """关闭环境资源"""
        ...
    
    @property
    def observation_space(self) -> Any:
        """观察空间定义"""
        ...
    
    @property
    def action_space(self) -> Any:
        """动作空间定义"""
        ...
```

### 4. 策略协议 (IPolicy)
```python
class IPolicy(Protocol):
    """策略协议，定义决策逻辑"""
    
    def get_action(self, state: State) -> Action:
        """根据状态选择动作"""
        ...
    
    def update(self, experiences: List[Experience]) -> Dict[str, Any]:
        """更新策略参数"""
        ...
    
    def save(self, path: str) -> None:
        """保存策略状态"""
        ...
    
    def load(self, path: str) -> None:
        """加载策略状态"""
        ...
```

### 5. 模型协议 (IModel)
```python
class IModel(Protocol):
    """通用模型协议，支持各种AI模型"""
    
    def predict(self, inputs: Any, **kwargs) -> Any:
        """模型预测"""
        ...
    
    def train(self, data: Any, **kwargs) -> Dict[str, Any]:
        """模型训练"""
        ...
    
    def save(self, path: str) -> None:
        """保存模型"""
        ...
    
    def load(self, path: str) -> None:
        """加载模型"""
        ...
```

### 6. 奖励函数协议 (IRewardFunction)
```python
class IRewardFunction(Protocol):
    """奖励函数协议，定义奖励计算逻辑"""
    
    def calculate(self, 
                 state: State, 
                 action: Action, 
                 next_state: State, 
                 done: bool) -> Reward:
        """计算奖励值"""
        ...
    
    def reset(self) -> None:
        """重置奖励函数状态"""
        ...
```

### 7. 特征提取器协议 (IFeatureExtractor)
```python
class IFeatureExtractor(Protocol):
    """特征提取协议，将原始数据转换为状态表示"""
    
    def extract(self, raw_data: Any) -> State:
        """提取特征"""
        ...
    
    def get_feature_dim(self) -> int:
        """获取特征维度"""
        ...
```

### 8. 插件协议 (IPlugin)
```python
class IPlugin(Protocol):
    """插件协议，定义扩展组件接口"""
    
    def register(self, registry: 'PluginRegistry') -> None:
        """注册插件到框架"""
        ...
    
    def configure(self, config: Dict[str, Any]) -> None:
        """配置插件参数"""
        ...
    
    def get_name(self) -> str:
        """获取插件名称"""
        ...
    
    def get_version(self) -> str:
        """获取插件版本"""
        ...
```

### 9. 监控器协议 (IMonitor)
```python
class IMonitor(Protocol):
    """监控协议，定义训练过程监控"""
    
    def on_step_start(self, step: int, state: State) -> None:
        """步骤开始回调"""
        ...
    
    def on_step_end(self, 
                   step: int, 
                   state: State, 
                   action: Action, 
                   reward: Reward, 
                   next_state: State, 
                   done: bool) -> None:
        """步骤结束回调"""
        ...
    
    def on_episode_start(self, episode: int) -> None:
        """回合开始回调"""
        ...
    
    def on_episode_end(self, episode: int, total_reward: Reward) -> None:
        """回合结束回调"""
        ...
```

## 数据类型定义

### 经验回放缓冲区
```python
@dataclass
class Experience:
    state: State
    action: Action
    reward: Reward
    next_state: State
    done: bool
    info: Dict[str, Any] = None
```

### 训练配置
```python
@dataclass
class TrainingConfig:
    total_timesteps: int = 1000000
    learning_starts: int = 10000
    batch_size: int = 64
    gamma: float = 0.99
    train_freq: int = 4
    target_update_freq: int = 10000
    exploration_fraction: float = 0.1
    exploration_initial_eps: float = 1.0
    exploration_final_eps: float = 0.01
```

## 协议使用示例

### 创建自定义智能体
```python
class MyCustomAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # 初始化组件
    
    def act(self, state: State) -> Action:
        # 自定义决策逻辑
        return action
    
    def learn(self, experiences: List[Experience]) -> Dict[str, Any]:
        # 自定义学习逻辑
        return {"loss": 0.1}
    
    # 实现其他协议方法...
```

### 类型检查
```python
def validate_agent(agent: IAgent) -> bool:
    """验证智能体是否实现协议"""
    return isinstance(agent, IAgent)
```

这个协议设计确保了框架的完全抽象性和技术无关性，同时提供了完整的类型安全和扩展性。