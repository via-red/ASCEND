"""示例配置文件"""

config = {
    "version": "1.0.0",
    "framework": "ascend",
    
    "agent": {
        "type": "trading_agent",
        "config": {
            "learning_rate": 0.0001,
            "batch_size": 128,
            "memory_size": 10000
        },
        "cognition": {
            "type": "llm",
            "model": "gpt-4",
            "config": {
                "temperature": 0.7,
                "max_tokens": 1000
            }
        },
        "perception": {
            "feature_extractors": [
                {
                    "name": "market_sentiment",
                    "type": "sentiment_analyzer",
                    "config": {
                        "lookback_window": 20
                    }
                },
                {
                    "name": "technical",
                    "type": "technical_indicator",
                    "config": {
                        "indicators": ["MA", "RSI", "MACD"]
                    }
                }
            ]
        },
        "safety_guards": [
            {
                "name": "risk_manager",
                "type": "dynamic_risk_manager",
                "config": {
                    "risk_limits": {
                        "max_position_size": 0.2,
                        "max_drawdown": 0.1,
                        "var_limit": 0.05
                    }
                }
            }
        ]
    },
    
    "environment": {
        "type": "market_env",
        "config": {
            "data_source": "yahoo_finance",
            "symbols": ["AAPL", "GOOGL", "MSFT"],
            "timeframe": "1d",
            "start_date": "2020-01-01",
            "end_date": "2023-12-31"
        }
    },
    
    "training": {
        "total_timesteps": 1000000,
        "eval_freq": 10000,
        "save_freq": 50000
    },
    
    "plugins": [
        "ascend_market_data",
        "ascend_trading",
        "ascend_risk_management"
    ]
}