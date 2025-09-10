# ASCEND Project Structure

## 整体目录结构

```
ascend/
├── ascend/                    # 核心框架包
│   ├── core/                 # 核心抽象和协议
│   │   ├── __init__.py
│   │   ├── protocols.py      # 核心协议定义
│   │   ├── types.py         # 类型定义和别名
│   │   ├── exceptions.py    # 异常类定义
│   │   └── constants.py     # 常量定义
│   │
│   ├── config/              # 配置系统
│   │   ├── __init__.py
│   │   ├── parser.py        # 配置解析器
│   │   ├── validator.py     # 配置验证器
│   │   ├── loader.py        # 配置加载器
│   │   └── schemas/         # 配置模式定义
│   │       ├── agent.yaml
│   │       ├── environment.yaml
│   │       └── training.yaml
│   │
│   ├── plugins/             # 插件系统
│   │   ├── __init__.py
│   │   ├── registry.py      # 插件注册表
│   │   ├── manager.py       # 插件管理器
│   │   ├── discovery.py     # 插件发现机制
│   │   └── base.py          # 基础插件类
│   │
│   ├── utils/               # 工具函数
│   │   ├── __init__.py
│   │   ├── logging.py       # 日志工具
│   │   ├── validation.py    # 验证工具
│   │   ├── serialization.py # 序列化工具
│   │   └── compat.py        # 兼容性工具
│   │
│   ├── runners/             # 运行器组件
│   │   ├── __init__.py
│   │   ├── base_runner.py   # 基础运行器
│   │   ├── train_runner.py  # 训练运行器
│   │   ├── eval_runner.py   # 评估运行器
│   │   └── deploy_runner.py # 部署运行器
│   │
│   └── __init__.py          # 包初始化
│
├── plugins/                 # 官方插件目录
│   ├── ascend_llm_openai/   # OpenAI LLM插件
│   │   ├── __init__.py
│   │   ├── plugin.py
│   │   └── config_schema.yaml
│   │
│   ├── ascend_rl_sb3/       # Stable Baselines3插件
│   │   ├── __init__.py
│   │   ├── plugin.py
│   │   └── config_schema.yaml
│   │
│   ├── ascend_env_gym/      # OpenAI Gym环境插件
│   │   └── ...             
│   │
│   └── ascend_monitor_tb/   # TensorBoard监控插件
│       └── ...
│
├── examples/                # 使用示例
│   ├── basic_usage/         # 基础使用示例
│   │   ├── config.yaml
│   │   ├── train.py
│   │   └── README.md
│   │
│   ├── medical_agent/       # 医疗智能体示例
│   │   ├── config.yaml
│   │   ├── custom_plugins/
│   │   └── medical_simulator.py
│   │
│   ├── financial_agent/     # 金融智能体示例
│   │   └── ...
│   │
│   └── industrial_agent/    # 工业智能体示例
│       └── ...
│
├── tests/                   # 测试目录
│   ├── unit/               # 单元测试
│   │   ├── test_core.py
│   │   ├── test_config.py
│   │   └── test_plugins.py
│   │
│   ├── integration/        # 集成测试
│   │   ├── test_full_pipeline.py
│   │   └── test_plugin_integration.py
│   │
│   └── conftest.py         # pytest配置
│
├── configs/                # 配置文件模板
│   ├── base.yaml          # 基础配置模板
│   ├── medical.yaml       # 医疗领域配置
│   ├── financial.yaml     # 金融领域配置
│   ├── industrial.yaml    # 工业领域配置
│   └── research.yaml      # 研究用途配置
│
├── docs/                   # 文档目录
│   ├── getting_started.md
│   ├── api_reference.md
│   ├── plugin_development.md
│   ├── configuration_guide.md
│   └── examples/
│
├── scripts/                # 工具脚本
│   ├── setup_environment.sh
│   ├── run_tests.sh
│   ├── build_docs.sh
│   └── release.py
│
├── .github/               # GitHub配置
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── test.yml
│   │   └── release.yml
│   └── ISSUE_TEMPLATE/
│
├── pyproject.toml         # 项目配置和依赖
├── setup.py              # 安装脚本（兼容旧版本）
├── requirements.txt      # 依赖文件
├── requirements-dev.txt  # 开发依赖
├── README.md            # 项目说明
├── LICENSE              # 许可证
└── CONTRIBUTING.md      # 贡献指南
```

## 核心文件详细说明

### 1. 核心协议文件 (`ascend/core/protocols.py`)

