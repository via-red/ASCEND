"""
ASCEND核心模块单元测试
测试核心协议、类型和异常类的功能
"""

import pytest
from typing import Dict, Any, List

from ascend.core.protocols import IAgent, IEnvironment, Experience
from ascend.core.types import State, Action, Reward, TrainingConfig, PluginMetadata
from ascend.core.exceptions import AscendError, ConfigError, PluginError


class TestCoreProtocols:
    """测试核心协议"""
    
    def test_protocol_definitions(self):
        """测试协议定义"""
        # 检查协议是否存在
        assert hasattr(IAgent, '__protocol__')
        assert hasattr(IEnvironment, '__protocol__')
        
        # 检查协议方法
        assert hasattr(IAgent, 'act')
        assert hasattr(IAgent, 'learn')
        assert hasattr(IEnvironment, 'reset')
        assert hasattr(IEnvironment, 'step')
    
    def test_experience_dataclass(self):
        """测试Experience数据类"""
        # 创建Experience实例
        state = {"observation": [1, 2, 3]}
        action = 1
        reward = 1.0
        next_state = {"observation": [1, 2, 4]}
        done = False
        
        exp = Experience(
            state=state,
            action=action,
            reward=reward,
            next_state=next_state,
            done=done
        )
        
        # 验证属性
        assert exp.state == state
        assert exp.action == action
        assert exp.reward == reward
        assert exp.next_state == next_state
        assert exp.done == done
        assert exp.info is None
        
        # 测试to_dict方法
        exp_dict = exp.to_dict()
        assert exp_dict['state'] == state
        assert exp_dict['action'] == action
        assert exp_dict['reward'] == reward
        assert exp_dict['next_state'] == next_state
        assert exp_dict['done'] == done
        
        # 测试from_dict方法
        exp_from_dict = Experience.from_dict(exp_dict)
        assert exp_from_dict.state == state
        assert exp_from_dict.action == action
        assert exp_from_dict.reward == reward
        assert exp_from_dict.next_state == next_state
        assert exp_from_dict.done == done


class TestCoreTypes:
    """测试核心类型"""
    
    def test_type_aliases(self):
        """测试类型别名"""
        # 测试State类型
        state: State = {"obs": [1, 2, 3], "info": "test"}
        assert isinstance(state, dict)
        
        # 测试Action类型
        action: Action = 1
        assert isinstance(action, int)
        
        action: Action = "move"
        assert isinstance(action, str)
        
        # 测试Reward类型
        reward: Reward = 1.0
        assert isinstance(reward, float)
    
    def test_training_config(self):
        """测试TrainingConfig数据类"""
        config = TrainingConfig(
            total_timesteps=100000,
            batch_size=64,
            learning_rate=0.001,
            gamma=0.99
        )
        
        assert config.total_timesteps == 100000
        assert config.batch_size == 64
        assert config.learning_rate == 0.001
        assert config.gamma == 0.99
        
        # 测试to_dict方法
        config_dict = config.to_dict()
        assert config_dict['total_timesteps'] == 100000
        assert config_dict['batch_size'] == 64
        
        # 测试from_dict方法
        config_from_dict = TrainingConfig.from_dict(config_dict)
        assert config_from_dict.total_timesteps == 100000
        assert config_from_dict.batch_size == 64
    
    def test_plugin_metadata(self):
        """测试PluginMetadata数据类"""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="Test plugin",
            author="Test Author",
            license="MIT",
            requires=["plugin_a", "plugin_b"],
            provides=["agent", "environment"],
            compatible_with=["0.1.0", "0.2.0"]
        )
        
        assert metadata.name == "test_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.description == "Test plugin"
        assert metadata.author == "Test Author"
        assert metadata.license == "MIT"
        assert metadata.requires == ["plugin_a", "plugin_b"]
        assert metadata.provides == ["agent", "environment"]
        assert metadata.compatible_with == ["0.1.0", "0.2.0"]
        
        # 测试to_dict方法
        metadata_dict = metadata.to_dict()
        assert metadata_dict['name'] == "test_plugin"
        assert metadata_dict['version'] == "1.0.0"
        assert metadata_dict['requires'] == ["plugin_a", "plugin_b"]


class TestCoreExceptions:
    """测试核心异常"""
    
    def test_ascend_error(self):
        """测试基础异常"""
        error = AscendError("Test error", "TEST_CODE")
        assert str(error) == "[TEST_CODE] Test error"
        assert error.code == "TEST_CODE"
        
        error = AscendError("Test error")
        assert str(error) == "Test error"
        assert error.code is None
    
    def test_config_error(self):
        """测试配置异常"""
        error = ConfigError("Config error", "config.yaml")
        assert "config.yaml" in str(error)
        assert error.config_path == "config.yaml"
        assert error.code == "CONFIG_ERROR"
    
    def test_plugin_error(self):
        """测试插件异常"""
        error = PluginError("Plugin error", "test_plugin")
        assert "test_plugin" in str(error)
        assert error.plugin_name == "test_plugin"
        assert error.code == "PLUGIN_ERROR"


class TestTypeCompatibility:
    """测试类型兼容性"""
    
    def test_state_compatibility(self):
        """测试State类型兼容性"""
        # 各种合法的State表示
        valid_states = [
            {"observation": [1, 2, 3]},
            {"sensor_data": {"temp": 25.0, "pressure": 1013.25}},
            {"image": "base64_encoded_data", "metadata": {"width": 128, "height": 128}},
            {"text": "Hello world", "embeddings": [0.1, 0.2, 0.3]},
            {}  # 空状态也是合法的
        ]
        
        for state in valid_states:
            typed_state: State = state
            assert isinstance(typed_state, dict)
    
    def test_action_compatibility(self):
        """测试Action类型兼容性"""
        # 各种合法的Action表示
        valid_actions = [
            1,            # 离散动作
            "move_left",  # 字符串动作
            [0.5, 0.3],   # 连续动作向量
            {"type": "attack", "target": "enemy"},  # 结构化动作
            None          # 空动作（在某些情况下）
        ]
        
        for action in valid_actions:
            if action is not None:  # 跳过None，因为某些协议可能不允许
                typed_action: Action = action
                # 只要能够赋值就是兼容的


if __name__ == "__main__":
    pytest.main([__file__, "-v"])