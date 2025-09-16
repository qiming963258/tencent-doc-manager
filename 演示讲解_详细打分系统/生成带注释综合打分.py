#!/usr/bin/env python3
"""
生成带详细注释的综合打分示例文件
用于演示和讲解UI与综合打分的适配规范
"""

import json
from datetime import datetime

def generate_annotated_comprehensive_score():
    """生成带注释的综合打分数据"""

    # 创建完整的综合打分数据结构
    comprehensive_data = {
        "_文档说明": "这是综合打分系统的核心数据文件，UI只能从此文件获取数据（强制原则）",
        "_规范版本": "基于0000-颜色和级别打分标准 v1.0",
        "_生成时间说明": "ISO 8601格式时间戳，记录数据生成时刻",

        "generation_time": datetime.now().isoformat(),
        "scoring_version": "3.0",
        "scoring_standard": "0000-颜色和级别打分标准",

        # ===== 关键内容1：所有表名列表 =====
        "_关键内容1": "【所有表名列表】UI热力图左侧Y轴显示的表格名称",
        "table_names": [
            "小红书内容审核记录表",
            "企业风险评估矩阵表",
            "财务月度报表汇总表"
        ],

        # ===== 关键内容2：每标准列平均加权修改打分 =====
        "_关键内容2": "【列平均打分】UI热力图顶部X轴显示的列平均风险值",
        "column_avg_scores": {
            "序号": 0.85,      # L1级别列，最低分0.8
            "项目类型": 0.92,   # L1级别列，核心关键数据
            "来源": 0.25,      # L3级别列，最低分0.1
            "任务发起时间": 0.28, # L3级别列
            "目标对齐": 0.88,   # L1级别列，战略关键
            "关键KR对齐": 0.91, # L1级别列，OKR核心
            "具体计划内容": 0.22, # L3级别列
            "邓总指导登记": 0.27, # L3级别列
            "负责人": 0.55,     # L2级别列，最低分0.4，需AI评估
            "协助人": 0.58,     # L2级别列
            "监督人": 0.59,     # L2级别列
            "重要程度": 0.56,   # L2级别列
            "预计完成时间": 0.54, # L2级别列
            "完成进度": 0.53,   # L2级别列
            "形成计划清单": 0.28, # L3级别列
            "复盘时间": 0.24,   # L3级别列
            "对上汇报": 0.25,   # L3级别列
            "应用情况": 0.22,   # L3级别列
            "进度分析总结": 0.23  # L3级别列
        },

        # ===== 关键内容3&4：表格详细数据 =====
        "_关键内容3_4": "【表格详细数据】包含修改行数、打分和URL",
        "table_scores": [
            {
                "_说明": "第一个表格的完整数据",
                "table_id": 0,
                "table_name": "小红书内容审核记录表",

                # 关键内容4：表格URL
                "_关键内容4": "【表格URL】点击表格名称跳转的腾讯文档地址",
                "table_url": "https://docs.qq.com/sheet/DWEFNU25TemFnZXJN",

                "total_rows": 92,
                "total_modifications": 15,
                "overall_risk_score": 0.65,

                # 关键内容3：每列具体修改行数和打分
                "_关键内容3": "【列修改详情】UI热力图单元格颜色和悬停信息的数据源",
                "column_scores": {
                    "项目类型": {
                        "_说明": "L1列示例，最高风险",
                        "column_level": "L1",
                        "avg_score": 0.98,  # 决定热力图颜色（红色）
                        "modified_rows": [5, 12, 28],  # 修改的行号
                        "row_scores": [0.95, 0.99, 1.0],  # 对应行的打分
                        "modifications": 3
                    },
                    "负责人": {
                        "_说明": "L2列示例，需要AI评估",
                        "column_level": "L2",
                        "avg_score": 0.55,  # 决定热力图颜色（黄色）
                        "modified_rows": [8, 15, 22, 35, 67],
                        "row_scores": [0.45, 0.52, 0.58, 0.61, 0.59],
                        "modifications": 5,
                        "ai_decisions": ["APPROVE", "APPROVE", "REVIEW", "REVIEW", "REVIEW"],
                        "ai_confidence": [0.85, 0.82, 0.75, 0.73, 0.76]
                    },
                    "来源": {
                        "_说明": "L3列示例，低风险",
                        "column_level": "L3",
                        "avg_score": 0.21,  # 决定热力图颜色（绿色）
                        "modified_rows": [2, 45],
                        "row_scores": [0.18, 0.24],
                        "modifications": 2
                    }
                }
            },
            {
                "_说明": "第二个表格的数据",
                "table_id": 1,
                "table_name": "企业风险评估矩阵表",
                "table_url": "https://docs.qq.com/sheet/DWGZDZkxpaGVQaURr",
                "total_rows": 75,
                "total_modifications": 8,
                "overall_risk_score": 0.48,
                "column_scores": {
                    "目标对齐": {
                        "column_level": "L1",
                        "avg_score": 0.88,
                        "modified_rows": [10, 25],
                        "row_scores": [0.85, 0.91],
                        "modifications": 2
                    },
                    "预计完成时间": {
                        "column_level": "L2",
                        "avg_score": 0.54,
                        "modified_rows": [30, 42, 58],
                        "row_scores": [0.52, 0.55, 0.55],
                        "modifications": 3
                    },
                    "进度分析总结": {
                        "column_level": "L3",
                        "avg_score": 0.23,
                        "modified_rows": [5, 18, 66],
                        "row_scores": [0.22, 0.24, 0.23],
                        "modifications": 3
                    }
                }
            },
            {
                "_说明": "第三个表格的数据",
                "table_id": 2,
                "table_name": "财务月度报表汇总表",
                "table_url": "https://docs.qq.com/sheet/DWFJzdWNwd0RGbU5R",
                "total_rows": 120,
                "total_modifications": 12,
                "overall_risk_score": 0.72,
                "column_scores": {
                    "关键KR对齐": {
                        "column_level": "L1",
                        "avg_score": 0.91,
                        "modified_rows": [3, 15, 45, 78],
                        "row_scores": [0.89, 0.92, 0.91, 0.92],
                        "modifications": 4
                    },
                    "监督人": {
                        "column_level": "L2",
                        "avg_score": 0.59,
                        "modified_rows": [20, 35, 50, 65, 80, 95],
                        "row_scores": [0.58, 0.60, 0.59, 0.61, 0.57, 0.59],
                        "modifications": 6
                    },
                    "复盘时间": {
                        "column_level": "L3",
                        "avg_score": 0.24,
                        "modified_rows": [12, 88],
                        "row_scores": [0.23, 0.25],
                        "modifications": 2
                    }
                }
            }
        ],

        # ===== 关键内容5：全部修改数 =====
        "_关键内容5": "【全部修改数】UI右上角显示的总修改统计",
        "total_modifications": 35,

        # ===== 风险统计汇总 =====
        "_风险统计": "【风险分布】UI风险分布统计图表的数据源",
        "risk_summary": {
            "high_risk_count": 12,   # 打分≥0.6的修改总数
            "medium_risk_count": 15,  # 0.4≤打分<0.6的修改总数
            "low_risk_count": 8       # 打分<0.4的修改总数
        }
    }

    # 添加UI映射指南
    ui_mapping = {
        "_UI适配说明": "以下是UI组件如何使用这些数据",
        "热力图矩阵": {
            "Y轴（行）": "table_names数组",
            "X轴（列）": "19个标准列名",
            "单元格颜色": "table_scores[i].column_scores[列名].avg_score",
            "颜色规则": {
                "红色": "score >= 0.8",
                "橙色": "0.6 <= score < 0.8",
                "黄色": "0.4 <= score < 0.6",
                "绿色": "0.1 <= score < 0.4",
                "蓝色": "score < 0.1"
            }
        },
        "右侧列分布图": {
            "数据源": "鼠标悬停时获取对应列的column_scores",
            "显示内容": "modified_rows数组长度和风险等级",
            "横条宽度": "基于avg_score计算"
        },
        "悬停详情弹窗": {
            "表格名": "table_name",
            "修改行数": "modified_rows数组",
            "行打分": "row_scores数组",
            "列级别": "column_level",
            "AI建议": "ai_decisions（仅L2列）"
        },
        "表格链接": {
            "点击跳转": "table_url",
            "新标签页打开": "腾讯文档链接"
        }
    }

    # 添加验证规则
    validation_rules = {
        "_数据验证规则": "服务器启动时的完整性检查",
        "必需字段检查": [
            "table_names必须是数组",
            "column_avg_scores必须包含19个标准列",
            "table_scores数组长度必须与table_names一致",
            "每个table_score必须包含table_url",
            "total_modifications必须是数字"
        ],
        "打分规则验证": [
            "L1列打分不能低于0.8",
            "L2列打分不能低于0.4",
            "L3列打分必须大于0.1",
            "所有打分必须在0-1范围内"
        ],
        "数据一致性": [
            "modified_rows和row_scores长度必须相同",
            "modifications应等于modified_rows长度",
            "total_modifications应等于所有表格修改数之和"
        ]
    }

    return comprehensive_data, ui_mapping, validation_rules

