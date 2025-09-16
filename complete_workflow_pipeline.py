#!/usr/bin/env python3
"""完整链路打通脚本 - 从CSV对比到综合打分的完整实现"""

import csv
import json
import os
import sys
from datetime import datetime
import random
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.insert(0, '/root/projects/tencent-doc-manager')

# 标准列定义（根据specs规范）
STANDARD_COLUMNS = [
    "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
    "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人",
    "协助人", "监督人", "重要程度", "预计完成时间", "完成进度",
    "完成链接", "经理分析复盘", "最新复盘时间", "对上汇报", "应用情况"
]

# 列级别定义（根据0000标准文档）
L1_COLUMNS = ["序号", "项目类型", "目标对齐", "关键KR对齐", "重要程度"]
L2_COLUMNS = ["负责人", "具体计划内容", "协助人", "监督人", "预计完成时间"]
L3_COLUMNS = [col for col in STANDARD_COLUMNS if col not in L1_COLUMNS and col not in L2_COLUMNS]

class CompletePipeline:
    """完整链路处理管道"""

    def __init__(self):
        self.week_number = 38  # 当前周数
        self.modifications = []
        self.table_scores = []
        self.column_avg_scores = {}

    def log(self, msg, level="INFO"):
        """增强日志输出"""
        if level == "ERROR":
            logger.error(f"❌ {msg}")
        elif level == "WARNING":
            logger.warning(f"⚠️ {msg}")
        elif level == "SUCCESS":
            logger.info(f"✅ {msg}")
        elif level == "PROCESS":
            logger.info(f"🔄 {msg}")
        else:
            logger.info(f"📋 {msg}")

    def load_csv_as_table(self, file_path):
        """加载CSV文件为表格数据"""
        self.log(f"加载CSV文件: {os.path.basename(file_path)}")

        data = []
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                data.append(row)

        self.log(f"加载完成: {len(data)} 行 × {len(data[0]) if data else 0} 列")
        return data

    def standardize_columns(self, data):
        """标准化列名（阶段1）"""
        self.log("阶段1: 标准化列名", "PROCESS")

        if not data or len(data) < 3:
            self.log("数据不足，无法标准化", "WARNING")
            return data

        # 假设第2行是列标题
        header_row = data[1] if len(data) > 1 else []

        # 映射到标准列名
        standardized_header = []
        for i, col in enumerate(header_row):
            if i < len(STANDARD_COLUMNS):
                standardized_header.append(STANDARD_COLUMNS[i])
            else:
                standardized_header.append(f"列{i+1}")

        # 替换原始列名
        if len(data) > 1:
            data[1] = standardized_header

        self.log(f"标准化完成: {len(standardized_header)} 个列名")
        return data

    def compare_tables(self, baseline_data, current_data):
        """对比表格数据（阶段2）"""
        self.log("阶段2: CSV对比分析", "PROCESS")

        differences = []
        max_rows = max(len(baseline_data), len(current_data))

        for row_idx in range(max_rows):
            if row_idx < 2:  # 跳过标题行
                continue

            baseline_row = baseline_data[row_idx] if row_idx < len(baseline_data) else []
            current_row = current_data[row_idx] if row_idx < len(current_data) else []

            max_cols = max(len(baseline_row), len(current_row))

            for col_idx in range(min(max_cols, len(STANDARD_COLUMNS))):
                baseline_val = baseline_row[col_idx] if col_idx < len(baseline_row) else ""
                current_val = current_row[col_idx] if col_idx < len(current_row) else ""

                if baseline_val != current_val:
                    column_name = STANDARD_COLUMNS[col_idx] if col_idx < len(STANDARD_COLUMNS) else f"列{col_idx+1}"
                    differences.append({
                        "row": row_idx,
                        "col": col_idx,
                        "column_name": column_name,
                        "old_value": str(baseline_val)[:100],
                        "new_value": str(current_val)[:100]
                    })

        self.log(f"发现 {len(differences)} 处差异")
        return differences

    def apply_base_scoring(self, differences):
        """应用基础打分（阶段3）"""
        self.log("阶段3: 基础打分（根据列级别）", "PROCESS")

        for diff in differences:
            column_name = diff["column_name"]

            # 根据列级别设置基础分
            if column_name in L1_COLUMNS:
                diff["base_score"] = 0.8
                diff["column_level"] = "L1"
            elif column_name in L2_COLUMNS:
                diff["base_score"] = 0.4
                diff["column_level"] = "L2"
            else:
                diff["base_score"] = 0.1
                diff["column_level"] = "L3"

            # 初始化最终得分为基础分
            diff["final_score"] = diff["base_score"]

        self.log(f"基础打分完成: L1={sum(1 for d in differences if d['column_level']=='L1')}个, "
                f"L2={sum(1 for d in differences if d['column_level']=='L2')}个, "
                f"L3={sum(1 for d in differences if d['column_level']=='L3')}个")

        return differences

    def apply_ai_scoring(self, differences):
        """AI智能打分（阶段4 - 仅L2列）"""
        self.log("阶段4: AI智能打分（仅L2列）", "PROCESS")

        l2_count = 0
        for diff in differences:
            if diff["column_level"] == "L2":
                # 模拟AI评分（实际应调用AI API）
                old_val = diff["old_value"].lower()
                new_val = diff["new_value"].lower()

                # 简单的相似度评分
                if "123" in new_val:
                    # 检测到测试数据，高风险
                    ai_score = 0.9
                elif old_val == "" and new_val != "":
                    # 新增内容，中风险
                    ai_score = 0.6
                elif old_val != "" and new_val == "":
                    # 删除内容，高风险
                    ai_score = 0.8
                else:
                    # 修改内容，根据差异程度评分
                    ai_score = 0.5 + random.random() * 0.3

                # 确保不低于L2基础分
                diff["ai_score"] = max(0.4, ai_score)
                diff["final_score"] = diff["ai_score"]
                l2_count += 1

        self.log(f"AI评分完成: 处理了 {l2_count} 个L2列修改")
        return differences

    def generate_detailed_scores(self, differences, table_name, table_url):
        """生成详细打分（阶段5）"""
        self.log("阶段5: 详细打分文件生成", "PROCESS")

        # 按列聚合修改
        column_modifications = {}

        for diff in differences:
            col_name = diff["column_name"]
            if col_name not in column_modifications:
                column_modifications[col_name] = {
                    "column_level": diff["column_level"],
                    "modified_rows": [],
                    "row_scores": [],
                    "modifications": []
                }

            column_modifications[col_name]["modified_rows"].append(diff["row"])
            column_modifications[col_name]["row_scores"].append(diff["final_score"])
            column_modifications[col_name]["modifications"].append(diff)

        # 计算每列的平均分
        column_scores = {}
        for col_name, mods in column_modifications.items():
            if mods["row_scores"]:
                avg_score = sum(mods["row_scores"]) / len(mods["row_scores"])
            else:
                avg_score = 0.0

            column_scores[col_name] = {
                "avg_score": round(avg_score, 3),
                "modified_rows": mods["modified_rows"],
                "row_scores": [round(s, 3) for s in mods["row_scores"]],
                "column_level": mods["column_level"],
                "modification_count": len(mods["modified_rows"])
            }

        # 创建详细打分结构
        detailed_score = {
            "table_name": table_name,
            "table_url": table_url,
            "total_modifications": len(differences),
            "column_scores": column_scores,
            "overall_risk_score": round(
                sum(d["final_score"] for d in differences) / len(differences) if differences else 0,
                3
            )
        }

        # 保存详细打分文件
        output_dir = "/root/projects/tencent-doc-manager/scoring_results/detailed"
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"detailed_score_{table_name}_{timestamp}.json")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(detailed_score, f, ensure_ascii=False, indent=2)

        self.log(f"详细打分保存到: {output_file}", "SUCCESS")

        return detailed_score

    def generate_comprehensive_score(self, all_table_scores):
        """生成综合打分（阶段6-7）"""
        self.log("阶段6-7: 综合打分汇总", "PROCESS")

        # 五个关键内容
        # 1. 所有表名
        table_names = [score["table_name"] for score in all_table_scores]

        # 2. 每标准列平均加权修改打分
        column_avg_scores = {}
        for col_name in STANDARD_COLUMNS:
            scores = []
            weights = []

            for table_score in all_table_scores:
                if col_name in table_score["column_scores"]:
                    col_data = table_score["column_scores"][col_name]
                    scores.append(col_data["avg_score"])
                    weights.append(col_data["modification_count"])

            if scores and weights:
                # 加权平均
                weighted_avg = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
                column_avg_scores[col_name] = round(weighted_avg, 3)
            else:
                column_avg_scores[col_name] = 0.0

        # 3. 表格详细数据（已包含在table_scores中）

        # 4. 表格URL列表
        table_urls = [score["table_url"] for score in all_table_scores]

        # 5. 全部修改数
        total_modifications = sum(score["total_modifications"] for score in all_table_scores)

        # 创建综合打分结构
        comprehensive_score = {
            "generation_time": datetime.now().isoformat(),
            "scoring_version": "2.0",
            "scoring_standard": "0000-颜色和级别打分标准",
            "week_number": f"W{self.week_number}",

            # 五个关键内容
            "table_names": table_names,
            "column_avg_scores": column_avg_scores,
            "table_scores": all_table_scores,
            "table_urls": table_urls,
            "total_modifications": total_modifications,

            # 附加统计信息
            "risk_summary": {
                "high_risk_count": sum(1 for t in all_table_scores if t["overall_risk_score"] >= 0.6),
                "medium_risk_count": sum(1 for t in all_table_scores if 0.4 <= t["overall_risk_score"] < 0.6),
                "low_risk_count": sum(1 for t in all_table_scores if t["overall_risk_score"] < 0.4)
            },

            # UI数据（热力图需要的格式）
            "ui_data": self.generate_ui_data(all_table_scores, column_avg_scores)
        }

        # 保存综合打分文件
        output_dir = "/root/projects/tencent-doc-manager/scoring_results/comprehensive"
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"comprehensive_score_W{self.week_number}_{timestamp}.json")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_score, f, ensure_ascii=False, indent=2)

        self.log(f"综合打分保存到: {output_file}", "SUCCESS")

        return comprehensive_score, output_file

    def generate_ui_data(self, table_scores, column_avg_scores):
        """生成UI热力图数据"""
        ui_data = []

        for table_score in table_scores:
            table_ui = {
                "table_name": table_score["table_name"],
                "table_url": table_score["table_url"],
                "row_data": []
            }

            # 为每列生成热力值
            for col_name in STANDARD_COLUMNS:
                if col_name in table_score["column_scores"]:
                    heat_value = table_score["column_scores"][col_name]["avg_score"]
                else:
                    heat_value = 0.0

                table_ui["row_data"].append({
                    "column": col_name,
                    "heat_value": heat_value,
                    "color": self.get_color_by_score(heat_value)
                })

            ui_data.append(table_ui)

        return ui_data

    def get_color_by_score(self, score):
        """根据分数获取颜色"""
        if score >= 0.8:
            return "#FF0000"  # 红色
        elif score >= 0.6:
            return "#FFA500"  # 橙色
        elif score >= 0.4:
            return "#FFFF00"  # 黄色
        elif score >= 0.1:
            return "#00FF00"  # 绿色
        else:
            return "#0000FF"  # 蓝色

    def run_complete_workflow(self):
        """运行完整工作流"""
        self.log("========== 开始完整链路处理 ==========", "PROCESS")

        # 获取文件路径
        baseline_files = [
            "/root/projects/tencent-doc-manager/csv_versions/2025_W38/baseline/tencent_出国销售计划表_20250915_0145_baseline_W38.csv",
            "/root/projects/tencent-doc-manager/csv_versions/2025_W38/baseline/tencent_小红书部门_20250915_0146_baseline_W38.csv"
        ]

        current_files = [
            "/root/projects/tencent-doc-manager/csv_versions/2025_W38/midweek/tencent_111测试版本-出国销售计划表-工作表1_20250915_0239_midweek_W38.csv",
            "/root/projects/tencent-doc-manager/csv_versions/2025_W38/midweek/tencent_111测试版本-小红书部门-工作表2_20250915_0240_midweek_W38.csv"
        ]

        table_urls = [
            "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN?tab=BB08J2",
            "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R?tab=000001"
        ]

        table_names = ["出国销售计划表", "小红书部门"]

        all_table_scores = []

        # 处理每个表格
        for i, (baseline_file, current_file) in enumerate(zip(baseline_files, current_files)):
            if not os.path.exists(baseline_file) or not os.path.exists(current_file):
                self.log(f"文件不存在，跳过: {table_names[i]}", "WARNING")
                continue

            self.log(f"\n处理表格 {i+1}/{len(baseline_files)}: {table_names[i]}", "PROCESS")

            # 阶段1: 加载和标准化
            baseline_data = self.load_csv_as_table(baseline_file)
            current_data = self.load_csv_as_table(current_file)

            baseline_data = self.standardize_columns(baseline_data)
            current_data = self.standardize_columns(current_data)

            # 阶段2: 对比分析
            differences = self.compare_tables(baseline_data, current_data)

            if not differences:
                self.log("没有发现差异，跳过", "WARNING")
                continue

            # 阶段3: 基础打分
            differences = self.apply_base_scoring(differences)

            # 阶段4: AI智能打分
            differences = self.apply_ai_scoring(differences)

            # 阶段5: 详细打分
            detailed_score = self.generate_detailed_scores(
                differences,
                table_names[i],
                table_urls[i] if i < len(table_urls) else ""
            )

            all_table_scores.append(detailed_score)

        # 阶段6-7: 综合打分
        if all_table_scores:
            comprehensive_score, output_file = self.generate_comprehensive_score(all_table_scores)

            self.log("\n========== 链路处理完成 ==========", "SUCCESS")
            self.log(f"✅ 处理了 {len(all_table_scores)} 个表格", "SUCCESS")
            self.log(f"✅ 发现 {comprehensive_score['total_modifications']} 处修改", "SUCCESS")
            self.log(f"✅ 综合打分文件: {output_file}", "SUCCESS")

            return comprehensive_score
        else:
            self.log("没有有效的表格数据", "ERROR")
            return None

if __name__ == "__main__":
    pipeline = CompletePipeline()
    result = pipeline.run_complete_workflow()

    if result:
        print(f"\n📊 综合打分摘要:")
        print(f"  - 处理表格数: {len(result['table_names'])}")
        print(f"  - 总修改数: {result['total_modifications']}")
        print(f"  - 高风险表格: {result['risk_summary']['high_risk_count']}")
        print(f"  - 中风险表格: {result['risk_summary']['medium_risk_count']}")
        print(f"  - 低风险表格: {result['risk_summary']['low_risk_count']}")