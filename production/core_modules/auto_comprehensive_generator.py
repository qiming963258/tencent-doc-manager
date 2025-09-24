#!/usr/bin/env python3
"""
自动生成综合打分文件
在8093工作流完成后调用，从详细打分和对比结果生成综合打分
"""

import json
import os
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class AutoComprehensiveGenerator:
    """自动综合打分生成器"""

    def __init__(self):
        self.scoring_dir = Path('/root/projects/tencent-doc-manager/scoring_results')
        self.comparison_dir = Path('/root/projects/tencent-doc-manager/comparison_results')
        self.detailed_dir = self.scoring_dir / 'detailed'
        self.comprehensive_dir = self.scoring_dir / 'comprehensive'

        # 标准19列
        self.STANDARD_COLUMNS = [
            "序号", "项目类型", "来源", "任务发起时间", "目标对齐",
            "关键KR对齐", "具体计划内容", "邓总指导登记", "负责人", "协助人",
            "监督人", "重要程度", "预计完成时间", "完成进度", "完成链接",
            "经理分析复盘", "最新复盘时间", "对上汇报", "应用情况"
        ]

        # L1/L2/L3列定义
        self.L1_COLUMNS = ["来源", "任务发起时间", "目标对齐", "关键KR对齐", "负责人", "重要程度", "预计完成时间"]
        self.L2_COLUMNS = ["项目类型", "具体计划内容", "邓总指导登记", "协助人", "监督人", "对上汇报"]
        self.L3_COLUMNS = ["序号", "完成进度", "完成链接", "经理分析复盘", "最新复盘时间", "应用情况"]

    def generate_from_latest_results(self, excel_url=None) -> str:
        """从最新的详细打分结果生成综合打分

        Args:
            excel_url: 上传后的腾讯文档URL
        """

        # 1. 查找最新的详细打分文件
        detailed_files = sorted(self.detailed_dir.glob('detailed_score_*.json'),
                              key=lambda x: x.stat().st_mtime, reverse=True)

        if not detailed_files:
            raise FileNotFoundError("没有找到详细打分文件")

        latest_detailed = detailed_files[0]
        logger.info(f"使用详细打分文件: {latest_detailed.name}")

        # 2. 加载详细打分数据
        with open(latest_detailed, 'r', encoding='utf-8') as f:
            detailed_data = json.load(f)

        # 3. 提取表格信息
        table_name = self._extract_table_name(detailed_data)

        # 4. 生成热力图矩阵和列修改数据
        heatmap_matrix, column_modifications = self._process_detailed_scores(detailed_data)

        # 5. 统计风险分布
        risk_stats = self._calculate_risk_stats(detailed_data)

        # 6. 生成综合打分数据结构
        comprehensive_data = self._build_comprehensive_structure(
            table_name, heatmap_matrix, column_modifications,
            detailed_data, risk_stats, excel_url
        )

        # 7. 保存文件
        output_file = self._save_comprehensive_file(comprehensive_data)

        logger.info(f"✅ 综合打分文件已生成: {output_file}")
        return str(output_file)

    def _extract_table_name(self, detailed_data):
        """提取表格名称"""
        # 从metadata或scores中提取
        table_name = detailed_data.get('metadata', {}).get('table_name', '')

        # 如果是临时文件名，使用默认名称
        if table_name.startswith('tmp'):
            table_name = "副本-测试版本-出国销售计划表"

        return table_name

    def _process_detailed_scores(self, detailed_data):
        """处理详细打分，生成热力图矩阵和列修改数据"""

        # 列名映射
        COLUMN_MAPPING = {
            "计划输出思路\n8/28": "序号",
            "项目类型": "项目类型",
            "来源": "来源",
            "任务发起时间": "任务发起时间",
            "目标对齐": "目标对齐",
            "关键KR对齐": "关键KR对齐",
            "具体计划内容": "具体计划内容",
            "邓总指导登记（日更新）": "邓总指导登记",
            "负责人": "负责人",
            "协助人": "协助人",
            "重要程度": "重要程度",
            "预计完成时间": "预计完成时间",
            "完成链接": "完成链接",
            "总完成进度": "完成进度",
            "经理分析复盘": "经理分析复盘",
        }

        # 收集每列的修改和风险等级
        column_data = {}

        for score in detailed_data.get('scores', []):
            original_col = score['column_name']
            standard_col = COLUMN_MAPPING.get(original_col, original_col)

            if standard_col in self.STANDARD_COLUMNS:
                if standard_col not in column_data:
                    column_data[standard_col] = {
                        'modifications': [],
                        'risk_level': score['column_level'],
                        'scores': []
                    }

                # 提取行号
                cell = score['cell']
                row_num = int(''.join(filter(str.isdigit, cell)))
                column_data[standard_col]['modifications'].append(row_num)
                column_data[standard_col]['scores'].append(
                    score.get('scoring_details', {}).get('final_score', 0)
                )

        # 生成热力图矩阵
        matrix_row = []
        column_modifications = {}

        for col in self.STANDARD_COLUMNS:
            if col in column_data:
                risk_level = column_data[col]['risk_level']
                has_modification = len(column_data[col]['modifications']) > 0

                # 根据风险等级设置颜色值
                if not has_modification:
                    heat_value = 0.05  # 无修改（蓝色）
                elif risk_level == 'L1':
                    heat_value = 0.90  # L1高风险（红色）
                elif risk_level == 'L2':
                    heat_value = 0.60  # L2中风险（橙色）
                else:  # L3
                    heat_value = 0.30  # L3低风险（绿色）

                # 构建列修改数据
                column_modifications[col] = {
                    'modified_rows': column_data[col]['modifications'],
                    'modification_count': len(column_data[col]['modifications']),
                    'risk_level': risk_level,
                    'average_score': round(sum(column_data[col]['scores']) / len(column_data[col]['scores']), 2) if column_data[col]['scores'] else 0
                }
            else:
                heat_value = 0.05  # 无修改

            matrix_row.append(heat_value)

        return [matrix_row], column_modifications

    def _calculate_risk_stats(self, detailed_data):
        """计算风险统计"""
        l1_count = 0
        l2_count = 0
        l3_count = 0

        for score in detailed_data.get('scores', []):
            level = score['column_level']
            if level == 'L1':
                l1_count += 1
            elif level == 'L2':
                l2_count += 1
            elif level == 'L3':
                l3_count += 1

        return {
            'l1_count': l1_count,
            'l2_count': l2_count,
            'l3_count': l3_count,
            'total': l1_count + l2_count + l3_count
        }

    def _build_comprehensive_structure(self, table_name, heatmap_matrix,
                                      column_modifications, detailed_data, risk_stats, excel_url=None):
        """构建综合打分数据结构

        Args:
            excel_url: 上传后的腾讯文档URL
        """

        total_mods = risk_stats['total']

        # 构建基础结构
        result = {
            "metadata": {
                "version": "2.0",
                "timestamp": datetime.now().isoformat(),
                "week": "W39",
                "generator": "auto_comprehensive_generator",
                "source_type": "detailed_scoring",
                "baseline_week": "W38",
                "comparison_week": "W39"
            },
            "summary": {
                "total_tables": 1,
                "total_columns": 19,
                "total_modifications": total_mods,
                "l1_modifications": risk_stats['l1_count'],
                "l2_modifications": risk_stats['l2_count'],
                "l3_modifications": risk_stats['l3_count'],
                "overall_risk_score": self._calculate_overall_risk(risk_stats),
                "processing_status": "complete",
                "data_source": "auto_generated"
            },
            "table_names": [table_name],
            "column_names": self.STANDARD_COLUMNS,
            "heatmap_data": {
                "matrix": heatmap_matrix,
                "rows": len(heatmap_matrix),
                "cols": 19,
                "generation_method": "risk_based_auto",
                "color_distribution": {
                    "red_0.9": heatmap_matrix[0].count(0.90),
                    "orange_0.6": heatmap_matrix[0].count(0.60),
                    "green_0.3": heatmap_matrix[0].count(0.30),
                    "blue_0.05": heatmap_matrix[0].count(0.05)
                }
            },
            "table_details": {
                table_name: {
                    "total_rows": 270,
                    "modified_rows": total_mods,
                    "added_rows": 0,
                    "deleted_rows": 0
                }
            },
            "statistics": {
                "total_cells": 5130,
                "modified_cells": total_mods,
                "modification_rate": round(total_mods / 5130, 4) if total_mods > 0 else 0,
                "risk_distribution": detailed_data.get('summary', {}).get('risk_distribution', {})
            },
            "column_modifications_by_table": {
                table_name: {
                    "column_modifications": column_modifications,
                    "total_rows": 270
                }
            }
        }

        # 添加excel_urls字段（如果有URL）
        if excel_url:
            result["excel_urls"] = {
                table_name: excel_url
            }
            # 同时在table_details中添加
            result["table_details"][table_name]["excel_url"] = excel_url
            logger.info(f"✅ 已添加Excel URL到综合打分: {excel_url}")

        return result

    def _calculate_overall_risk(self, risk_stats):
        """计算整体风险分数"""
        total = risk_stats['total']
        if total == 0:
            return 0

        weighted_score = (
            risk_stats['l1_count'] * 0.9 +
            risk_stats['l2_count'] * 0.6 +
            risk_stats['l3_count'] * 0.3
        ) / total

        return round(weighted_score, 2)

    def _save_comprehensive_file(self, data):
        """保存综合打分文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"comprehensive_score_W39_AUTO_{timestamp}.json"
        output_path = self.comprehensive_dir / filename

        # 确保目录存在
        self.comprehensive_dir.mkdir(parents=True, exist_ok=True)

        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 同时保存为latest文件
        latest_path = self.comprehensive_dir / "comprehensive_score_W39_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return output_path


if __name__ == "__main__":
    generator = AutoComprehensiveGenerator()
    output = generator.generate_from_latest_results()
    print(f"✅ 综合打分已生成: {output}")