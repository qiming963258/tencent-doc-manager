#!/usr/bin/env python3
"""
打分参数配置 - 算法权重和参数定义
定义打分算法的所有参数配置
创建日期：2025-09-17

基于《06-详细分表打分方法规范》和《07-综合集成打分算法规范》
"""

# =============================================================================
# 列权重定义（仅L1和L2列需要特殊权重）
# =============================================================================

COLUMN_WEIGHTS = {
    # L1列权重（风险权重较高）
    "重要程度": 1.4,         # 最高权重，重要程度变更影响最大
    "任务发起时间": 1.3,     # 时间变更影响重大
    "预计完成时间": 1.3,     # 交付时间变更需重点关注
    "完成进度": 1.1,         # 进度变更直接反映执行状态
    "目标对齐": 1.0,         # 标准权重
    "关键KR对齐": 1.0,       # 标准权重
    "来源": 1.0,             # 标准权重

    # L2列权重（中等权重）
    "负责人": 1.2,           # 负责人变更影响执行
    "邓总指导登记": 1.15,    # 领导指导需要重视
    "项目类型": 1.1,         # 类型变更有一定影响
    "具体计划内容": 1.0,     # 标准权重
    "协助人": 1.0,           # 标准权重
    "监督人": 1.0,           # 标准权重

    # L3列默认权重1.0，无需显式定义
}

# =============================================================================
# 基础分配置
# =============================================================================

BASE_SCORES = {
    "L1": 0.8,  # L1级变更基础分（高）
    "L2": 0.5,  # L2级变更基础分（中）
    "L3": 0.2   # L3级变更基础分（低）
}

# =============================================================================
# 强制阈值配置（确保重要变更得分不会过低）
# =============================================================================

FORCE_THRESHOLDS = {
    "L1": 0.8,  # L1列变更最低分不低于0.8
    "L2": 0.6,  # L2列变更最低分不低于0.6
    "L3": 0.0   # L3列无最低分限制
}

# =============================================================================
# 热力图渲染参数
# =============================================================================

# IDW（反距离权重）插值参数
IDW_PARAMS = {
    "power": 2.0,           # 距离幂次（影响插值平滑度）
    "smoothing": 0.5,       # 平滑系数
    "neighbors": 8,         # 邻居点数量
    "radius": 3.0          # 影响半径
}

# 扩散算法参数
DIFFUSION_PARAMS = {
    "rate": 0.08,          # 扩散率（控制扩散速度）
    "iterations": 3,       # 迭代次数（控制扩散范围）
    "threshold": 0.01      # 扩散阈值（低于此值停止扩散）
}

# =============================================================================
# 热力图颜色映射
# =============================================================================

HEATMAP_COLOR_RANGES = [
    {"min": 0.0, "max": 0.2, "color": "#1a237e", "label": "极低风险"},   # 深蓝
    {"min": 0.2, "max": 0.4, "color": "#00acc1", "label": "低风险"},     # 青色
    {"min": 0.4, "max": 0.6, "color": "#43a047", "label": "中等风险"},   # 绿色
    {"min": 0.6, "max": 0.8, "color": "#ffb300", "label": "高风险"},     # 黄色
    {"min": 0.8, "max": 1.0, "color": "#b71c1c", "label": "极高风险"}    # 血红
]

# =============================================================================
# 打分算法参数
# =============================================================================

SCORING_ALGORITHM = {
    "version": "2.0",
    "name": "综合风险评分算法",

    # 算法组件权重
    "components": {
        "base_score": 0.4,        # 基础分权重
        "column_weight": 0.3,     # 列权重权重
        "change_magnitude": 0.2,  # 变更幅度权重
        "frequency": 0.1         # 变更频率权重
    },

    # 变更幅度计算参数
    "change_magnitude": {
        "minor": 0.2,      # 轻微变更
        "moderate": 0.5,   # 中度变更
        "major": 0.8,      # 重大变更
        "critical": 1.0    # 关键变更
    },

    # 频率影响因子
    "frequency_factor": {
        "rare": 1.0,       # 罕见（<5%行）
        "uncommon": 1.1,   # 不常见（5-20%行）
        "common": 1.2,     # 常见（20-50%行）
        "frequent": 1.3    # 频繁（>50%行）
    }
}