def save_with_comments():
    """保存带注释版本的JSON文件"""
    comprehensive_data, ui_mapping, validation_rules = generate_annotated_comprehensive_score()

    # 保存主数据文件
    output_file = "/root/projects/tencent-doc-manager/演示讲解_详细打分系统/综合打分结果_带注释版_W36.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 已生成带注释的综合打分文件: {output_file}")

    # 保存UI映射指南
    ui_mapping_file = "/root/projects/tencent-doc-manager/演示讲解_详细打分系统/UI映射指南.json"
    with open(ui_mapping_file, 'w', encoding='utf-8') as f:
        json.dump(ui_mapping, f, ensure_ascii=False, indent=2)

    print(f"✅ 已生成UI映射指南: {ui_mapping_file}")

    # 保存验证规则
    validation_file = "/root/projects/tencent-doc-manager/演示讲解_详细打分系统/数据验证规则.json"
    with open(validation_file, 'w', encoding='utf-8') as f:
        json.dump(validation_rules, f, ensure_ascii=False, indent=2)

    print(f"✅ 已生成数据验证规则: {validation_file}")

    # 生成简洁版（去除注释）
    clean_data = remove_comments(comprehensive_data)
    clean_file = "/root/projects/tencent-doc-manager/演示讲解_详细打分系统/综合打分结果_生产版_W36.json"
    with open(clean_file, 'w', encoding='utf-8') as f:
        json.dump(clean_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 已生成生产版本（无注释）: {clean_file}")

def remove_comments(data):
    """移除所有以_开头的注释字段"""
    if isinstance(data, dict):
        return {k: remove_comments(v) for k, v in data.items() if not k.startswith('_')}
    elif isinstance(data, list):
        return [remove_comments(item) for item in data]
    else:
        return data

if __name__ == "__main__":
    save_with_comments()

    print("\n📊 文件生成完成！包含：")
    print("1. 综合打分结果_带注释版_W36.json - 详细注释版本")
    print("2. 综合打分结果_生产版_W36.json - 生产环境版本")
    print("3. UI映射指南.json - UI组件使用说明")
    print("4. 数据验证规则.json - 数据完整性验证规则")