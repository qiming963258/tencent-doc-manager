#!/usr/bin/env python3
"""
标准19列配置文件 - 向后兼容适配器
为了保持向后兼容，此文件现在从配置中心导入配置

更新：2025-09-17 - 迁移到配置中心架构
所有配置现在从 production.config 模块统一管理
"""

# 从配置中心导入所有配置
from production.config import (
    STANDARD_COLUMNS,
    COLUMN_IDS,
    COLUMN_TYPES,
    COLUMN_WIDTHS,
    L1_COLUMNS,  # 高风险列
    L2_COLUMNS,  # 中风险列
    L3_COLUMNS,  # 低风险列
    get_column_index,
    get_column_by_index,
    normalize_column_name,
    get_column_risk_level,
    get_column_weight
)

# 导出原有的常量（向后兼容）
# 这些是只读引用，指向配置中心的数据
# 所有常量已通过import语句从配置中心导入

# 向后兼容函数（保留原有接口）
def get_standard_columns():
    """获取标准列名列表"""
    return STANDARD_COLUMNS.copy()

def validate_columns(columns):
    """
    验证提供的列名是否与标准列名完全一致
    返回：(是否有效, 错误信息列表)
    """
    from production.config import get_config_center
    return get_config_center().validate_columns(columns)

if __name__ == "__main__":
    # 测试
    print("📋 标准19列定义")
    print("=" * 60)
    for i, col in enumerate(STANDARD_COLUMNS):
        print(f"{i:2d}. {col:15s} ({COLUMN_IDS[i]:20s}) - {COLUMN_WIDTHS[i]:3d}px")

    print("\n✅ 标准列配置已定义")