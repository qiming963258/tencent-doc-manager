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

        # 获取当前周数
        self.current_week = self._get_current_week()
        # 创建对应周的目录
        self.week_dir = self.scoring_dir / f'2025_W{self.current_week}'
        self.week_dir.mkdir(parents=True, exist_ok=True)

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

    def _get_current_week(self) -> str:
        """获取当前周数"""
        return str(datetime.now().isocalendar()[1]).zfill(2)

    def _get_baseline_week(self) -> str:
        """获取基线周数（通常是上一周）"""
        now = datetime.now()
        weekday = now.weekday()  # 0=周一
        hour = now.hour
        current_week = now.isocalendar()[1]

        # 根据技术规范v1.6的逻辑
        if weekday < 1 or (weekday == 1 and hour < 12):
            # 周一全天 OR 周二12点前 → 使用上周基线
            target_week = current_week - 1
        else:
            # 周二12点后 OR 周三到周日 → 使用本周基线
            target_week = current_week

        return str(target_week).zfill(2)

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

        # 如果是临时文件名，尝试从工作流历史记录中查找真实文档名
        if table_name.startswith('tmp'):
            # 查找对应的工作流文件来获取真实文档名
            import glob
            import json
            from pathlib import Path

            # 先尝试从workflow历史中查找
            workflow_dir = Path('/root/projects/tencent-doc-manager/workflow_history')

            # 查找包含这个临时ID的workflow文件
            for workflow_file in workflow_dir.glob('workflow_*.json'):
                try:
                    with open(workflow_file, 'r', encoding='utf-8') as f:
                        workflow_data = json.load(f)

                    # 检查score_file是否包含当前的临时ID
                    score_file = workflow_data.get('results', {}).get('score_file', '')
                    if table_name in score_file:
                        # 从target_file中提取文档名
                        target_file = workflow_data.get('results', {}).get('target_file', '')
                        if target_file:
                            import re
                            # 匹配格式：tencent_{文档名}_{时间戳}_{版本}_W{周}.csv
                            match = re.search(r'tencent_(.+?)_\d{8}_\d{4}_(baseline|midweek)_W\d+\.csv$', target_file)
                            if match:
                                extracted_name = match.group(1)
                                logger.info(f"从workflow历史提取表名: {table_name} -> {extracted_name}")
                                return extracted_name
                except Exception as e:
                    logger.debug(f"读取workflow文件失败: {e}")
                    continue

            # 如果workflow中找不到，尝试从对应时间的CSV文件查找（备用方案）
            # 但不使用最新文件，而是尝试匹配时间戳
            if '_' in table_name:
                # 提取详细文件的时间戳（例如：tmpi6tacfy8_20250925_183507）
                parts = table_name.split('_')
                if len(parts) >= 3:
                    date_str = parts[-2]  # 20250925
                    time_str = parts[-1]  # 183507

                    # 动态获取当前周的midweek目录
                    current_year = datetime.now().year
                    current_week = datetime.now().isocalendar()[1]
                    csv_dir = Path(f'/root/projects/tencent-doc-manager/csv_versions/{current_year}_W{current_week:02d}/midweek')
                    # 查找同一时间段的CSV文件（允许5分钟误差）
                    for csv_file in csv_dir.glob(f'*_{date_str}_*.csv'):
                        csv_time = csv_file.stem.split('_')[-3]  # 获取时间部分
                        # 简单时间比较（允许相近时间）
                        if abs(int(time_str[:4]) - int(csv_time)) <= 5:  # 5分钟内
                            import re
                            match = re.search(r'^tencent_(.+?)_\d{8}_\d{4}_(baseline|midweek)_W\d+$', csv_file.stem)
                            if match:
                                extracted_name = match.group(1)
                                logger.info(f"从时间匹配的CSV文件提取表名: {table_name} -> {extracted_name}")
                                return extracted_name

            # 如果还是找不到，返回临时ID本身（保持可追溯性）
            logger.warning(f"无法为临时ID {table_name} 找到对应的文档名")
            return f"文档_{table_name}"

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
                "week": f"W{self.current_week}",
                "generator": "auto_comprehensive_generator",
                "source_type": "detailed_scoring",
                "baseline_week": f"W{self._get_baseline_week()}",
                "comparison_week": f"W{self.current_week}"
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
        filename = f"comprehensive_score_W{self.current_week}_AUTO_{timestamp}.json"

        # 保存到对应周的目录
        output_path = self.week_dir / filename

        # 确保目录存在
        self.week_dir.mkdir(parents=True, exist_ok=True)

        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 同时保存到comprehensive目录作为latest文件（保持兼容）
        self.comprehensive_dir.mkdir(parents=True, exist_ok=True)
        latest_path = self.comprehensive_dir / f"comprehensive_score_W{self.current_week}_latest.json"
        with open(latest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 同时保存到周目录作为latest
        week_latest_path = self.week_dir / f"comprehensive_score_W{self.current_week}_latest.json"
        with open(week_latest_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return output_path

    def generate_from_all_detailed_results(self, excel_urls=None) -> str:
        """
        批量处理：从所有详细打分结果生成综合打分
        支持多文档聚合，生成N×19矩阵热力图

        Args:
            excel_urls: 字典，格式 {表格名: URL}
        """
        import re
        from datetime import datetime

        # 1. 查找当前时间段内的所有详细打分文件
        detailed_files = sorted(self.detailed_dir.glob('detailed_score_*.json'),
                              key=lambda x: x.stat().st_mtime, reverse=True)

        if not detailed_files:
            raise FileNotFoundError("没有找到详细打分文件")

        # 2. 过滤出最近1小时内的文件（属于同一批次）
        current_time = datetime.now()
        batch_files = []
        for file in detailed_files:
            file_time = datetime.fromtimestamp(file.stat().st_mtime)
            time_diff = (current_time - file_time).total_seconds()
            if time_diff <= 3600:  # 1小时内的文件
                batch_files.append(file)

        if not batch_files:
            # 如果没有1小时内的文件，使用最新的3个文件
            batch_files = detailed_files[:3]

        logger.info(f"批量处理 {len(batch_files)} 个详细打分文件")

        # 3. 处理每个文件，收集数据
        all_table_data = []
        all_heatmap_rows = []
        total_l1 = 0
        total_l2 = 0
        total_l3 = 0
        total_mods = 0

        for detailed_file in batch_files:
            logger.info(f"处理文件: {detailed_file.name}")

            with open(detailed_file, 'r', encoding='utf-8') as f:
                detailed_data = json.load(f)

            # 提取表格信息
            table_name = self._extract_table_name(detailed_data)

            # 生成热力图矩阵和列修改数据
            heatmap_matrix, column_modifications = self._process_detailed_scores(detailed_data)

            # 累加热力图行（每个文档一行）
            if heatmap_matrix and len(heatmap_matrix) > 0:
                all_heatmap_rows.append(heatmap_matrix[0])  # 取第一行（单文档只有一行）

            # 统计风险分布
            risk_stats = self._calculate_risk_stats(detailed_data)
            total_l1 += risk_stats['l1_count']
            total_l2 += risk_stats['l2_count']
            total_l3 += risk_stats['l3_count']
            total_mods += risk_stats['total']

            # 收集表格数据
            table_info = {
                'table_name': table_name,
                'modified_rows': risk_stats['total'],
                'column_modifications': column_modifications,
                'excel_url': excel_urls.get(table_name) if excel_urls else None
            }
            all_table_data.append(table_info)

        # 4. 构建综合打分数据结构（多文档版本）
        comprehensive_data = {
            "metadata": {
                "version": "2.0",
                "timestamp": datetime.now().isoformat(),
                "week": f"W{self.current_week}",
                "generator": "auto_comprehensive_generator_batch",
                "source_type": "multi_document_scoring",
                "baseline_week": f"W{self._get_baseline_week()}",
                "comparison_week": f"W{self.current_week}"
            },
            "summary": {
                "total_tables": len(all_table_data),  # 动态计算表格数量
                "total_columns": 19,
                "total_modifications": total_mods,
                "l1_modifications": total_l1,
                "l2_modifications": total_l2,
                "l3_modifications": total_l3,
                "overall_risk_score": self._calculate_overall_risk({
                    'l1_count': total_l1,
                    'l2_count': total_l2,
                    'l3_count': total_l3,
                    'total': total_mods
                }),
                "processing_status": "complete",
                "data_source": "batch_auto_generated"
            },
            "table_names": [item['table_name'] for item in all_table_data],
            "column_names": self.STANDARD_COLUMNS,
            "heatmap_data": {
                "matrix": all_heatmap_rows,  # N×19矩阵
                "rows": len(all_heatmap_rows),  # 动态行数
                "cols": 19,
                "generation_method": "batch_risk_based_auto",
                "color_distribution": self._calculate_color_distribution(all_heatmap_rows)
            },
            "table_details": {}
        }

        # 5. 添加每个表格的详细信息
        for table_info in all_table_data:
            table_name = table_info['table_name']
            comprehensive_data["table_details"][table_name] = {
                "total_rows": 270,  # 可以从详细文件中获取
                "modified_rows": table_info['modified_rows'],
                "added_rows": 0,
                "deleted_rows": 0
            }
            if table_info['excel_url']:
                comprehensive_data["table_details"][table_name]["excel_url"] = table_info['excel_url']

        # 6. 如果提供了excel_urls，添加到数据中
        if excel_urls:
            comprehensive_data["excel_urls"] = excel_urls

        # 7. 保存文件
        output_path = self._save_comprehensive_file(comprehensive_data)

        logger.info(f"✅ 批量综合打分已生成: {output_path}")
        logger.info(f"   包含 {len(all_table_data)} 个表格，热力图矩阵: {len(all_heatmap_rows)}×19")

        return str(output_path)

    def _calculate_color_distribution(self, matrix):
        """计算颜色分布统计"""
        distribution = {
            "red_0.9": 0,
            "orange_0.6": 0,
            "green_0.3": 0,
            "blue_0.05": 0
        }

        for row in matrix:
            distribution["red_0.9"] += row.count(0.90)
            distribution["orange_0.6"] += row.count(0.60)
            distribution["green_0.3"] += row.count(0.30)
            distribution["blue_0.05"] += row.count(0.05)

        return distribution


if __name__ == "__main__":
    generator = AutoComprehensiveGenerator()
    output = generator.generate_from_latest_results()
    print(f"✅ 综合打分已生成: {output}")