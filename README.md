# ASCEND Framework

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

Agent-Native System with Cognitive Embedding for Decision-Making

## 项目愿景

当前市场对AI的理解仍停留在"LLM+"的工具化应用层面。我们认为，下一代AI应用将是"智能体原生"（Agent-Native）的。其核心特征是从被动响应走向主动决策与持续优化。

### 三层架构设计

1. **决策层（RL Framework）**
   - 作为"大脑中枢"
   - 设定目标与奖励函数
   - 评估状态、做出决策
   - 持续学习与优化

2. **认知层（LLM & Knowledge）**
   - 理解非结构化信息
   - 生成候选决策方案
   - 提供决策解释
   - 管理知识库

3. **感知层（Domain Models）**
   - 提供精准分析
   - 构建训练环境
   - 执行具体动作
   - 收集反馈

一个基于强化学习的主动式智能体通用框架，采用完全抽象、协议驱动的设计，支持插件化架构和配置驱动的工作流。

## 🚀 核心特性

- **完全抽象**: 只定义接口和协议，不关心具体实现
- **协议导向**: 基于Python Protocol，不依赖继承关系
- **插件化架构**: 所有组件支持热插拔和动态替换
- **配置驱动**: 通过YAML/JSON配置定义智能体行为
- **技术无关**: 不绑定特定技术栈，支持多种实现

## 📦 快速开始

请访问我们的[开发者指南](./DEVELOPER_GUIDE.md)获取详细的安装和使用说明。



## 🏗️ 架构设计

### 核心协议

ASCEND框架基于以下核心协议构建：

1. **`IAgent`** - 智能体协议，定义决策和学习行为
2. **`IEnvironment`** - 环境交互协议，定义RL环境接口
3. **`IPolicy`** - 策略协议，定义决策逻辑
4. **`IModel`** - 通用模型协议，支持各种AI模型
5. **`IRewardFunction`** - 奖励函数协议，定义奖励计算逻辑
6. **`IFeatureExtractor`** - 特征提取协议，将原始数据转换为状态表示
7. **`IPlugin`** - 插件协议，定义扩展组件接口
8. **`IMonitor`** - 监控协议，定义训练过程监控

### 系统层次

1. **核心层 (Core Layer)**: 协议定义和基础抽象
2. **插件层 (Plugin Layer)**: LLM集成、RL算法、领域特定模型等插件
3. **扩展层 (Extension Layer)**: 特征提取、监控、自定义回调等钩子

## 🔌 插件系统

ASCEND框架提供了强大的插件系统，支持功能扩展和自定义实现。详细信息请参考[开发者指南](./DEVELOPER_GUIDE.md)的插件开发章节。

## 📚 核心概念

### 状态和动作

```python
from ascend import State, Action, Reward

# 状态类型: Dict[str, Any]
state: State = {"observation": [1, 2, 3], "info": {}}

# 动作类型: Any
action: Action = 0

# 奖励类型: float
reward: Reward = 1.0
```

### 经验回放

```python
from ascend import Experience

experience = Experience(
    state=state,
    action=action,
    reward=reward,
    next_state=next_state,
    done=False,
    info={}
)
```

## 🧪 示例和教程

项目包含多个示例代码：

- [`examples/basic_usage/`](examples/basic_usage/) - 基础使用示例
- [`examples/advanced/`](examples/advanced/) - 高级功能示例
- [`examples/custom_plugins/`](examples/custom_plugins/) - 自定义插件示例

运行基础示例：

```bash
cd examples/basic_usage
python basic_example.py
```

## 🧩 模块结构

```
ascend/
├── core/           # 核心协议和抽象
│   ├── protocols.py    # 协议定义
│   ├── types.py       # 类型定义
│   ├── exceptions.py  # 异常定义
│   └── __init__.py
├── config/         # 配置系统
│   ├── parser.py      # 配置解析
│   ├── validator.py   # 配置验证
│   ├── loader.py      # 配置加载
│   └── __init__.py
├── plugins/        # 插件系统
│   ├── base.py        # 插件基类
│   ├── manager.py     # 插件管理
│   ├── discovery.py   # 插件发现
│   └── __init__.py
├── runners/        # 运行器（开发中）
├── utils/          # 工具函数（开发中）
└── __init__.py
```

## 🧪 测试

运行测试套件：

```bash
# 运行所有测试
pytest

# 运行特定测试模块
pytest tests/unit/test_core.py

# 带覆盖率报告
pytest --cov=ascend --cov-report=html
```

## 🤝 贡献指南

我们欢迎贡献！请参阅以下指南：

1. Fork 项目仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

### 开发设置

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 安装预提交钩子
pre-commit install

# 运行代码格式化
black ascend/ tests/ examples/
isort ascend/ tests/ examples/
```

## 📄 许可证

本项目采用 Apache 2.0 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 📞 支持

- 📖 [文档](https://ascend-ai.github.io/ascend)
- 🐛 [问题报告](https://github.com/ascend-ai/ascend/issues)
- 💬 [讨论区](https://github.com/ascend-ai/ascend/discussions)
- 📧 邮箱: contact@ascend.ai

## 🙏 致谢

感谢所有为ASCEND框架做出贡献的开发者和研究人员！

---

**ASCEND** - 构建下一代智能体系统的通用框架 🚀
