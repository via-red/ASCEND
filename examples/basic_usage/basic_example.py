#!/usr/bin/env python3
"""
ASCEND 框架基础用法示例

展示了框架的核心功能，包括：
1. 创建和配置环境
2. 创建和训练智能体
3. 使用插件
4. 配置管理
5. 运行仿真
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

import logging
from ascend.config.loader import ConfigLoader
from ascend.plugins.manager import PluginManager
from ascend.core.types import State, Action

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('training.log')
    ]
)

logger = logging.getLogger(__name__)

def setup():
    """初始化框架组件"""
    # 加载配置
    config_loader = ConfigLoader([str(Path(__file__).parent)])
    config = config_loader.load_config("config.yaml")
    logger.info("Loaded configuration")

    # 初始化插件管理器
    plugin_manager = PluginManager()
    discovered = plugin_manager.discover_plugins()
    logger.info(f"Discovered plugins: {list(discovered.keys())}")

    # 加载和初始化 SB3 插件
    sb3_plugin = plugin_manager.load_plugin("rl_sb3")
    plugin_manager.initialize_plugin("rl_sb3", config.get("rl_sb3", {}))
    logger.info("Initialized SB3 plugin")

    return config, plugin_manager, sb3_plugin

class SimpleEnvironment:
    """简单的强化学习环境
    
    这是一个一维空间中的目标追踪问题。智能体需要通过增加或减少
    状态值来接近目标值。
    
    状态空间: [0, 100]
    动作空间: {0: 减少, 1: 增加}
    奖励: 与目标值的负距离
    """
    
    def __init__(self, config: dict):
        """初始化环境
        
        Args:
            config: 环境配置
        """
        self.max_steps = config.get("max_steps", 100)
        self.target_value = config.get("target_value", 75)
        self.reset()
        
        # 定义动作空间和观察空间
        import gymnasium as gym
        self.action_space = gym.spaces.Discrete(2)  # 0: 减少, 1: 增加
        self.observation_space = gym.spaces.Box(low=0, high=100, shape=(1,), dtype=float)
        
        logger.info(
            f"Initialized environment with target={self.target_value}, "
            f"max_steps={self.max_steps}"
        )
    
    def reset(self):
        """重置环境
        
        Returns:
            初始状态
        """
        self.state = 50  # 从中间开始
        self.current_step = 0
        return [self.state]
    
    def step(self, action):
        """执行一步交互
        
        Args:
            action: 动作(0或1)
            
        Returns:
            (next_state, reward, done, info) 元组
        """
        self.current_step += 1
        
        # 执行动作
        if action == 0:
            self.state = max(0, self.state - 1)
        else:
            self.state = min(100, self.state + 1)
        
        # 计算奖励：越接近目标值越好
        reward = -abs(self.target_value - self.state) / self.target_value
        
        # 检查是否结束
        done = self.current_step >= self.max_steps
        
        return [self.state], reward, done, {}

def train(env, agent, config: dict):
    """训练智能体
    
    Args:
        env: 环境实例
        agent: 智能体实例
        config: 训练配置
    """
    num_episodes = config.get("num_episodes", 1000)
    log_interval = config.get("log_interval", 100)
    
    logger.info(f"Starting training for {num_episodes} episodes")
    
    for episode in range(num_episodes):
        state = env.reset()
        total_reward = 0
        done = False
        
        while not done:
            # 选择动作
            action = agent.act(state)
            
            # 执行动作
            next_state, reward, done, info = env.step(action)
            
            # 累积奖励
            total_reward += reward
            
            # 更新状态
            state = next_state
        
        # 打印进度
        if (episode + 1) % log_interval == 0:
            logger.info(
                f"Episode {episode + 1}/{num_episodes} - "
                f"Total Reward: {total_reward:.2f}"
            )

def evaluate(env, agent, config: dict):
    """评估智能体性能
    
    Args:
        env: 环境实例
        agent: 智能体实例
        config: 评估配置
    """
    num_episodes = config.get("eval_episodes", 10)
    logger.info(f"Starting evaluation for {num_episodes} episodes")
    
    total_rewards = []
    
    for episode in range(num_episodes):
        state = env.reset()
        total_reward = 0
        done = False
        
        while not done:
            action = agent.act(state)
            next_state, reward, done, info = env.step(action)
            total_reward += reward
            state = next_state
        
        total_rewards.append(total_reward)
        logger.info(
            f"Evaluation Episode {episode + 1} - Total Reward: {total_reward:.2f}"
        )
    
    avg_reward = sum(total_rewards) / len(total_rewards)
    logger.info(f"Average Reward: {avg_reward:.2f}")
    
    return avg_reward

def main():
    """主函数"""
    try:
        # 初始化框架
        config, plugin_manager, sb3_plugin = setup()
        
        # 创建环境
        env = SimpleEnvironment(config["environment"])
        
        # 创建智能体
        agent = sb3_plugin.create_agent(env)
        logger.info("Created agent")
        
        # 训练智能体
        train(env, agent, config["training"])
        
        # 评估性能
        evaluate(env, agent, config["training"])
        
        # 保存模型
        save_path = config["training"].get("save_path", "trained_agent")
        agent.save(save_path)
        logger.info(f"Saved trained agent to {save_path}")
        
    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from ascend import (
    load_config, validate_config, create_default_config,
    load_plugins, list_loaded_plugins, list_available_plugins,
    ConfigError, ValidationError, PluginError
)

def basic_config_example():
    """基础配置操作示例"""
    print("=" * 50)
    print("ASCEND框架基础配置示例")
    print("=" * 50)
    
    try:
        # 1. 加载配置文件
        print("\n1. 加载配置文件...")
        config_path = Path(__file__).parent / "config.yaml"
        config = load_config(str(config_path))
        print(f"✓ 配置文件加载成功: {config_path}")
        print(f"  框架版本: {config.get('version')}")
        print(f"  智能体类型: {config['agent']['type']}")
        print(f"  环境类型: {config['environment']['type']}")
        
        # 2. 验证配置
        print("\n2. 验证配置...")
        is_valid = validate_config(config)
        print(f"✓ 配置验证通过: {is_valid}")
        
        # 3. 创建默认配置
        print("\n3. 创建默认配置...")
        default_config = create_default_config()
        print(f"✓ 默认配置创建成功")
        print(f"  默认智能体: {default_config['agent']['type']}")
        print(f"  默认环境: {default_config['environment']['type']}")
        
        return config
        
    except (ConfigError, ValidationError) as e:
        print(f"✗ 配置错误: {e}")
        return None
    except Exception as e:
        print(f"✗ 未知错误: {e}")
        return None

def plugin_management_example():
    """插件管理示例"""
    print("\n" + "=" * 50)
    print("插件管理示例")
    print("=" * 50)
    
    try:
        # 1. 列出可用插件
        print("\n1. 列出可用插件...")
        available_plugins = list_available_plugins()
        print(f"发现 {len(available_plugins)} 个可用插件:")
        for plugin_info in available_plugins:
            print(f"  - {plugin_info['name']}: {plugin_info['metadata']['description']}")
        
        # 2. 尝试加载插件（这里会失败，因为没有实际插件实现）
        print("\n2. 尝试加载插件...")
        print("注意: 由于没有实际插件实现，加载会失败")
        print("这只是演示框架的插件管理接口")
        
        # 模拟插件配置
        plugin_configs = {
            "ascend_rl_sb3": {"learning_rate": 0.0003},
            "ascend_env_gym": {"env_id": "CartPole-v1"}
        }
        
        try:
            plugins = load_plugins(["ascend_rl_sb3", "ascend_env_gym"], plugin_configs)
            print(f"✓ 插件加载成功: {len(plugins)} 个插件")
            
            # 3. 列出已加载插件
            loaded_plugins = list_loaded_plugins()
            print(f"已加载插件: {loaded_plugins}")
            
        except PluginError as e:
            print(f"✗ 插件加载失败（预期中）: {e}")
            print("这是正常的，因为我们还没有实现具体的插件")
        
        return True
        
    except Exception as e:
        print(f"✗ 插件管理错误: {e}")
        return False

def framework_info_example():
    """框架信息示例"""
    print("\n" + "=" * 50)
    print("框架信息示例")
    print("=" * 50)
    
    from ascend import __version__, __author__, __description__
    
    print(f"框架名称: ASCEND")
    print(f"版本: {__version__}")
    print(f"作者: {__author__}")
    print(f"描述: {__description__}")
    
    # 核心协议信息
    from ascend import (
        IAgent, IEnvironment, IPolicy, IModel,
        State, Action, Reward, Config
    )
    
    print(f"\n核心协议:")
    print(f"  - IAgent: {IAgent.__doc__}")
    print(f"  - IEnvironment: {IEnvironment.__doc__}")
    print(f"  - IPolicy: {IPolicy.__doc__}")
    print(f"  - IModel: {IModel.__doc__}")
    
    print(f"\n核心类型:")
    print(f"  - State: 状态表示")
    print(f"  - Action: 动作类型") 
    print(f"  - Reward: 奖励值")
    print(f"  - Config: 配置字典")

def create_custom_plugin_example():
    """创建自定义插件示例"""
    print("\n" + "=" * 50)
    print("创建自定义插件示例")
    print("=" * 50)
    
    from ascend.plugins import BasePlugin
    from ascend.core import PluginMetadata
    
    class DemoPlugin(BasePlugin):
        """演示插件"""
        
        def __init__(self):
            super().__init__(
                name="demo_plugin",
                version="0.1.0",
                description="演示插件示例",
                author="ASCEND Team"
            )
        
        def register(self, registry):
            """注册插件组件"""
            print("✓ 演示插件注册方法被调用")
            # 这里可以注册具体的组件
        
        def _get_required_plugins(self):
            return ["ascend_rl_sb3"]  # 依赖其他插件
        
        def _get_provided_components(self):
            return ["demo_component"]  # 提供 demo_component
    
    # 创建插件实例
    plugin = DemoPlugin()
    print(f"插件名称: {plugin.get_name()}")
    print(f"插件版本: {plugin.get_version()}")
    print(f"插件描述: {plugin.description}")
    
    # 获取元数据
    metadata = plugin.get_metadata()
    print(f"依赖插件: {metadata['requires']}")
    print(f"提供组件: {metadata['provides']}")
    
    print("✓ 自定义插件创建成功")

def main():
    """主函数"""
    print("ASCEND框架基础使用示例")
    print("本示例演示框架的核心功能和接口")
    print()
    
    # 运行各个示例
    config = basic_config_example()
    if config:
        plugin_management_example()
        framework_info_example()
        create_custom_plugin_example()
        
        print("\n" + "=" * 50)
        print("示例执行完成!")
        print("=" * 50)
        print("框架核心功能演示完毕。")
        print("下一步可以:")
        print("1. 实现具体的插件")
        print("2. 创建自定义智能体和环境")
        print("3. 开始训练实验")
    else:
        print("示例执行失败，请检查配置")

if __name__ == "__main__":
    main()