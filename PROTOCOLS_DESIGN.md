# ASCEND Core Protocols Design

## 协议设计原则

1. **基于Python Protocol**: 使用`typing.Protocol`而非ABC
2. **完全抽象**: 只定义接口，不提供实现
3. **最小化依赖**: 协议间相互独立
4. **类型安全**: 完整的类型注解

## 核心协议定义

### 1. 基础类型定义

框架定义了以下核心类型：

- **State**: 表示环境状态的字典类型，可包含任意类型的观察数据
- **Action**: 表示智能体动作的通用类型，支持离散和连续动作空间
- **Reward**: 表示奖励信号的浮点数类型
- **Experience**: 包含状态转换信息的字典类型，用于训练和优化

### 2. 智能体协议 (IAgent)

智能体是框架的核心抽象，定义了智能体的基本行为和能力：

1. **决策能力 (act)**
   - 接收当前环境状态
   - 返回选择的动作
   - 支持确定性和随机策略

2. **学习能力 (learn)**
   - 从经验数据中学习
   - 优化决策策略
   - 返回学习指标

3. **状态管理**
   - 保存智能体状态
   - 加载已有模型
   - 管理训练进度

4. **配置管理**
   - 获取当前配置
   - 动态更新参数
   - 支持热重载

### 3. 环境协议 (IEnvironment)

环境协议定义了智能体可以交互的世界模型：

1. **状态转换**
   - 接收智能体动作
   - 返回新的状态、奖励和完成标志
   - 提供额外的环境信息

2. **环境控制**
   - 重置到初始状态
   - 渲染环境状态
   - 管理环境资源

3. **空间定义**
   - 定义观察空间
   - 定义动作空间
   - 约束交互范围

4. **资源管理**
   - 创建环境实例
   - 释放系统资源
   - 确保清理完成

### 4. 策略协议 (IPolicy)

策略协议定义了智能体的决策方法：

1. **动作选择**
   - 基于当前状态
   - 支持探索与利用
   - 处理连续和离散动作

2. **策略更新**
   - 从经验中学习
   - 优化策略参数
   - 返回更新指标

3. **状态维护**
   - 保存策略状态
   - 加载已有策略
   - 管理版本信息

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