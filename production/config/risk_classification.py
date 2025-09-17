#!/usr/bin/env python3
"""
风险分级配置 - L1/L2/L3列分类定义
定义各列的风险等级和分类
创建日期：2025-09-17

基于《06-详细分表打分方法规范》
"""

# =============================================================================
# L1级列 - 高风险列（7列）
# 这些列的变更需要高度关注，对业务影响重大
# =============================================================================

L1_COLUMNS = [
    "来源",              # 任务来源变更影响重大
    "任务发起时间",      # 时间线变更需要关注
    "目标对齐",          # 目标变更是重要事项
    "关键KR对齐",        # KR对齐直接影响绩效
    "重要程度",          # 优先级变更需要评估
    "预计完成时间",      # 交付时间变更需要关注
    "完成进度"           # 进度变更直接反映执行状况
]

# =============================================================================
# L2级列 - 中风险列（6列）
# 这些列的变更需要适度关注，对执行有一定影响
# =============================================================================

L2_COLUMNS = [
    "项目类型",          # 类型变更影响资源分配
    "具体计划内容",      # 内容变更影响执行方案
    "邓总指导登记",      # 领导指导需要重视
    "负责人",            # 负责人变更影响执行
    "协助人",            # 协助人变更影响协作
    "监督人"             # 监督人变更影响管控
]

# =============================================================================
# L3级列 - 低风险列（6列）
# 这些列的变更影响较小，主要是参考性信息
# =============================================================================

L3_COLUMNS = [
    "序号",              # 仅为标识，无实质影响
    "完成链接",          # 参考性信息
    "经理分析复盘",      # 事后分析，参考价值
    "最新复盘时间",      # 时间记录，参考信息
    "对上汇报",          # 汇报记录，参考信息
    "应用情况"           # 应用记录，参考信息
]

# =============================================================================
# 风险等级定义
# =============================================================================

RISK_LEVELS = {
    "L1": {
        "name": "高风险",
        "base_score": 0.8,     # L1基础分
        "min_score": 0.8,       # L1最低分（强制阈值）
        "color": "#FF4444",     # 红色
        "description": "关键业务列，变更需高度关注"
    },
    "L2": {
        "name": "中风险",
        "base_score": 0.5,     # L2基础分
        "min_score": 0.6,       # L2最低分（强制阈值）
        "color": "#FFB144",     # 橙色
        "description": "重要执行列，变更需适度关注"
    },
    "L3": {
        "name": "低风险",
        "base_score": 0.2,     # L3基础分
        "min_score": 0.0,       # L3无最低分要求
        "color": "#44FF44",     # 绿色
        "description": "参考信息列，变更影响较小"
    }
}

# =============================================================================
# 辅助函数
# =============================================================================

def get_column_risk_level(column_name: str) -> str:
    """
    获取列的风险级别
    返回: 'L1', 'L2', 'L3' 或 None
    """
    if column_name in L1_COLUMNS:
        return "L1"
    elif column_name in L2_COLUMNS:
        return "L2"
    elif column_name in L3_COLUMNS:
        return "L3"
    else:
        # 未知列默认为L3
        return "L3"


def get_risk_info(risk_level: str) -> dict:
    """获取风险等级的详细信息"""
    return RISK_LEVELS.get(risk_level, RISK_LEVELS["L3"])


def get_base_score(column_name: str) -> float:
    """根据列名获取基础分"""
    risk_level = get_column_risk_level(column_name)
    risk_info = get_risk_info(risk_level)
    return risk_info["base_score"]


def validate_risk_classification() -> tuple[bool, list]:
    """
    验证风险分类的完整性和正确性
    返回: (是否有效, 错误信息列表)
    """
    from .column_definitions import STANDARD_COLUMNS

    errors = []

    # 1. 检查列数量
    total_classified = len(L1_COLUMNS) + len(L2_COLUMNS) + len(L3_COLUMNS)
    if total_classified != 19:
        errors.append(f"分类列总数不正确：期望19列，实际{total_classified}列")

    # 2. 检查是否有重复
    l1_set = set(L1_COLUMNS)
    l2_set = set(L2_COLUMNS)
    l3_set = set(L3_COLUMNS)

    if l1_set & l2_set:
        errors.append(f"L1和L2有重复列: {l1_set & l2_set}")
    if l2_set & l3_set:
        errors.append(f"L2和L3有重复列: {l2_set & l3_set}")
    if l1_set & l3_set:
        errors.append(f"L1和L3有重复列: {l1_set & l3_set}")

    # 3. 检查是否都在标准列中
    all_classified = l1_set | l2_set | l3_set
    standard_set = set(STANDARD_COLUMNS)

    missing = standard_set - all_classified
    if missing:
        errors.append(f"以下标准列未分类: {missing}")

    extra = all_classified - standard_set
    if extra:
        errors.append(f"以下列不在标准列中: {extra}")

    return len(errors) == 0, errors


if __name__ == "__main__":
    # 测试
    print("📊 风险分级配置")
    print("=" * 60)

    print(f"\n🔴 L1级列（高风险，{len(L1_COLUMNS)}列）:")
    for col in L1_COLUMNS:
        print(f"  - {col}")

    print(f"\n🟠 L2级列（中风险，{len(L2_COLUMNS)}列）:")
    for col in L2_COLUMNS:
        print(f"  - {col}")

    print(f"\n🟢 L3级列（低风险，{len(L3_COLUMNS)}列）:")
    for col in L3_COLUMNS:
        print(f"  - {col}")

    print("\n🔍 验证风险分类...")
    valid, errors = validate_risk_classification()
    if valid:
        print("✅ 风险分类验证通过")
    else:
        print("❌ 风险分类验证失败:")
        for error in errors:
            print(f"  - {error}")

    print(f"\n📈 统计:")
    print(f"  总列数: {len(L1_COLUMNS) + len(L2_COLUMNS) + len(L3_COLUMNS)}")
    print(f"  L1列数: {len(L1_COLUMNS)}")
    print(f"  L2列数: {len(L2_COLUMNS)}")
    print(f"  L3列数: {len(L3_COLUMNS)}")