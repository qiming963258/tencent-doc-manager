#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
30份表格真实随机CSV变化参数生成器
完全随机差异数量和位置分布，模拟真实业务场景
"""

import json
import random
import os

class RealRandomTableGenerator:
    def __init__(self):
        """初始化生成器"""
        self.standard_columns = [
            "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
            "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
            "协助人", "监督人", "重要程度", "预计完成时间", "完成进度",
            "形成计划清单", "复盘时间", "对上汇报", "应用情况", "进度分析总结"
        ]
        
        # 真实业务数据池
        self.real_data = {
            "departments": [
                "小红书运营部", "抖音内容组", "微信推广部", "视频制作组", 
                "数据分析部", "用户增长部", "产品运营部", "社群管理部"
            ],
            "project_types": [
                "目标管理", "体系建设", "流程优化", "内容策划", "数据驱动", 
                "用户增长", "技术优化", "质量管控"
            ],
            "sources": [
                "经理日常交办", "周会决策待办", "月度规划", "临时紧急任务",
                "战略项目调整", "客户需求反馈"
            ],
            "staff_names": [
                "张三", "李四", "王五", "蔡悦莹", "朱瀚桔", "曾利萍", 
                "杨佳玲", "李月", "邓总", "陈小明"
            ]
        }
    
    def generate_all_tables(self):
        """生成所有表格 - 完全随机方式"""
        print("🎲 开始生成30份完全随机的表格变化参数...")
        
        output_dir = "/root/projects/tencent-doc-manager/csv_versions/standard_outputs"
        os.makedirs(output_dir, exist_ok=True)
        
        for table_num in range(2, 31):  # table_002 到 table_030
            # 完全随机的差异数量：1到30个差异
            diff_count = random.randint(1, 30)
            
            # 随机选择部门
            department = random.choice(self.real_data["departments"])
            
            print(f"🔄 table_{table_num:03d}: {diff_count}个随机差异")
            
            table_data = {
                "comparison_summary": {
                    "baseline_file": f"baseline_table_{table_num:03d}_20250818.csv",
                    "current_file": f"current_{department}_table_{table_num:03d}_20250819.csv",
                    "total_differences": diff_count,
                    "rows_compared": random.randint(30, 120),  # 随机行数
                    "columns_compared": 19
                },
                "differences": []
            }
            
            # 生成完全随机的差异
            used_positions = set()
            for diff_id in range(1, diff_count + 1):
                # 随机位置，允许重复（真实场景中同一位置可能多次修改）
                row_num = random.randint(1, 30)
                col_index = random.randint(1, 18)
                
                # 如果位置重复，就跳过（保持真实性）
                position = (row_num, col_index)
                if position in used_positions:
                    continue
                used_positions.add(position)
                
                col_name = self.standard_columns[col_index]
                original, new = self.random_realistic_change(col_name)
                
                difference = {
                    "序号": diff_id,
                    "行号": row_num,
                    "列名": col_name,
                    "列索引": col_index,
                    "原值": original,
                    "新值": new,
                    "位置": f"行{row_num}列{col_index}({col_name})"
                }
                
                table_data["differences"].append(difference)
            
            # 更新实际生成的差异数量
            table_data["comparison_summary"]["total_differences"] = len(table_data["differences"])
            
            # 保存文件
            output_file = f"{output_dir}/table_{table_num:03d}_diff.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(table_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ table_{table_num:03d}_diff.json 完成 - 实际{len(table_data['differences'])}个差异")
        
        print(f"\n🎉 29份完全随机表格数据生成完成！")
    
    def random_realistic_change(self, column_name):
        """基于列名生成随机但符合逻辑的变更"""
        
        if column_name == "项目类型":
            original = random.choice(self.real_data["project_types"])
            new = random.choice(self.real_data["project_types"])
        elif column_name == "来源":
            original = random.choice(self.real_data["sources"])
            # 50%概率是组合来源
            if random.random() < 0.5:
                new = f"{random.choice(self.real_data['sources'])},{random.choice(self.real_data['sources'])}"
            else:
                new = random.choice(self.real_data["sources"])
        elif "负责人" in column_name or "协助人" in column_name or "监督人" in column_name:
            original = random.choice(self.real_data["staff_names"])
            # 30%概率是多人
            if random.random() < 0.3:
                new = f"{random.choice(self.real_data['staff_names'])},{random.choice(self.real_data['staff_names'])}"
            else:
                new = random.choice(self.real_data["staff_names"])
        elif column_name == "重要程度":
            original = str(random.randint(1, 5))
            new = str(random.randint(1, 5))
        elif column_name == "完成进度":
            original = f"{random.randint(0, 9)}0%"
            new = f"{random.randint(0, 10)}0%"
        elif "时间" in column_name:
            original = f"2025/7/{random.randint(1, 31)}"
            new = f"2025/8/{random.randint(1, 31)}"
        elif column_name == "对上汇报":
            statuses = ["已汇报已结项", "待汇报", "尚未汇报", "计划汇报"]
            original = random.choice(statuses)
            new = random.choice(statuses)
        else:
            # 其他列随机内容
            original = f"原始{column_name}_{random.randint(1, 100)}"
            new = f"修改{column_name}_{random.randint(1, 100)}"
        
        return original, new

if __name__ == "__main__":
    generator = RealRandomTableGenerator()
    generator.generate_all_tables()