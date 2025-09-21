#!/usr/bin/env python3
"""
生成更连贯的测试数据，避免热团分离
"""

import json
import random
import math
from typing import List, Dict, Any


def generate_coherent_heat_values(table_index: int, total_tables: int) -> List[float]:
    """
    生成连贯的热度值，确保相邻表格和相邻列有相似的热度模式

    Args:
        table_index: 当前表格索引
        total_tables: 总表格数

    Returns:
        19个热度值的列表
    """
    heat_values = []

    # 定义热度中心和波形
    # 让热度在矩阵中形成连续的波形，而不是跳跃的点

    # 计算这个表格的主热度区域
    # 使用正弦波让热度中心平滑移动
    table_position = table_index / max(1, total_tables - 1)  # 0到1之间

    # 主热度中心在列空间中移动
    primary_center = 9 + 8 * math.sin(table_position * math.pi)  # 在1-17之间移动
    secondary_center = 9 - 6 * math.sin(table_position * math.pi * 2)  # 次要热度中心

    # 基础热度级别（随表格位置变化）
    base_heat = 0.3 + 0.4 * math.sin(table_position * math.pi * 0.5)

    for col_index in range(19):
        # 计算到主热度中心的距离
        dist_to_primary = abs(col_index - primary_center)
        dist_to_secondary = abs(col_index - secondary_center)

        # 使用高斯分布生成热度
        # 主热度贡献
        primary_heat = math.exp(-dist_to_primary**2 / 8) * 0.7
        # 次要热度贡献
        secondary_heat = math.exp(-dist_to_secondary**2 / 12) * 0.3

        # 合并热度
        heat = base_heat + primary_heat + secondary_heat

        # 添加小幅随机扰动
        heat += random.uniform(-0.1, 0.1)

        # 限制在[0.05, 0.95]范围内
        heat = max(0.05, min(0.95, heat))

        heat_values.append(round(heat, 2))

    return heat_values


def generate_coherent_comprehensive_data(num_tables: int = 22) -> Dict[str, Any]:
    """
    生成连贯的综合评分数据
    """
    # 表格名称列表
    table_names = [
        "副本-测试版本-出国销售计划表",
        "副本-测试版本-回国销售计划表",
        "测试版本-小红书部门",
        "产品库存管理表",
        "财务报表Q3",
        "员工考勤记录",
        "项目进度跟踪",
        "客户反馈汇总",
        "供应商管理",
        "市场营销计划",
        "产品定价策略",
        "技术文档管理",
        "质量检测报告",
        "合同管理台账",
        "研发进度表",
        "培训计划表",
        "物流跟踪表",
        "费用报销单",
        "年度预算表",
        "风险评估表",
        "会议记录表",
        "绩效考核表"
    ]

    # 确保有足够的表格名称
    while len(table_names) < num_tables:
        table_names.append(f"业务表格{len(table_names) + 1}")

    table_scores = []
    total_modifications = 0

    for i in range(num_tables):
        # 生成连贯的热度值
        heat_values = generate_coherent_heat_values(i, num_tables)

        # 计算修改数（基于平均热度）
        avg_heat = sum(heat_values) / len(heat_values)
        modifications = int(50 + avg_heat * 150 + random.uniform(-20, 20))
        modifications = max(5, modifications)  # 至少5个修改

        total_modifications += modifications

        # 确定风险等级
        max_heat = max(heat_values)
        if max_heat > 0.8:
            risk_level = "L3"
        elif max_heat > 0.5:
            risk_level = "L2"
        else:
            risk_level = "L1"

        table_scores.append({
            "table_name": table_names[i],
            "name": table_names[i],
            "doc_url": f"https://docs.qq.com/sheet/test{i+1}",
            "url": f"https://docs.qq.com/sheet/test{i+1}",
            "modifications": modifications,
            "risk_level": risk_level,
            "heat_values": heat_values
        })

    # 构建完整的数据结构
    data = {
        "metadata": {
            "week": 37,
            "timestamp": "2025-09-15T10:00:00",
            "table_count": num_tables,
            "total_modifications": total_modifications,
            "description": "连贯热度分布测试数据"
        },
        "table_scores": table_scores,
        "total_modifications": total_modifications
    }

    return data


def main():
    """生成并保存连贯的测试数据"""
    print("🔄 生成连贯的综合评分测试数据...")

    # 生成数据
    data = generate_coherent_comprehensive_data(22)

    # 保存文件
    output_path = "/root/projects/tencent-doc-manager/scoring_results/2025_W37/comprehensive_score_W37_coherent.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ 数据已保存到: {output_path}")

    # 显示热度分布预览
    print("\n📊 热度分布预览（前5个表格）：")
    for i, table in enumerate(data['table_scores'][:5]):
        heat_values = table['heat_values']
        heat_str = ''.join(['█' if v > 0.7 else '▓' if v > 0.4 else '░' for v in heat_values])
        print(f"{i+1:2d}. {table['table_name'][:20]:20s}: {heat_str}")

    print("\n💡 特点：")
    print("  - 热度在相邻表格间平滑过渡")
    print("  - 热度在相邻列间连续分布")
    print("  - 形成自然的热度波形，避免跳跃")


if __name__ == "__main__":
    main()