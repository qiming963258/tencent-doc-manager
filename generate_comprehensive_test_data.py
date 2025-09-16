#!/usr/bin/env python3
"""
生成包含22个表格的综合打分模拟数据
基于真实综合打分文件格式，错误数超过100个且随机分布
"""

import json
import random
from datetime import datetime

# 定义真实的表格名称（企业级表格）
TABLE_NAMES = [
    "项目进度跟踪表",
    "客户信息管理表",
    "财务月度报表",
    "人力资源档案表",
    "产品库存清单",
    "销售业绩统计表",
    "供应商管理表",
    "市场活动计划表",
    "研发任务分配表",
    "质量检测记录表",
    "合同管理台账",
    "员工考勤记录表",
    "培训计划执行表",
    "设备维护记录表",
    "采购订单跟踪表",
    "客户投诉处理表",
    "生产计划排程表",
    "物流配送记录表",
    "会议纪要管理表",
    "风险评估矩阵表",
    "预算执行情况表",
    "竞品分析对比表"
]

# 定义标准的19个列名
STANDARD_COLUMNS = [
    "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
    "关键KR对齐", "具体计划内容", "邓总指导登记（日更新）", "负责人", "协助人",
    "监督人", "重要程度", "预计完成时间", "完成进度", "形成计划清单",
    "复盘时间", "对上汇报", "进度分析总结", "应用情况"
]

# AI决策类型
AI_DECISIONS = ["APPROVE", "REVIEW", "CONDITIONAL", "REJECT"]

def generate_column_score(risk_level, has_modification):
    """生成列的打分数据"""
    if not has_modification:
        return None
    
    # 根据风险等级生成不同范围的分数
    if risk_level == "L1":
        base_score = random.uniform(0.7, 1.0)
    elif risk_level == "L2":
        base_score = random.uniform(0.3, 0.7)
    else:  # L3
        base_score = random.uniform(0.1, 0.4)
    
    # 添加一些噪声
    score = base_score + random.uniform(-0.1, 0.1)
    score = max(0.01, min(1.0, score))  # 限制在0.01-1.0范围
    
    # 随机决定是否有AI决策
    ai_decision = None
    if random.random() > 0.5:
        decision_type = random.choice(AI_DECISIONS)
        ai_decision = {decision_type: 1}
    
    return {
        "column_level": risk_level,
        "modifications": random.randint(1, 8),  # 每列1-8个修改
        "scores": [round(score, 3)],
        "aggregated_score": round(score, 3),
        "max_score": round(score, 3),
        "min_score": round(score, 3),
        "risk_trend": random.choice(["increasing", "stable", "decreasing"]),
        "ai_decisions": ai_decision
    }

def generate_table_data(table_name, table_index, target_modifications):
    """生成单个表格的数据"""
    
    # 决定这个表格的风险等级
    if table_index < 4:  # 前4个表格为L1
        table_risk = "L1"
        risk_score = random.uniform(0.7, 0.95)
    elif table_index < 11:  # 中间7个表格为L2
        table_risk = "L2"
        risk_score = random.uniform(0.4, 0.69)
    else:  # 后11个表格为L3
        table_risk = "L3"
        risk_score = random.uniform(0.15, 0.39)
    
    # 决定哪些列有修改（随机选择5-12列）
    num_modified_cols = random.randint(5, min(12, len(STANDARD_COLUMNS)))
    modified_columns = random.sample(STANDARD_COLUMNS, num_modified_cols)
    
    # 生成列的打分数据
    column_scores = {}
    total_modifications = 0
    
    for col in modified_columns:
        # 为主要列分配更高的风险等级
        if col in ["负责人", "重要程度", "具体计划内容", "邓总指导登记（日更新）"]:
            col_risk = random.choice(["L1", "L1", "L2"])  # 更倾向于L1
        elif col in ["任务发起时间", "预计完成时间", "关键KR对齐"]:
            col_risk = random.choice(["L1", "L2", "L2"])  # 平衡L1和L2
        else:
            col_risk = random.choice(["L2", "L3", "L3"])  # 更倾向于L3
            
        col_data = generate_column_score(col_risk, True)
        if col_data:
            column_scores[col] = col_data
            total_modifications += col_data["modifications"]
    
    # 构建表格数据
    table_data = {
        "table_name": table_name,
        "table_url": f"https://docs.qq.com/sheet/DWE{random.randint(1000,9999)}{random.choice(['ABC','XYZ','MNO'])}{random.randint(100,999)}",
        "modifications_count": total_modifications,
        "column_scores": column_scores,
        "table_summary": {
            "overall_risk_score": round(risk_score, 3),
            "risk_level": table_risk.replace("L", "LEVEL_"),
            "top_risks": [
                {
                    "column": col,
                    "score": column_scores[col]["aggregated_score"],
                    "reason": f"{col}发生重大变更"
                }
                for col in list(column_scores.keys())[:3]  # 取前3个高风险列
            ],
            "recommendation": f"建议重点关注{list(column_scores.keys())[0]}的变更",
            "confidence": round(random.uniform(0.75, 0.95), 2)
        }
    }
    
    return table_data, total_modifications

def generate_comprehensive_scoring():
    """生成完整的综合打分文件"""
    
    # 生成22个表格的数据
    tables_data = []
    total_modifications = 0
    
    # 目标是超过100个修改，平均每个表格需要5-6个修改
    for i, table_name in enumerate(TABLE_NAMES):
        # 为了确保总修改数超过100，给一些表格分配更多修改
        if i < 5:  # 前5个表格多一些修改
            target_mods = random.randint(8, 12)
        else:
            target_mods = random.randint(3, 8)
            
        table_data, mods = generate_table_data(table_name, i, target_mods)
        tables_data.append(table_data)
        total_modifications += mods
    
    # 构建完整的综合打分文件
    comprehensive_data = {
        "metadata": {
            "week": "W37",
            "generation_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_tables": len(tables_data),
            "total_modifications": total_modifications,
            "scoring_version": "v2.0",
            "data_source": "comprehensive_analysis",
            "analysis_type": "multi_table_comparison"
        },
        "table_scores": tables_data,
        "summary": {
            "high_risk_tables": sum(1 for t in tables_data if "LEVEL_L1" in str(t)),
            "medium_risk_tables": sum(1 for t in tables_data if "LEVEL_L2" in str(t)),
            "low_risk_tables": sum(1 for t in tables_data if "LEVEL_L3" in str(t)),
            "total_modifications": total_modifications,
            "average_risk_score": round(
                sum(t["table_summary"]["overall_risk_score"] for t in tables_data) / len(tables_data),
                3
            ),
            "recommendation": "建议优先处理高风险表格的变更审批"
        }
    }
    
    return comprehensive_data

# 生成数据
print("🎲 生成综合打分模拟数据...")
data = generate_comprehensive_scoring()

# 保存文件
output_file = "/root/projects/tencent-doc-manager/scoring_results/comprehensive_score_W37_realistic_22tables.json"
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ 文件已生成: {output_file}")
print(f"📊 统计信息:")
print(f"  - 表格总数: {data['metadata']['total_tables']}")
print(f"  - 修改总数: {data['metadata']['total_modifications']}")
print(f"  - 高风险表格: {data['summary']['high_risk_tables']}")
print(f"  - 中风险表格: {data['summary']['medium_risk_tables']}")
print(f"  - 低风险表格: {data['summary']['low_risk_tables']}")
print(f"  - 平均风险分数: {data['summary']['average_risk_score']}")