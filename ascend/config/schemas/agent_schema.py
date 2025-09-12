"""配置模式定义"""

agent_schema = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "config": {
            "type": "object",
            "properties": {
                "learning_rate": {"type": "number"},
                "batch_size": {"type": "integer"},
                "memory_size": {"type": "integer"}
            }
        },
        "cognition": {
            "type": "object",
            "properties": {
                "type": {"type": "string"},
                "model": {"type": "string"},
                "config": {"type": "object"}
            }
        },
        "perception": {
            "type": "object",
            "properties": {
                "feature_extractors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "config": {"type": "object"}
                        }
                    }
                }
            }
        },
        "safety_guards": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "config": {"type": "object"}
                }
            }
        }
    },
    "required": ["type", "config"]
}