```python
"""
ASCEND核心协议定义
基于Python Protocol的完全抽象接口设计
"""

from typing import Protocol, Any, Dict, List, Tuple, Optional
from typing_extensions import TypeAlias

# 基础类型定义
State: TypeAlias = Dict[str, Any]
Action: TypeAlias = Any
Reward: TypeAlias = float
Experience: TypeAlias = Dict[str, Any]

class IAgent(Protocol):
    """智能体协议"""
    def act(self, state: State) -> Action: ...
    def learn(self, experiences: List[Experience]) -> Dict[str, Any]: ...
    def save(self, path: str) -> None: ...
    def load(self, path: str) -> None: ...

# 其他协议定义...
```

### 2. 配置解析器 (`ascend/config/parser.py`)

```python
"""
配置解析器实现
支持YAML、JSON格式，环境变量解析，配置合并
"""

import yaml
import json
import os
from typing import Dict, Any
from pathlib import Path

class ConfigParser:
    def __init__(self):
        self.supported_formats = {'.yaml', '.yml', '.json'}
    
    def load(self, config_path: str) -> Dict[str, Any]:
        """加载并解析配置文件"""
        path = Path(config_path)
        if not path.suffix in self.supported_formats:
            raise ValueError(f"Unsupported config format: {path.suffix}")
        
        with open(path, 'r', encoding='utf-8') as f:
            if path.suffix in {'.yaml', '.yml'}:
                config = yaml.safe_load(f)
            else:
                config = json.load(f)
        
        return self._resolve_env_vars(config)
```

### 3. 插件注册表 (`ascend/plugins/registry.py`)

```python
"""
插件注册表实现
管理插件的注册、发现和生命周期
"""

from typing import Dict, List, Optional
from ascend.core.protocols import IPlugin

class PluginRegistry:
    def __init__(self):
        self._plugins: Dict[str, IPlugin] = {}
        self._plugin_metadata: Dict[str, Dict] = {}
    
    def register(self, plugin: IPlugin) -> None:
        """注册插件"""
        plugin_name = plugin.get_name()
        if plugin_name in self._plugins:
            raise ValueError(f"Plugin {plugin_name} already registered")
        
        self._plugins[plugin_name] = plugin
        self._plugin_metadata[plugin_name] = plugin.get_metadata()
```

### 4. 项目配置文件 (`pyproject.toml`)

```toml
[project]
name = "ascend-framework"
version = "0.1.0"
description = "Agent-Native System with Cognitive Embedding for Decision-Making"
readme = "README.md"
requires-python = ">=3.9"
license = {file = "LICENSE"}
authors = [
    {name = "ASCEND Team", email = "contact@ascend.ai"}
]

dependencies = [
    "pyyaml>=6.0",
    "typing-extensions>=4.0",
    "importlib-metadata>=4.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "isort>=5.0",
    "mypy>=1.0",
]
llm = [
    "openai>=1.0",
    "transformers>=4.30",
]
rl = [
    "stable-baselines3>=2.0",
    "gymnasium>=0.28",
]

[project.entry-points."ascend.plugins"]
llm_openai = "ascend_llm_openai.plugin:OpenAIPlugin"
rl_sb3 = "ascend_rl_sb3.plugin:SB3Plugin"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=ascend --cov-report=html"

[tool.black]
line-length = 88
target-version = ['py39']
```

### 5. 基础运行器 (`ascend/runners/base_runner.py`)

```python
"""
基础运行器抽象类
提供训练、评估、部署的统一接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from ascend.core.protocols import IAgent, IEnvironment

class BaseRunner(ABC):
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agent: Optional[IAgent] = None
        self.env: Optional[IEnvironment] = None
    
    @abstractmethod
    def setup(self) -> None:
        """初始化运行环境"""
        pass
    
    @abstractmethod
    def run(self) -> Dict[str, Any]:
        """执行运行逻辑"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """清理资源"""
        pass
```

## 开发环境设置

### 开发依赖安装

```bash
# 安装基础框架
pip install -e .

# 安装开发依赖
pip install -e ".[dev]"

# 安装所有可选依赖
pip install -e ".[dev,llm,rl]"
```

### 测试运行

```bash
# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 带覆盖率测试
pytest --cov=ascend tests/
```

### 代码质量检查

```bash
# 代码格式化
black ascend/ tests/ examples/

# 导入排序
isort ascend/ tests/ examples/

# 类型检查
mypy ascend/
```

这个项目结构设计确保了框架的模块化、可扩展性和易维护性，同时提供了完整的开发工具链和文档支持。