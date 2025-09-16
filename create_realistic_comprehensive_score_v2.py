#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建真实随机分布的综合打分数据 V2
匹配8089期望的数据格式
18个表格，约100个修改，无规律分布
"""

import json
import random
from datetime import datetime
import os

def create_realistic_comprehensive_score_v2():
    """创建匹配8089格式的真实随机综合打分数据"""
    
    # 18个表格的名称（使用真实业务场景）
    table_names = [
        "销售部门Q4计划", "市场推广方案", "产品研发进度", "客户服务优化",
        "供应链管理", "财务预算执行", "人力资源规划", "技术架构升级",
        "数据分析平台", "移动端开发", "云服务迁移", "安全合规审查",
        "国际业务拓展", "品牌建设项目", "创新实验室", "数字化转型",
        "战略合作伙伴", "年度总结报告"
    ]
    
    # 定义列名
    columns = [
        "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
        "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
        "协助人", "监督人", "重要程度", "预计完成时间", 
        "完成进度", "形成计划清单", "复盘时间", "对上汇报",
        "应用情况", "进度分析总结"
    ]
    
    # 生成修改分布（更真实的随机分布）
    modification_counts = []
    target_total = 100
    
    # 使用幂律分布：少数表格有很多修改，多数表格修改较少
    for i in range(18):
        if random.random() < 0.1:  # 10%概率没有修改
            count = 0
        elif random.random() < 0.3:  # 20%概率有较多修改
            count = random.randint(8, 15)
        else:  # 70%概率有少量修改
            count = random.randint(1, 7)
        modification_counts.append(count)
    
    # 调整总数到约100个
    current_total = sum(modification_counts)
    while abs(current_total - target_total) > 10:
        if current_total < target_total:
            idx = random.randint(0, 17)
            modification_counts[idx] += 1
            current_total += 1
        else:
            idx = random.randint(0, 17)
            if modification_counts[idx] > 0:
                modification_counts[idx] -= 1
                current_total -= 1
    
    # 创建table_scores数据
    table_scores = []
    total_modifications = 0
    
    for idx, (table_name, mod_count) in enumerate(zip(table_names, modification_counts)):
        # 生成每个表格的修改位置
        modifications = {}
        
        if mod_count > 0:
            # 随机选择修改的单元格
            for _ in range(mod_count):
                row = random.randint(1, 50)
                col = random.randint(0, 18)
                col_name = columns[col]
                
                # 生成风险等级
                risk_prob = random.random()
                if risk_prob < 0.15:  # 15% L1高风险
                    risk_level = "L1"
                    risk_score = random.uniform(0.7, 1.0)
                elif risk_prob < 0.60:  # 45% L2中风险
                    risk_level = "L2"
                    risk_score = random.uniform(0.4, 0.7)
                else:  # 40% L3低风险
                    risk_level = "L3"
                    risk_score = random.uniform(0.1, 0.4)
                
                # 存储修改信息
                cell_key = f"row_{row}_{col_name}"
                modifications[cell_key] = {
                    "risk_level": risk_level,
                    "risk_score": round(risk_score, 3),
                    "column": col_name
                }
        
        # 计算表格的综合风险分数
        if modifications:
            risk_scores = [m["risk_score"] for m in modifications.values()]
            overall_risk = sum(risk_scores) / len(risk_scores)
        else:
            overall_risk = 0
        
        # 统计风险等级分布
        risk_distribution = {"L1": 0, "L2": 0, "L3": 0}
        for mod in modifications.values():
            risk_distribution[mod["risk_level"]] += 1
        
        table_score = {
            "table_name": table_name,
            "table_id": idx + 1,
            "overall_risk_score": round(overall_risk, 3),
            "modification_count": mod_count,
            "risk_distribution": risk_distribution,
            "critical_changes": risk_distribution["L1"],
            "modifications": modifications
        }
        
        table_scores.append(table_score)
        total_modifications += mod_count
    
    # 按风险分数排序（高风险优先）
    table_scores.sort(key=lambda x: x["overall_risk_score"], reverse=True)
    
    # 创建交叉表格分析
    cross_table_analysis = {
        "total_tables": 18,
        "total_modifications": total_modifications,
        "tables_with_changes": sum(1 for t in table_scores if t["modification_count"] > 0),
        "high_risk_tables": sum(1 for t in table_scores if t["overall_risk_score"] > 0.7),
        "medium_risk_tables": sum(1 for t in table_scores if 0.4 <= t["overall_risk_score"] <= 0.7),
        "low_risk_tables": sum(1 for t in table_scores if 0 < t["overall_risk_score"] < 0.4),
        "risk_heatmap": []
    }
    
    # 生成风险热力图数据（简化版）
    for table in table_scores:
        row_data = []
        for col_name in columns:
            # 查找该列是否有修改
            found = False
            for key, mod in table["modifications"].items():
                if mod["column"] == col_name:
                    row_data.append(mod["risk_score"])
                    found = True
                    break
            if not found:
                row_data.append(0)
        cross_table_analysis["risk_heatmap"].append(row_data)
    
    # 创建完整的数据结构（匹配旧格式）
    comprehensive_data = {
        "metadata": {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "week_number": "W03",
            "analysis_type": "comprehensive_scoring",
            "data_source": "realistic_random"
        },
        "table_scores": table_scores,
        "cross_table_analysis": cross_table_analysis
    }
    
    # 保存文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    week_number = comprehensive_data['metadata']['week_number']
filename = f"/root/projects/tencent-doc-manager/scoring_results/2025_{week_number}/comprehensive_score_{week_number}_{timestamp}.json"
    
    # 确保目录存在
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 生成完成: {filename}")
    print(f"📊 统计信息:")
    print(f"  - 总表格数: 18")
    print(f"  - 总修改数: {total_modifications}")
    print(f"  - 有修改的表格: {cross_table_analysis['tables_with_changes']}")
    print(f"  - 无修改的表格: {18 - cross_table_analysis['tables_with_changes']}")
    
    # 计算总体风险分布
    total_l1 = sum(t["risk_distribution"]["L1"] for t in table_scores)
    total_l2 = sum(t["risk_distribution"]["L2"] for t in table_scores)
    total_l3 = sum(t["risk_distribution"]["L3"] for t in table_scores)
    
    print(f"  - L1高风险: {total_l1}")
    print(f"  - L2中风险: {total_l2}")
    print(f"  - L3低风险: {total_l3}")
    
    # 显示修改分布
    print("\n📈 表格修改分布（前10个）:")
    for i, table in enumerate(table_scores[:10], 1):
        bar = "█" * (table["modification_count"] // 2) if table["modification_count"] > 0 else "□"
        risk_level = "🔴" if table["overall_risk_score"] > 0.7 else "🟡" if table["overall_risk_score"] > 0.4 else "🟢" if table["overall_risk_score"] > 0 else "⚪"
        print(f"  {i:2d}. {risk_level} {table['table_name'][:15]:<15} [{table['modification_count']:3d}] {bar}")
    
    return filename

if __name__ == "__main__":
    create_realistic_comprehensive_score_v2()