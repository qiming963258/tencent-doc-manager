#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建真实随机分布的综合打分数据
18个表格，约100个修改，无规律分布
"""

import json
import random
from datetime import datetime
import os

def create_realistic_comprehensive_score():
    """创建真实随机的综合打分数据"""
    
    # 定义列名
    columns = [
        "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
        "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
        "协助人", "监督人", "重要程度", "预计完成时间", 
        "完成进度", "形成计划清单", "复盘时间", "对上汇报",
        "应用情况", "进度分析总结"
    ]
    
    # 18个表格的名称（使用真实业务场景）
    table_names = [
        "销售部门Q4计划", "市场推广方案", "产品研发进度", "客户服务优化",
        "供应链管理", "财务预算执行", "人力资源规划", "技术架构升级",
        "数据分析平台", "移动端开发", "云服务迁移", "安全合规审查",
        "国际业务拓展", "品牌建设项目", "创新实验室", "数字化转型",
        "战略合作伙伴", "年度总结报告"
    ]
    
    # 风险等级定义
    risk_levels = ["L1", "L2", "L3"]
    
    # 生成18个表格的数据
    tables = []
    total_modifications = 0
    
    # 为每个表格随机分配修改数量（更真实的分布）
    # 使用泊松分布来模拟真实的修改分布
    modification_counts = []
    target_total = 100
    
    # 使用更真实的分布：有些表格没有修改，有些表格修改较多
    weights = [random.random() for _ in range(18)]
    total_weight = sum(weights)
    
    for i in range(18):
        # 基于权重分配修改数量
        base_count = int((weights[i] / total_weight) * target_total)
        # 添加随机波动
        variance = random.randint(-3, 3)
        count = max(0, base_count + variance)
        modification_counts.append(count)
    
    # 调整总数到约100个
    current_total = sum(modification_counts)
    if current_total < 95:
        # 随机增加一些修改
        for _ in range(95 - current_total):
            idx = random.randint(0, 17)
            modification_counts[idx] += 1
    elif current_total > 105:
        # 随机减少一些修改
        for _ in range(current_total - 105):
            idx = random.randint(0, 17)
            if modification_counts[idx] > 0:
                modification_counts[idx] -= 1
    
    # 打乱顺序以避免明显的模式
    random.shuffle(modification_counts)
    
    for idx, table_name in enumerate(table_names):
        num_modifications = modification_counts[idx]
        
        # 创建表格数据
        table_data = {
            "table_id": idx + 1,
            "table_name": table_name,
            "total_rows": random.randint(30, 80),  # 随机行数
            "total_columns": 19,
            "modifications": []
        }
        
        # 如果这个表格有修改
        if num_modifications > 0:
            # 生成修改位置（避免重复）
            modified_cells = set()
            
            while len(modified_cells) < num_modifications:
                row = random.randint(0, table_data["total_rows"] - 1)
                col = random.randint(0, 18)
                modified_cells.add((row, col))
            
            # 为每个修改生成数据
            for row, col in modified_cells:
                # 随机选择风险等级（更真实的分布）
                risk_prob = random.random()
                if risk_prob < 0.15:  # 15% L1高风险
                    risk_level = "L1"
                elif risk_prob < 0.60:  # 45% L2中风险
                    risk_level = "L2"
                else:  # 40% L3低风险
                    risk_level = "L3"
                
                modification = {
                    "row": row,
                    "column": col,
                    "column_name": columns[col],
                    "old_value": f"原始值_{random.randint(1000, 9999)}",
                    "new_value": f"修改值_{random.randint(1000, 9999)}",
                    "risk_level": risk_level,
                    "change_type": random.choice(["update", "correction", "addition"]),
                    "timestamp": f"2025-01-12T{random.randint(8, 18):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
                }
                table_data["modifications"].append(modification)
        
        # 计算表格统计
        table_data["modification_count"] = num_modifications
        table_data["risk_summary"] = {
            "L1": sum(1 for m in table_data["modifications"] if m["risk_level"] == "L1"),
            "L2": sum(1 for m in table_data["modifications"] if m["risk_level"] == "L2"),
            "L3": sum(1 for m in table_data["modifications"] if m["risk_level"] == "L3")
        }
        
        # 计算综合风险分数（加权平均）
        if num_modifications > 0:
            risk_score = (
                table_data["risk_summary"]["L1"] * 0.9 +
                table_data["risk_summary"]["L2"] * 0.5 +
                table_data["risk_summary"]["L3"] * 0.2
            ) / num_modifications
        else:
            risk_score = 0
        
        table_data["overall_risk_score"] = round(risk_score, 3)
        
        tables.append(table_data)
        total_modifications += num_modifications
    
    # 按风险分数排序（高风险优先）
    tables.sort(key=lambda x: x["overall_risk_score"], reverse=True)
    
    # 创建完整的数据结构
    comprehensive_data = {
        "metadata": {
            "version": "2.0",
            "generated_at": datetime.now().isoformat(),
            "week_number": "W03",
            "total_tables": 18,
            "total_modifications": total_modifications,
            "data_type": "comprehensive_scoring",
            "description": "真实随机分布的综合打分数据"
        },
        "summary": {
            "total_modifications": total_modifications,
            "risk_distribution": {
                "L1": sum(t["risk_summary"]["L1"] for t in tables),
                "L2": sum(t["risk_summary"]["L2"] for t in tables),
                "L3": sum(t["risk_summary"]["L3"] for t in tables)
            },
            "tables_with_modifications": sum(1 for t in tables if t["modification_count"] > 0),
            "tables_without_modifications": sum(1 for t in tables if t["modification_count"] == 0),
            "average_modifications_per_table": round(total_modifications / 18, 2),
            "max_modifications_in_table": max(t["modification_count"] for t in tables),
            "min_modifications_in_table": min(t["modification_count"] for t in tables)
        },
        "tables": tables,
        "column_definitions": columns
    }
    
    # 保存文件 - 使用新的周文件夹结构
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    week_number = 3  # W03
    week_dir = f"/root/projects/tencent-doc-manager/scoring_results/2025_W{week_number}"
    filename = f"{week_dir}/comprehensive_score_W{week_number:02d}_realistic_{timestamp}.json"

    # 确保目录存在
    os.makedirs(week_dir, exist_ok=True)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 生成完成: {filename}")
    print(f"📊 统计信息:")
    print(f"  - 总表格数: 18")
    print(f"  - 总修改数: {total_modifications}")
    print(f"  - 有修改的表格: {comprehensive_data['summary']['tables_with_modifications']}")
    print(f"  - 无修改的表格: {comprehensive_data['summary']['tables_without_modifications']}")
    print(f"  - L1高风险: {comprehensive_data['summary']['risk_distribution']['L1']}")
    print(f"  - L2中风险: {comprehensive_data['summary']['risk_distribution']['L2']}")
    print(f"  - L3低风险: {comprehensive_data['summary']['risk_distribution']['L3']}")
    print(f"  - 最多修改: {comprehensive_data['summary']['max_modifications_in_table']}个")
    print(f"  - 最少修改: {comprehensive_data['summary']['min_modifications_in_table']}个")
    
    # 显示每个表格的修改数量分布
    print("\n📈 表格修改分布:")
    for i, table in enumerate(tables[:10], 1):  # 只显示前10个
        bar = "█" * (table["modification_count"] // 2) if table["modification_count"] > 0 else "□"
        print(f"  {i:2d}. {table['table_name'][:15]:<15} [{table['modification_count']:3d}] {bar}")
    if len(tables) > 10:
        print(f"  ... 还有{len(tables) - 10}个表格")
    
    return filename

if __name__ == "__main__":
    create_realistic_comprehensive_score()