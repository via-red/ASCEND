# ASCEND Project Configuration Files

## 项目基础配置文件

### 1. pyproject.toml (现代Python项目配置)

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
    "pydantic>=2.0",
    "loguru>=0.7",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "isort>=5.0",
    "mypy>=1.0",
    "ruff>=0.1",
]
llm = [
    "openai>=1.0",
    "transformers>=4.30",
    "sentencepiece>=0.1",
    "tokenizers>=0.13",
]
rl = [
    "stable-baselines3>=2.0",
    "gymnasium>=0.28",
    "torch>=2.0",
]
monitoring = [
    "tensorboard>=2.0",
    "wandb>=0.15",
]

[project.entry-points."ascend.plugins"]
llm_openai = "ascend_plugins.llm_openai:OpenAIPlugin"
rl_sb3 = "ascend_plugins.rl_sb3:SB3Plugin"
env_gym = "ascend_plugins.env_gym:GymPlugin"
monitor_tb = "ascend_plugins.monitor_tb:TensorBoardPlugin"

[project.urls]
Homepage = "https://github.com/ascend-ai/ascend"
Documentation = "https://ascend-ai.github.io/ascend"
Repository = "https://github.com/ascend-ai/ascend"
Issues = "https://github.com/ascend-ai/ascend/issues"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=ascend --cov-report=html -x"
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"

[tool.black]
line-length = 88
target-version = ['py39']
include = '\.pyi?$'
exclude = '''
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
line_length = 88

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true

[tool.ruff]
line-length = 88
select = [
    "E", "F", "W",  # pycodestyle
    "I",            # isort
    "B",            # flake8-bugbear
    "C",            # flake8-comprehensions
    "UP",           # pyupgrade
]
ignore = ["E501"]
```

### 2. requirements-dev.txt (开发依赖)

```
# 开发工具
black==23.7.0
isort==5.12.0
mypy==1.5.0
ruff==0.0.287
pytest==7.4.0
pytest-cov==4.1.0
pytest-mock==3.11.1

# 文档生成
sphinx==7.2.6
sphinx-rtd-theme==1.3.0
myst-parser==2.0.0

# 其他开发工具
pre-commit==3.3.3
tox==4.6.4
ipython==8.14.0
jupyter==1.0.0
```

### 3. 基础配置模板 (configs/base.yaml)

```yaml
# ASCEND基础配置模板
version: "1.0.0"
framework: "ascend"

# 智能体配置
agent:
  type: "ppo_agent"
  config:
    learning_rate: 0.0003
    batch_size: 64
    n_steps: 2048
    ent_coef: 0.01
    vf_coef: 0.5
    max_grad_norm: 0.5
    clip_range: 0.2
    clip_range_vf: null
    normalize_advantage: true

# 环境配置
environment:
  type: "gym_env"
  config:
    env_id: "CartPole-v1"
    max_episode_steps: 500
    render_mode: "rgb_array"
    auto_reset: true

# 训练配置
training:
  total_timesteps: 100000
  learning_starts: 10000
  train_freq: 1
  gradient_steps: 1
  buffer_size: 100000
  learning_rate: 0.0003
  batch_size: 64
  tau: 1.0
  gamma: 0.99
  target_update_interval: 1

# 评估配置
evaluation:
  eval_freq: 10000
  n_eval_episodes: 5
  deterministic: true
  render: false
  warn: true

# 模型配置
models:
  policy:
    type: "mlp_policy"
    config:
      net_arch:
        pi: [64, 64]
        vf: [64, 64]
      activation_fn: "relu"
      ortho_init: true
      log_std_init: 0.0

# 奖励配置
rewards:
  main:
    type: "sparse_reward"
    config:
      goal_reward: 1.0
      step_penalty: -0.01
      failure_penalty: -1.0

# 特征提取配置
features:
  state_extractor:
    type: "flatten_extractor"
    config:
      normalize: true
      clip_range: 10.0

# 监控配置
monitoring:
  tensorboard:
    enabled: true
    log_dir: "./logs/tensorboard"
    update_freq: 1000
  
  console:
    enabled: true
    progress_bar: true
    verbose: 1

# 保存配置
checkpoint:
  save_freq: 10000
  save_path: "./checkpoints"
  keep_last: 5
  save_replay_buffer: false
  save_vecnormalize: false

# 插件配置
plugins:
  - "ascend_rl_sb3"
  - "ascend_env_gym"
  - "ascend_monitor_tb"

# 环境变量
env_vars:
  OPENAI_API_KEY: optional
  WANDB_API_KEY: optional
  TENSORBOARD_LOGDIR: optional
```

### 4. 医疗领域配置模板 (configs/medical.yaml)

```yaml
# 医疗智能体配置模板
_extends: "base.yaml"

agent:
  type: "medical_agent"
  config:
    learning_rate: 0.0001
    patient_safety_weight: 0.8
    treatment_efficacy_weight: 0.6
    cost_efficiency_weight: 0.3
    risk_tolerance: 0.1

environment:
  type: "medical_simulator"
  config:
    disease_types: ["cancer", "diabetes", "heart_disease"]
    patient_demographics: true
    lab_results: true
    imaging_data: true
    max_patients: 1000
    difficulty: "medium"

models:
  llm:
    type: "medical_llm"
    config:
      model_name: "clinical-bert"
      max_tokens: 512
      temperature: 0.3
  
  imaging:
    type: "densenet"
    config:
      pretrained: true
      num_classes: 10
  
  lab_analysis:
    type: "random_forest"
    config:
      n_estimators: 100
      max_depth: 10

rewards:
  main:
    type: "composite_reward"
    components:
      - type: "patient_outcome"
        weight: 0.5
        config:
          recovery_bonus: 2.0
          complication_penalty: -1.0
      
      - type: "treatment_safety"
        weight: 0.3
        config:
          safe_treatment_bonus: 0.5
          risky_treatment_penalty: -2.0
      
      - type: "cost_efficiency"
        weight: 0.2
        config:
          cost_per_treatment: -0.1
          efficient_bonus: 0.3

plugins:
  - "ascend_llm_medical"
  - "ascend_imaging_analysis"
  - "ascend_lab_processor"
```

### 5. GitHub工作流配置 (.github/workflows/ci.yml)

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Run tests
      run: |
        pytest tests/ --cov=ascend --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  lint:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.11"
    
    - name: Install linting tools
      run: |
        pip install black isort ruff mypy
    
    - name: Check formatting with black
      run: |
        black --check ascend/ tests/ examples/
    
    - name: Check import sorting with isort
      run: |
        isort --check-only ascend/ tests/ examples/
    
    - name: Check code quality with ruff
      run: |
        ruff check ascend/ tests/ examples/
    
    - name: Check types with mypy
      run: |
        mypy ascend/
```

### 6. 预提交钩子配置 (.pre-commit-config.yaml)

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        name: isort (python)

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.0.287
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.0
    hooks:
      - id: mypy
        additional_dependencies: [types-PyYAML, types-requests]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

这些配置文件为ASCEND框架提供了完整的基础设施支持，包括项目配置、依赖管理、CI/CD流程和代码质量保证。