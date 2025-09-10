# ASCEND Framework Documentation

## 概述

ASCEND (Agent-Native System with Cognitive Embedding for Decision-Making) 是一个基于强化学习的主动式智能体通用框架。它采用完全抽象、协议驱动的设计，支持插件化架构和配置驱动的工作流。

## 核心特性

- 🧠 **强化学习为核心**: 以RL为决策框架，LLM为知识库，专业模型为感知器
- 🔌 **完全插件化**: 所有组件支持热插拔和动态替换
- 📝 **协议导向**: 基于Python Protocol，不依赖具体继承关系
- ⚙️ **配置驱动**: 通过YAML配置定义智能体行为，无需修改代码
- 🚀 **技术无关**: 不绑定特定技术栈，支持多种实现
- 📊 **可扩展性**: 通过钩子函数和动态特征提取器支持无限扩展

## 快速开始

### 安装

```bash
# 安装基础框架
pip install ascend-framework

# 安装可选依赖
pip install ascend-framework[llm,rl,monitoring]

# 从源码安装
git clone https://github.com/ascend-ai/ascend.git
cd ascend
pip install -e ".[dev,llm,rl]"
```

### 基本使用

```python
from ascend import ConfigParser, PluginManager, TrainRunner

# 加载配置
config_parser = ConfigParser()
config = config_parser.load("configs/base.yaml")

# 初始化插件管理器
plugin_manager = PluginManager()
plugin_manager.load_plugins(config['plugins'])

# 创建训练运行器
runner = TrainRunner(config)
runner.setup()

# 开始训练
results = runner.run()

# 清理资源
runner.cleanup()
```

### 配置文件示例

```yaml
# config.yaml
agent:
  type: "ppo_agent"
  config:
    learning_rate: 0.0003
    batch_size: 64

environment:
  type: "gym_env"
  config:
    env_id: "CartPole-v1"

training:
  total_timesteps: 100000

plugins:
  - "ascend_rl_sb3"
  - "ascend_env_gym"
```

## 核心概念

### 1. 智能体 (Agent)

智能体是框架的核心组件，负责决策和学习：

```python
from ascend.core.protocols import IAgent

class MyCustomAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def act(self, state: State) -> Action:
        # 自定义决策逻辑
        return action
    
    def learn(self, experiences: List[Experience]) -> Dict[str, Any]:
        # 自定义学习逻辑
        return {"loss": 0.1}
    
    # 实现其他协议方法...
```

### 2. 环境 (Environment)

环境提供智能体交互的模拟世界：

```python
from ascend.core.protocols import IEnvironment

class CustomEnvironment:
    def reset(self) -> State:
        # 重置环境状态
        return initial_state
    
    def step(self, action: Action) -> Tuple[State, Reward, bool, Dict]:
        # 执行动作并返回结果
        return next_state, reward, done, info
```

### 3. 插件系统

插件扩展框架功能：

```python
from ascend.plugins.base import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__("my_plugin", "0.1.0")
    
    def register(self, registry):
        # 注册组件到框架
        registry.register_agent("my_agent", MyAgent)
        registry.register_environment("my_env", MyEnvironment)
    
    def configure(self, config):
        # 配置插件参数
        self.config = config
```

## 配置指南

### 配置结构

ASCEND使用分层配置结构：

```yaml
# 智能体配置
agent:
  type: "ppo_agent"
  config:
    learning_rate: 0.0003
    batch_size: 64

# 环境配置  
environment:
  type: "gym_env"
  config:
    env_id: "CartPole-v1"

# 训练配置
training:
  total_timesteps: 100000
  eval_freq: 10000

# 插件配置
plugins:
  - "ascend_rl_sb3"
  - "ascend_env_gym"
```

### 环境变量支持

配置支持环境变量注入：

```yaml
models:
  llm:
    type: "openai"
    config:
      api_key: "${OPENAI_API_KEY}"  # 从环境变量获取
```

### 配置继承

支持配置模板继承：

```yaml
# medical_config.yaml
_extends: "base.yaml"

agent:
  type: "medical_agent"
  config:
    learning_rate: 0.0001
    patient_safety_weight: 0.8
```

## 插件开发

### 创建新插件

1. **项目结构**:
```
my_plugin/
├── __init__.py
├── plugin.py
├── config_schema.yaml
└── pyproject.toml
```

