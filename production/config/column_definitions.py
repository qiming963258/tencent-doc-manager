#!/usr/bin/env python3
"""
列定义配置 - 单一真相源
定义系统所有标准列及相关属性
创建日期：2025-09-17

重要：这是系统列定义的唯一权威来源
所有其他模块应该从这里导入列定义
"""

# =============================================================================
# 标准19列定义（绝对固定，不可更改）
# =============================================================================

STANDARD_COLUMNS = [
    "序号",              # 0 - L3
    "项目类型",          # 1 - L2
    "来源",              # 2 - L1
    "任务发起时间",      # 3 - L1
    "目标对齐",          # 4 - L1
    "关键KR对齐",        # 5 - L1
    "具体计划内容",      # 6 - L2
    "邓总指导登记",      # 7 - L2
    "负责人",            # 8 - L2
    "协助人",            # 9 - L2
    "监督人",            # 10 - L2
    "重要程度",          # 11 - L1
    "预计完成时间",      # 12 - L1
    "完成进度",          # 13 - L1
    "完成链接",          # 14 - L3（统一为此版本，原"形成计划清单"已废弃）
    "经理分析复盘",      # 15 - L3（统一为此版本，原"进度分析总结"已废弃）
    "最新复盘时间",      # 16 - L3（统一为此版本，原"复盘时间"已废弃）
    "对上汇报",          # 17 - L3
    "应用情况"           # 18 - L3
]

# =============================================================================
# 列的英文标识（用于代码中的键名）
# =============================================================================

COLUMN_IDS = [
    "serial_no",                # 序号
    "project_type",             # 项目类型
    "source",                   # 来源
    "task_start_time",          # 任务发起时间
    "target_alignment",         # 目标对齐
    "key_kr_alignment",         # 关键KR对齐
    "specific_plan_content",    # 具体计划内容
    "ceo_guidance_register",    # 邓总指导登记
    "owner",                    # 负责人
    "assistant",                # 协助人
    "supervisor",               # 监督人
    "importance_level",         # 重要程度
    "expected_completion_time", # 预计完成时间
    "completion_progress",      # 完成进度
    "completion_link",          # 完成链接
    "manager_analysis_review",  # 经理分析复盘
    "latest_review_time",       # 最新复盘时间
    "upward_report",           # 对上汇报
    "application_status"        # 应用情况
]

# =============================================================================
# 列的数据类型（用于验证）
# =============================================================================

COLUMN_TYPES = {
    "serial_no": "string",
    "project_type": "string",
    "source": "string",
    "task_start_time": "datetime",
    "target_alignment": "string",
    "key_kr_alignment": "string",
    "specific_plan_content": "string",
    "ceo_guidance_register": "string",
    "owner": "string",
    "assistant": "string",
    "supervisor": "string",
    "importance_level": "string",
    "expected_completion_time": "datetime",
    "completion_progress": "string",
    "completion_link": "string",
    "manager_analysis_review": "string",
    "latest_review_time": "datetime",
    "upward_report": "string",
    "application_status": "string"
}

# =============================================================================
# 列的显示宽度建议（像素）
# =============================================================================

COLUMN_WIDTHS = [
    60,   # 序号
    100,  # 项目类型
    100,  # 来源
    120,  # 任务发起时间
    100,  # 目标对齐
    110,  # 关键KR对齐
    150,  # 具体计划内容
    120,  # 邓总指导登记
    80,   # 负责人
    80,   # 协助人
    80,   # 监督人
    90,   # 重要程度
    120,  # 预计完成时间
    100,  # 完成进度
    100,  # 完成链接
    120,  # 经理分析复盘
    120,  # 最新复盘时间
    100,  # 对上汇报
    100   # 应用情况
]

# =============================================================================
# 列名别名映射（处理历史遗留问题）
# =============================================================================

COLUMN_ALIASES = {
    # 正确列名映射到自身
    "序号": "序号",
    "项目类型": "项目类型",
    "来源": "来源",
    "任务发起时间": "任务发起时间",
    "目标对齐": "目标对齐",
    "关键KR对齐": "关键KR对齐",
    "具体计划内容": "具体计划内容",
    "邓总指导登记": "邓总指导登记",
    "负责人": "负责人",
    "协助人": "协助人",
    "监督人": "监督人",
    "重要程度": "重要程度",
    "预计完成时间": "预计完成时间",
    "完成进度": "完成进度",
    "完成链接": "完成链接",
    "经理分析复盘": "经理分析复盘",
    "最新复盘时间": "最新复盘时间",
    "对上汇报": "对上汇报",
    "应用情况": "应用情况",

    # 历史别名映射
    "形成计划清单": "完成链接",        # 旧名称 -> 新名称
    "进度分析总结": "经理分析复盘",    # 旧名称 -> 新名称
    "复盘时间": "最新复盘时间",        # 旧名称 -> 新名称

    # 其他可能的别名
    "完成状态": "完成进度",
    "任务来源": "来源",
    "发起时间": "任务发起时间"
}

# =============================================================================
# 辅助函数
# =============================================================================

def get_column_index(column_name: str) -> int:
    """根据列名获取列索引"""
    # 先尝试别名映射
    actual_name = COLUMN_ALIASES.get(column_name, column_name)
    try:
        return STANDARD_COLUMNS.index(actual_name)
    except ValueError:
        return -1


def get_column_by_index(index: int) -> str:
    """根据索引获取列名"""
    if 0 <= index < 19:
        return STANDARD_COLUMNS[index]
    return None


def get_column_id(column_name: str) -> str:
    """根据列名获取英文标识"""
    index = get_column_index(column_name)
    if index >= 0:
        return COLUMN_IDS[index]
    return None


def normalize_column_name(column_name: str) -> str:
    """
    标准化列名（处理别名）
    将任何已知的别名转换为标准列名
    """
    return COLUMN_ALIASES.get(column_name, column_name)


def is_valid_column(column_name: str) -> bool:
    """检查是否为有效的列名（包括别名）"""
    normalized = normalize_column_name(column_name)
    return normalized in STANDARD_COLUMNS


if __name__ == "__main__":
    # 测试
    print("📋 标准19列定义")
    print("=" * 70)

    for i, col in enumerate(STANDARD_COLUMNS):
        print(f"{i:2d}. {col:15s} ({COLUMN_IDS[i]:25s}) - {COLUMN_WIDTHS[i]:3d}px")

    print("\n📝 别名映射:")
    print("-" * 40)
    for old, new in COLUMN_ALIASES.items():
        if old != new:
            print(f"  {old:15s} -> {new}")

    print("\n✅ 列定义配置已加载")