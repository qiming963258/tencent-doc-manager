#!/usr/bin/env python3
"""
标准19列配置文件
根据实际综合打分文件定义的固定列名
这些列名必须在所有综合打分文件和UI中使用
"""

# 标准19列名称（绝对固定，不可更改，按照实际文件顺序）
STANDARD_COLUMNS = [
    "序号",              # 列0
    "项目类型",          # 列1
    "来源",              # 列2
    "任务发起时间",      # 列3
    "目标对齐",          # 列4
    "关键KR对齐",        # 列5
    "具体计划内容",      # 列6
    "邓总指导登记",      # 列7
    "负责人",            # 列8
    "协助人",            # 列9
    "监督人",            # 列10
    "重要程度",          # 列11
    "预计完成时间",      # 列12
    "完成进度",          # 列13
    "完成链接",          # 列14
    "经理分析复盘",      # 列15
    "最新复盘时间",      # 列16
    "对上汇报",          # 列17
    "应用情况"           # 列18
]

# 列的英文标识（用于代码中的键名）
COLUMN_IDS = [
    "serial_no",
    "project_type",
    "source",
    "task_start_time",
    "target_alignment",
    "key_kr_alignment",
    "specific_plan_content",
    "ceo_guidance_register",
    "owner",
    "assistant",
    "supervisor",
    "importance_level",
    "expected_completion_time",
    "completion_progress",
    "completion_link",
    "manager_analysis_review",
    "latest_review_time",
    "upward_report",
    "application_status"
]

# 列的数据类型（用于验证）
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

# 列的显示宽度建议（像素）
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

def get_standard_columns():
    """获取标准列名列表"""
    return STANDARD_COLUMNS.copy()

def validate_columns(columns):
    """
    验证提供的列名是否与标准列名完全一致
    返回：(是否有效, 错误信息列表)
    """
    errors = []

    if not isinstance(columns, list):
        return False, ["列名必须是列表类型"]

    if len(columns) != 19:
        errors.append(f"列数不正确：期望19列，实际{len(columns)}列")

    # 逐个比较列名
    for i, (standard, actual) in enumerate(zip(STANDARD_COLUMNS, columns)):
        if standard != actual:
            errors.append(f"列{i}: 期望'{standard}'，实际'{actual}'")

    return len(errors) == 0, errors

def get_column_index(column_name):
    """根据列名获取列索引"""
    try:
        return STANDARD_COLUMNS.index(column_name)
    except ValueError:
        return -1

def get_column_by_index(index):
    """根据索引获取列名"""
    if 0 <= index < 19:
        return STANDARD_COLUMNS[index]
    return None

if __name__ == "__main__":
    # 测试
    print("📋 标准19列定义")
    print("=" * 60)
    for i, col in enumerate(STANDARD_COLUMNS):
        print(f"{i:2d}. {col:15s} ({COLUMN_IDS[i]:20s}) - {COLUMN_WIDTHS[i]:3d}px")

    print("\n✅ 标准列配置已定义")