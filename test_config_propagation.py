#!/usr/bin/env python3
"""
测试配置更改传播
验证配置修改后是否能正确传播到所有相关模块
"""

import sys
import json
import time
from pathlib import Path

sys.path.insert(0, '/root/projects/tencent-doc-manager')

def test_config_propagation():
    """测试配置更改传播"""
    print("\n" + "="*60)
    print("🔄 测试配置更改传播机制")
    print("="*60)

    # 1. 获取当前配置
    print("\n📌 步骤1: 获取当前配置")
    from production.config import get_config_center, STANDARD_COLUMNS

    config = get_config_center()
    original_columns = config.get_standard_columns()
    print(f"  当前列14: {original_columns[14]}")
    print(f"  当前列15: {original_columns[15]}")
    print(f"  当前列16: {original_columns[16]}")

    # 2. 通过不同方式导入，验证是否一致
    print("\n📌 步骤2: 验证不同导入方式的一致性")

    # 方式1：从配置中心导入
    from production.config import STANDARD_COLUMNS as CONFIG_COLUMNS

    # 方式2：从适配器导入
    from standard_columns_config import STANDARD_COLUMNS as ADAPTER_COLUMNS

    # 方式3：从具体模块导入
    from production.config.column_definitions import STANDARD_COLUMNS as DIRECT_COLUMNS

    if CONFIG_COLUMNS == ADAPTER_COLUMNS == DIRECT_COLUMNS:
        print("  ✅ 所有导入方式返回相同配置")
    else:
        print("  ❌ 不同导入方式返回不同配置")
        print(f"    CONFIG: {CONFIG_COLUMNS[14:17]}")
        print(f"    ADAPTER: {ADAPTER_COLUMNS[14:17]}")
        print(f"    DIRECT: {DIRECT_COLUMNS[14:17]}")

    # 3. 测试单例模式
    print("\n📌 步骤3: 验证单例模式")
    config1 = get_config_center()
    config2 = get_config_center()

    if config1 is config2:
        print("  ✅ 配置中心是单例（同一实例）")
    else:
        print("  ❌ 配置中心不是单例（不同实例）")

    # 4. 测试缓存机制
    print("\n📌 步骤4: 测试配置缓存机制")

    # 清空缓存
    if hasattr(config, '_config_cache'):
        original_cache = config._config_cache.copy()
        config._config_cache.clear()
        print(f"  清空缓存，原有{len(original_cache)}项")

        # 重新获取配置
        new_columns = config.get_standard_columns()

        # 检查缓存是否重建
        if hasattr(config, '_config_cache') and config._config_cache:
            print(f"  ✅ 缓存已重建，包含{len(config._config_cache)}项")

        # 恢复缓存
        config._config_cache = original_cache
    else:
        print("  ⚠️ 配置中心没有缓存机制")

    # 5. 测试别名转换传播
    print("\n📌 步骤5: 测试列名别名转换传播")
    from production.config import normalize_column_name

    test_cases = [
        ("形成计划清单", "完成链接"),
        ("进度分析总结", "经理分析复盘"),
        ("复盘时间", "最新复盘时间")
    ]

    all_correct = True
    for old_name, expected in test_cases:
        actual = normalize_column_name(old_name)
        if actual == expected:
            print(f"  ✅ '{old_name}' → '{actual}'")
        else:
            print(f"  ❌ '{old_name}' → '{actual}' (期望'{expected}')")
            all_correct = False

    # 6. 测试在实际模块中的使用
    print("\n📌 步骤6: 测试在实际模块中的配置使用")

    try:
        # 导入使用配置的模块
        from production.core_modules.comparison_to_scoring_adapter import (
            ComparisonToScoringAdapter
        )

        # 创建适配器实例
        adapter = ComparisonToScoringAdapter()

        # 检查是否使用正确的配置
        if hasattr(adapter, 'standard_columns'):
            columns = adapter.standard_columns
            print(f"  适配器列14: {columns[14] if len(columns) > 14 else 'N/A'}")
            print(f"  适配器列15: {columns[15] if len(columns) > 15 else 'N/A'}")
            print(f"  适配器列16: {columns[16] if len(columns) > 16 else 'N/A'}")

            if columns[14:17] == STANDARD_COLUMNS[14:17]:
                print("  ✅ 适配器使用正确的配置")
            else:
                print("  ❌ 适配器配置不一致")
        else:
            print("  ⚠️ 适配器未找到standard_columns属性")

    except Exception as e:
        print(f"  ❌ 无法测试适配器: {str(e)}")

    # 7. 测试热力图服务的配置
    print("\n📌 步骤7: 检查热力图服务配置状态")

    # 检查正在运行的服务
    import subprocess
    result = subprocess.run(
        ["ps", "aux"],
        capture_output=True,
        text=True
    )

    if "final_heatmap_server.py" in result.stdout:
        print("  ℹ️ 热力图服务正在运行")

        # 检查服务输出的背景任务
        try:
            from BashOutput import BashOutput
            # 这里应该检查背景任务输出，但需要知道任务ID
            print("  ⚠️ 需要重启服务以应用新配置")
        except:
            pass
    else:
        print("  ⚠️ 热力图服务未运行")

    # 8. 测试风险分级传播
    print("\n📌 步骤8: 测试风险分级配置传播")
    from production.config import L1_COLUMNS, L2_COLUMNS, L3_COLUMNS
    from standard_columns_config import (
        L1_COLUMNS as ADAPTER_L1,
        L2_COLUMNS as ADAPTER_L2,
        L3_COLUMNS as ADAPTER_L3
    )

    if L1_COLUMNS == ADAPTER_L1:
        print("  ✅ L1列分级一致")
    else:
        print("  ❌ L1列分级不一致")

    if L2_COLUMNS == ADAPTER_L2:
        print("  ✅ L2列分级一致")
    else:
        print("  ❌ L2列分级不一致")

    if L3_COLUMNS == ADAPTER_L3:
        print("  ✅ L3列分级一致")
    else:
        print("  ❌ L3列分级不一致")

    print("\n" + "="*60)
    print("✨ 配置传播测试完成")
    print("="*60)

if __name__ == "__main__":
    test_config_propagation()