2. **插件实现**:
```python
# plugin.py
from ascend.plugins.base import BasePlugin

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__("my_plugin", "0.1.0")
    
    def register(self, registry):
        registry.register_agent("my_agent", MyAgent)
    
    def configure(self, config):
        self.config = config
```

3. **配置入口点**:
```toml
# pyproject.toml
[project.entry-points."ascend.plugins"]
my_plugin = "my_plugin.plugin:MyPlugin"
```

### 插件发布

```bash
# 构建插件
python -m build

# 发布到PyPI
twine upload dist/*
```

## API参考

### 核心协议

#### IAgent Protocol
```python
class IAgent(Protocol):
    def act(self, state: State) -> Action: ...
    def learn(self, experiences: List[Experience]) -> Dict[str, Any]: ...
    def save(self, path: str) -> None: ...
    def load(self, path: str) -> None: ...
```

#### IEnvironment Protocol
```python
class IEnvironment(Protocol):
    def reset(self) -> State: ...
    def step(self, action: Action) -> Tuple[State, Reward, bool, Dict]: ...
    def render(self) -> Any: ...
    def close(self) -> None: ...
```

### 工具函数

#### 配置管理
```python
from ascend.config import ConfigParser

parser = ConfigParser()
config = parser.load("config.yaml")
valid = parser.validate(config)
```

#### 插件管理
```python
from ascend.plugins import PluginManager

manager = PluginManager()
manager.load_plugin("my_plugin", config)
manager.unload_plugin("my_plugin")
```

## 示例应用

### 医疗诊断智能体

```yaml
# configs/medical.yaml
agent:
  type: "medical_diagnosis_agent"
  config:
    learning_rate: 0.0001
    safety_weight: 0.8

environment:
  type: "medical_simulator"
  config:
    disease_types: ["cancer", "diabetes"]

models:
  llm:
    type: "clinical_bert"
  imaging:
    type: "densenet"

plugins:
  - "ascend_medical"
```

### 金融交易智能体

```yaml
# configs/financial.yaml
agent:
  type: "trading_agent"
  config:
    risk_tolerance: 0.3
    learning_rate: 0.0002

environment:
  type: "market_simulator"
  config:
    instruments: ["stock", "forex"]
    data_source: "yahoo_finance"

plugins:
  - "ascend_financial"
```

## 最佳实践

### 1. 配置管理
- 使用环境特定的配置文件
- 利用配置继承减少重复
- 验证配置有效性

### 2. 插件开发
- 保持插件单一职责
- 提供完整的类型注解
- 实现适当的错误处理

### 3. 性能优化
- 使用向量化环境提高吞吐量
- 合理设置批量大小
- 启用混合精度训练

### 4. 监控和调试
- 使用TensorBoard监控训练
- 实现自定义回调函数
- 记录详细的日志信息

## 故障排除

### 常见问题

1. **插件加载失败**
   - 检查插件入口点配置
   - 验证依赖是否安装

2. **配置验证错误**
   - 检查配置格式是否正确
   - 验证必填字段是否提供

3. **性能问题**
   - 检查硬件资源使用情况
   - 优化环境模拟速度

### 获取帮助

- 📖 [详细文档](https://ascend-ai.github.io/ascend)
- 🐛 [提交Issue](https://github.com/ascend-ai/ascend/issues)
- 💬 [讨论区](https://github.com/ascend-ai/ascend/discussions)
- 📧 [联系支持](mailto:support@ascend.ai)

## 贡献指南

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/ascend-ai/ascend.git
cd ascend

# 安装开发依赖
pip install -e ".[dev]"

# 安装预提交钩子
pre-commit install
```

### 代码规范

- 遵循PEP 8风格指南
- 使用类型注解
- 编写单元测试
- 更新文档

### 提交流程

1. Fork项目仓库
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

ASCEND框架采用Apache 2.0许可证开源。详见[LICENSE](LICENSE)文件。

## 版本历史

- **v0.1.0** (2024-01-01): 初始版本发布
  - 核心协议系统
  - 插件化架构
  - 配置驱动框架
  - 基础工具链

---

*更多详细信息和高级用法，请参考[完整文档](https://ascend-ai.github.io/ascend)。*