# =============================================================================
# 统计阈值配置
# =============================================================================

STATISTICS_THRESHOLDS = {
    "high_risk_threshold": 0.7,     # 高风险阈值
    "medium_risk_threshold": 0.4,   # 中风险阈值
    "significant_change": 0.5,      # 显著变更阈值
    "minor_change": 0.2            # 轻微变更阈值
}

# =============================================================================
# 辅助函数
# =============================================================================

def get_column_weight(column_name: str) -> float:
    """
    获取列的权重值
    未定义的列返回默认权重1.0
    """
    return COLUMN_WEIGHTS.get(column_name, 1.0)


def get_base_score_by_level(risk_level: str) -> float:
    """根据风险级别获取基础分"""
    return BASE_SCORES.get(risk_level, BASE_SCORES["L3"])


def get_force_threshold(risk_level: str) -> float:
    """获取强制阈值"""
    return FORCE_THRESHOLDS.get(risk_level, 0.0)


def calculate_weighted_score(base_score: float,
                            column_name: str,
                            risk_level: str) -> float:
    """
    计算加权后的分数

    Args:
        base_score: 基础分
        column_name: 列名
        risk_level: 风险级别

    Returns:
        加权后的分数
    """
    # 获取列权重
    weight = get_column_weight(column_name)

    # 计算加权分数
    weighted = base_score * weight

    # 应用强制阈值
    threshold = get_force_threshold(risk_level)
    return max(weighted, threshold)


def get_color_for_score(score: float) -> str:
    """根据分数获取对应的颜色"""
    for range_config in HEATMAP_COLOR_RANGES:
        if range_config["min"] <= score <= range_config["max"]:
            return range_config["color"]
    return "#1a237e"  # 默认深蓝色


def validate_parameters() -> tuple[bool, list]:
    """
    验证参数配置的合理性
    返回: (是否有效, 错误信息列表)
    """
    errors = []

    # 验证权重值范围
    for col, weight in COLUMN_WEIGHTS.items():
        if weight < 0 or weight > 2:
            errors.append(f"列权重超出合理范围 [0, 2]: {col}={weight}")

    # 验证基础分范围
    for level, score in BASE_SCORES.items():
        if score < 0 or score > 1:
            errors.append(f"基础分超出范围 [0, 1]: {level}={score}")

    # 验证阈值范围
    for level, threshold in FORCE_THRESHOLDS.items():
        if threshold < 0 or threshold > 1:
            errors.append(f"强制阈值超出范围 [0, 1]: {level}={threshold}")

    # 验证L1阈值不低于基础分
    if FORCE_THRESHOLDS["L1"] < BASE_SCORES["L1"]:
        errors.append("L1强制阈值不应低于L1基础分")

    return len(errors) == 0, errors


if __name__ == "__main__":
    # 测试
    print("⚙️ 打分参数配置")
    print("=" * 60)

    print("\n📊 列权重配置:")
    for col, weight in sorted(COLUMN_WEIGHTS.items(), key=lambda x: x[1], reverse=True):
        print(f"  {col:15s}: {weight:.2f}")

    print("\n🎯 基础分配置:")
    for level, score in BASE_SCORES.items():
        print(f"  {level}: {score:.1f}")

    print("\n🔒 强制阈值:")
    for level, threshold in FORCE_THRESHOLDS.items():
        print(f"  {level}: {threshold:.1f}")

    print("\n🎨 热力图颜色范围:")
    for range_config in HEATMAP_COLOR_RANGES:
        print(f"  [{range_config['min']:.1f}-{range_config['max']:.1f}]: "
              f"{range_config['color']} ({range_config['label']})")

    print("\n🔍 验证参数配置...")
    valid, errors = validate_parameters()
    if valid:
        print("✅ 参数配置验证通过")
    else:
        print("❌ 参数配置验证失败:")
        for error in errors:
            print(f"  - {error}")