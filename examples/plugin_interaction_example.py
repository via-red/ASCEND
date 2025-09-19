#!/usr/bin/env python3
"""
ASCEND插件交互使用示例
展示新的简洁插件调用方式
"""

from ascend import Ascend

def main():
    print("🚀 ASCEND插件交互使用示例")
    print("=" * 50)
    
    # 初始化框架
    ascend = Ascend(config_path="examples/basic_usage/config.yaml")
    
    print("1. 直接调用数据插件")
    print("-" * 30)
    
    # 方式1：直接获取插件并调用start
    data_plugin = ascend.get_plugin("tushare_data")
    data_results = data_plugin.start(
        ascend,
        symbols=["000001.SZ", "600036.SH"],
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
    print(f"数据获取结果: {len(data_results)} 只股票")
    
    print("\n2. 直接调用策略插件（自动使用数据插件）")
    print("-" * 30)
    
    # 方式2：策略插件自动调用数据插件
    strategy_plugin = ascend.get_plugin("daily_kline_scoring")
    strategy_results = strategy_plugin.start(
        ascend,
        symbols=["000001.SZ", "600036.SH"],
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
    print(f"策略评分结果: {strategy_results}")
    
    print("\n3. 使用流水线执行")
    print("-" * 30)
    
    # 方式3：流水线执行
    pipeline_results = ascend.execute_pipeline(
        ["tushare_data", "daily_kline_scoring"],
        symbols=["000001.SZ", "600036.SH"],
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
    print(f"流水线执行完成: {len(pipeline_results)} 个插件")
    
    print("\n4. 启动所有插件")
    print("-" * 30)
    
    # 方式4：启动所有插件
    all_results = ascend.start_all_plugins(
        symbols=["000001.SZ"],
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
    print(f"所有插件启动完成: {len(all_results)} 个插件")
    
    print("\n5. 停止所有插件")
    print("-" * 30)
    
    # 停止所有插件
    ascend.stop_all_plugins()
    print("所有插件已停止")
    
    print("\n" + "=" * 50)
    print("🎉 插件交互示例运行完成！")

if __name__ == "__main__":
    main()